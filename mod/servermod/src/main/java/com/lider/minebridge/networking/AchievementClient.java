package com.lider.minebridge.networking;

import com.google.gson.JsonObject;
import com.lider.minebridge.config.ModConfig;
import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;

/**
 * Cliente para enviar eventos al backend de forma individual e inmediata.
 * Versión optimizada para reenvío de eventos del cliente y chat.
 */
public class AchievementClient {
    private static final HttpClient client = HttpClient.newBuilder()
            .version(HttpClient.Version.HTTP_1_1)
            .build();

    // Cache para suprimir eventos repetidos en la misma sesión y ahorrar recursos
    private static final java.util.Set<String> sentEventsSession = java.util.concurrent.ConcurrentHashMap.newKeySet();

    private static String getBaseUrl() {
        String url = ModConfig.getBackendUrl();
        if (url == null || url.isEmpty() || url.equals("PENDING")) return null;
        return url.endsWith("/") ? url : url + "/";
    }

    private static final java.util.concurrent.ExecutorService networkExecutor = java.util.concurrent.Executors.newSingleThreadExecutor(r -> {
        Thread t = new Thread(r, "MineBridge-Network-Worker");
        t.setPriority(Thread.MIN_PRIORITY);
        return t;
    });

    private static void sendRequest(String endpoint, JsonObject payload) {
        String base = getBaseUrl();
        if (base == null) return;

        networkExecutor.submit(() -> {
            try {
                HttpRequest request = HttpRequest.newBuilder()
                        .uri(URI.create(base + endpoint))
                        .header("Content-Type", "application/json")
                        .header("X-API-Key", ModConfig.getApiKey())
                        .timeout(java.time.Duration.ofSeconds(2))
                        .POST(HttpRequest.BodyPublishers.ofString(payload.toString()))
                        .build();

                client.sendAsync(request, HttpResponse.BodyHandlers.ofString());
            } catch (Exception e) {
                // Silencio total en errores de red
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
        // Suprimir si ya se envió en esta sesión
        String cacheKey = playerUuid + ":" + eventKey;
        if (!sentEventsSession.add(cacheKey)) return;

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

    public static void clearSessionCache(String playerUuid) {
        sentEventsSession.removeIf(key -> key.startsWith(playerUuid + ":"));
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
}
