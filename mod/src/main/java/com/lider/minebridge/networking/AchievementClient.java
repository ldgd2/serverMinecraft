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

    private static String getApiUrl() {
        return ModConfig.getBackendUrl() + "/api/minecraft/event";
    }

    /**
     * Envía un mensaje de chat o evento de sistema al backend.
     */
    public static void sendChatMessage(String playerUuid, String playerName, String message, String type) {
        CompletableFuture.runAsync(() -> {
            try {
                JsonObject json = new JsonObject();
                json.addProperty("player_uuid", playerUuid);
                json.addProperty("player_name", playerName);
                json.addProperty("message", message);
                json.addProperty("type", type); // 'chat', 'join', 'leave', 'achievement'

                HttpRequest request = HttpRequest.newBuilder()
                        .uri(URI.create(ModConfig.getBackendUrl() + "/api/minecraft/chat"))
                        .header("Content-Type", "application/json")
                        .POST(HttpRequest.BodyPublishers.ofString(json.toString()))
                        .build();

                client.sendAsync(request, HttpResponse.BodyHandlers.ofString());
            } catch (Exception e) {
                System.err.println("[MineBridge] Error enviando chat: " + e.getMessage());
            }
        });
    }

    public static void sendEvent(String playerUuid, String eventKey, int increment) {
        CompletableFuture.runAsync(() -> {
            try {
                JsonObject json = new JsonObject();
                json.addProperty("player_uuid", playerUuid);
                json.addProperty("event_key", eventKey);
                json.addProperty("increment", increment);

                HttpRequest request = HttpRequest.newBuilder()
                        .uri(URI.create(getApiUrl()))
                        .header("Content-Type", "application/json")
                        .POST(HttpRequest.BodyPublishers.ofString(json.toString()))
                        .build();

                client.sendAsync(request, HttpResponse.BodyHandlers.ofString())
                      .thenAccept(response -> {
                          if (response.statusCode() != 200) {
                              System.err.println("[MineBridge] Error enviando evento: " + response.body());
                          }
                      });
            } catch (Exception e) {
                System.err.println("[MineBridge] Error critico de red: " + e.getMessage());
            }
        });
    }
}
