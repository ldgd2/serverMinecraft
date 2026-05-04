package com.lider.minebridge.networking;

import com.google.gson.JsonObject;
import com.lider.minebridge.config.ModConfig;
import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.util.concurrent.CompletableFuture;

/**
 * Cliente para enviar eventos al backend de forma individual e inmediata.
 */
public class AchievementClient {
    private static final HttpClient client = HttpClient.newBuilder()
            .version(HttpClient.Version.HTTP_1_1)
            .build();

    private static String getBaseUrl() {
        String url = ModConfig.getBackendUrl();
        if (url == null || url.isEmpty() || url.equals("PENDING")) return null;
        return url.endsWith("/") ? url : url + "/";
    }

    private static void sendRequest(String endpoint, JsonObject payload) {
        String base = getBaseUrl();
        if (base == null) return;

        CompletableFuture.runAsync(() -> {
            try {
                HttpRequest request = HttpRequest.newBuilder()
                        .uri(URI.create(base + endpoint))
                        .header("Content-Type", "application/json")
                        .header("X-API-Key", ModConfig.getApiKey())
                        .POST(HttpRequest.BodyPublishers.ofString(payload.toString()))
                        .build();

                client.sendAsync(request, HttpResponse.BodyHandlers.ofString())
                      .thenAccept(response -> {
                          if (response.statusCode() >= 400) {
                              System.err.println("[MineBridge] Error en " + endpoint + ": " + response.statusCode() + " " + response.body());
                          }
                      });
            } catch (Exception e) {
                System.err.println("[MineBridge] Error de red: " + e.getMessage());
            }
        });
    }

    public static void sendChatMessage(String playerUuid, String playerName, String message, String type) {
        JsonObject json = new JsonObject();
        json.addProperty("uuid", playerUuid);
        json.addProperty("player", playerName);
        json.addProperty("message", message);
        json.addProperty("type", type);
        json.addProperty("server_name", ModConfig.getServerName());
        
        sendRequest("api/v1/bridge/chat", json);
    }

    public static void sendJoinEvent(String playerUuid, String playerName, String ip) {
        JsonObject json = new JsonObject();
        json.addProperty("uuid", playerUuid);
        json.addProperty("player", playerName);
        json.addProperty("ip", ip);
        json.addProperty("type", "join");
        json.addProperty("server_name", ModConfig.getServerName());
        
        sendRequest("api/v1/bridge/events", json);
    }

    public static void sendEvent(String playerUuid, String eventKey, int increment) {
        // Silenciado para ahorrar recursos - Solo errores se reportan

        JsonObject json = new JsonObject();
        json.addProperty("uuid", playerUuid);
        json.addProperty("player", "Server");
        json.addProperty("achievement_id", eventKey);
        json.addProperty("message", eventKey);
        json.addProperty("increment", increment);
        json.addProperty("type", "achievement");
        json.addProperty("server_name", ModConfig.getServerName());
        
        sendRequest("api/v1/bridge/events", json);
    }

    public static void sendSessionSummary(String playerUuid, java.util.Map<String, Integer> stats) {
        String base = getBaseUrl();
        if (base == null || stats.isEmpty()) return;

        JsonObject payload = new JsonObject();
        payload.addProperty("player_uuid", playerUuid);
        
        JsonObject statsJson = new JsonObject();
        stats.forEach(statsJson::addProperty);
        payload.add("stats", statsJson);

        sendRequest("api/v1/minecraft/stats/session", payload);
    }

    public static void fetchPlayerStats(String playerUuid) {
        String base = getBaseUrl();
        if (base == null) return;

        CompletableFuture.runAsync(() -> {
            try {
                HttpRequest request = HttpRequest.newBuilder()
                        .uri(URI.create(base + "api/v1/minecraft/stats/" + playerUuid))
                        .header("X-API-Key", ModConfig.getApiKey())
                        .GET()
                        .build();

                client.sendAsync(request, HttpResponse.BodyHandlers.ofString())
                      .thenAccept(response -> {
                          if (response.statusCode() == 200) {
                              try {
                                  JsonObject stats = new com.google.gson.JsonParser().parse(response.body()).getAsJsonObject();
                                  if (stats.has("block_broken")) {
                                      com.lider.minebridge.events.blocks.BlockLogic.setInitialStats(playerUuid, stats.get("block_broken").getAsInt());
                                  }
                                  if (stats.has("total_kills")) {
                                      com.lider.minebridge.events.combat.CombatLogic.setInitialStats(playerUuid, stats.get("total_kills").getAsInt());
                                  }
                                  if (stats.has("item_enchanted")) {
                                      com.lider.minebridge.events.items.ItemLogic.setInitialStats(playerUuid, stats.get("item_enchanted").getAsInt());
                                  }
                              } catch (Exception ex) {}
                          }
                      });
            } catch (Exception e) {}
        });
    }
}
