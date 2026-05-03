package com.lider.minebridge.networking;

import com.google.gson.JsonObject;
import com.lider.minebridge.config.ModConfig;
import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.util.concurrent.CompletableFuture;

/**
 * Cliente centralizado para enviar eventos al backend de Python.
 */
public class AchievementClient {
    private static final HttpClient client = HttpClient.newHttpClient();
    private static final java.util.concurrent.CopyOnWriteArrayList<JsonObject> batchEvents = new java.util.concurrent.CopyOnWriteArrayList<>();
    private static final java.util.concurrent.CopyOnWriteArrayList<JsonObject> batchChats = new java.util.concurrent.CopyOnWriteArrayList<>();
    private static java.util.concurrent.ScheduledExecutorService scheduler;

    static {
        scheduler = java.util.concurrent.Executors.newSingleThreadScheduledExecutor();
        // Reducido a 10 segundos para mejor respuesta sin sobrecargar
        scheduler.scheduleAtFixedRate(AchievementClient::flushBatch, 5, 10, java.util.concurrent.TimeUnit.SECONDS);
    }

    private static String getBaseUrl() {
        String url = ModConfig.getBackendUrl();
        if (url == null || url.isEmpty() || url.equals("PENDING")) return null;
        return url.endsWith("/") ? url : url + "/";
    }

    /**
     * Envía un mensaje de chat o evento de sistema al backend.
     */
    public static void sendChatMessage(String playerUuid, String playerName, String message, String type) {
        JsonObject json = new JsonObject();
        json.addProperty("uuid", playerUuid);
        json.addProperty("player", playerName); // Backend expects 'player'
        json.addProperty("message", message);
        json.addProperty("type", type); // 'chat', 'join', 'leave', 'achievement'
        json.addProperty("server_name", ModConfig.getServerName());
        
        batchChats.add(json);
    }

    /**
     * Reporta que un jugador se ha unido, incluyendo su IP para el dashboard.
     */
    public static void sendJoinEvent(String playerUuid, String playerName, String ip) {
        JsonObject json = new JsonObject();
        json.addProperty("uuid", playerUuid);
        json.addProperty("player", playerName);
        json.addProperty("ip", ip);
        json.addProperty("type", "join");
        json.addProperty("server_name", ModConfig.getServerName());
        
        batchEvents.add(json);
    }

    /**
     * Reporta que se ha cumplido una condición de logro o una estadística.
     */
    public static void sendEvent(String playerUuid, String eventKey, int increment) {
        // Log en consola para depuración
        com.lider.minebridge.MineBridge.LOGGER.info("[MineBridge] Evento registrado: " + eventKey + " para " + playerUuid);

        JsonObject json = new JsonObject();
        json.addProperty("uuid", playerUuid);
        json.addProperty("player", "Server"); // The backend will resolve by UUID if possible
        json.addProperty("achievement_id", eventKey); // Explicit field for achievements
        json.addProperty("message", eventKey);        // Fallback for generic handlers
        json.addProperty("increment", increment);      // Essential for counters
        json.addProperty("type", "achievement");
        json.addProperty("server_name", ModConfig.getServerName());
        
        // Add to events batch, NOT chats
        batchEvents.add(json);
    }

    /**
     * Envía el resumen acumulado de la sesión al desconectarse.
     */
    public static void sendSessionSummary(String playerUuid, java.util.Map<String, Integer> stats) {
        String base = getBaseUrl();
        if (base == null || stats.isEmpty()) return;

        JsonObject payload = new JsonObject();
        payload.addProperty("player_uuid", playerUuid);
        
        JsonObject statsJson = new JsonObject();
        stats.forEach(statsJson::addProperty);
        payload.add("stats", statsJson);

        CompletableFuture.runAsync(() -> {
            try {
                HttpRequest request = HttpRequest.newBuilder()
                        .uri(URI.create(base + "api/minecraft/stats/session"))
                        .version(HttpClient.Version.HTTP_1_1)
                        .header("Content-Type", "application/json")
                        .header("X-API-Key", ModConfig.getApiKey())
                        .POST(HttpRequest.BodyPublishers.ofString(payload.toString()))
                        .build();

                client.sendAsync(request, HttpResponse.BodyHandlers.ofString());
            } catch (Exception e) {
                System.err.println("[MineBridge] Error enviando session summary: " + e.getMessage());
            }
        });
    }

    /**
     * Pide al backend las estadísticas actuales del jugador para sincronizar contadores.
     */
    public static void fetchPlayerStats(String playerUuid) {
        String base = getBaseUrl();
        if (base == null) return;

        CompletableFuture.runAsync(() -> {
            try {
                HttpRequest request = HttpRequest.newBuilder()
                        .uri(URI.create(base + "api/minecraft/stats/" + playerUuid))
                        .version(HttpClient.Version.HTTP_1_1)
                        .header("X-API-Key", ModConfig.getApiKey())
                        .GET()
                        .build();

                client.sendAsync(request, HttpResponse.BodyHandlers.ofString())
                      .thenAccept(response -> {
                          if (response.statusCode() == 200) {
                              try {
                                  JsonObject stats = new com.google.gson.JsonParser().parse(response.body()).getAsJsonObject();
                                  
                                  // Sync counters in logic modules
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
            } catch (Exception e) {
                System.err.println("[MineBridge] Error recuperando estadísticas: " + e.getMessage());
            }
        });
    }

    private static void flushBatch() {
        String base = getBaseUrl();
        if (base == null) return;
        if (batchEvents.isEmpty() && batchChats.isEmpty()) return;

        JsonObject batch = new JsonObject();
        batch.addProperty("server_name", ModConfig.getServerName());
        
        com.google.gson.JsonArray eventsArray = new com.google.gson.JsonArray();
        while (!batchEvents.isEmpty()) { eventsArray.add(batchEvents.remove(0)); }
        if (eventsArray.size() > 0) batch.add("events", eventsArray);

        com.google.gson.JsonArray chatsArray = new com.google.gson.JsonArray();
        while (!batchChats.isEmpty()) { chatsArray.add(batchChats.remove(0)); }
        if (chatsArray.size() > 0) batch.add("chats", chatsArray);

        CompletableFuture.runAsync(() -> {
            try {
                HttpRequest request = HttpRequest.newBuilder()
                        .uri(URI.create(base + "api/bridge/batch")) // Correct path
                        .version(HttpClient.Version.HTTP_1_1)
                        .header("Content-Type", "application/json")
                        .header("X-API-Key", ModConfig.getApiKey())
                        .POST(HttpRequest.BodyPublishers.ofString(batch.toString()))
                        .build();

                client.sendAsync(request, HttpResponse.BodyHandlers.ofString())
                      .thenAccept(response -> {
                          if (response.statusCode() >= 400) {
                              System.err.println("[MineBridge] Error enviando batch: " + response.body());
                          }
                      });
            } catch (Exception e) {
                System.err.println("[MineBridge] Error critico de red en batch: " + e.getMessage());
            }
        });
    }
}
