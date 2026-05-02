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
        scheduler.scheduleAtFixedRate(AchievementClient::flushBatch, 5, 5, java.util.concurrent.TimeUnit.SECONDS);
    }

    private static String getBaseUrl() {
        String url = ModConfig.getBackendUrl();
        if (url == null || url.isEmpty() || url.equals("PENDING")) return null;
        return url.endsWith("/") ? url : url + "/";
    }

    private static String getApiUrl() {
        String base = getBaseUrl();
        if (base == null) return null;
        return base + "api/minecraft/event";
    }

    /**
     * Envía un mensaje de chat o evento de sistema al backend.
     */
    public static void sendChatMessage(String playerUuid, String playerName, String message, String type) {
        JsonObject json = new JsonObject();
        json.addProperty("player_uuid", playerUuid);
        json.addProperty("player_name", playerName);
        json.addProperty("message", message);
        json.addProperty("type", type); // 'chat', 'join', 'leave', 'achievement'
        json.addProperty("server_name", ModConfig.getServerName());
        
        batchChats.add(json);
    }

    public static void sendEvent(String playerUuid, String eventKey, int increment) {
        JsonObject json = new JsonObject();
        json.addProperty("player_uuid", playerUuid);
        json.addProperty("event_key", eventKey);
        json.addProperty("increment", increment);
        json.addProperty("server_name", ModConfig.getServerName());
        
        batchEvents.add(json);
    }

    private static void flushBatch() {
        String base = getBaseUrl();
        if (base == null) return;
        if (batchEvents.isEmpty() && batchChats.isEmpty()) return;

        JsonObject batch = new JsonObject();
        
        com.google.gson.JsonArray eventsArray = new com.google.gson.JsonArray();
        while (!batchEvents.isEmpty()) { eventsArray.add(batchEvents.remove(0)); }
        if (eventsArray.size() > 0) batch.add("events", eventsArray);

        com.google.gson.JsonArray chatsArray = new com.google.gson.JsonArray();
        while (!batchChats.isEmpty()) { chatsArray.add(batchChats.remove(0)); }
        if (chatsArray.size() > 0) batch.add("chats", chatsArray);

        CompletableFuture.runAsync(() -> {
            try {
                HttpRequest request = HttpRequest.newBuilder()
                        .uri(URI.create(base + "api/minecraft/batch"))
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
