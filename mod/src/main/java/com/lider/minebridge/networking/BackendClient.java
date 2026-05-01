package com.lider.minebridge.networking;

import com.google.gson.Gson;
import com.google.gson.JsonObject;
import com.lider.minebridge.MineBridge;
import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.net.http.WebSocket;
import java.util.concurrent.CompletableFuture;
import java.util.concurrent.CompletionStage;

public class BackendClient {
    private String baseUrl;
    private String apiKey;
    private final HttpClient httpClient;
    private final Gson gson;
    private WebSocket webSocket;

    public BackendClient(String baseUrl, String apiKey) {
        this.baseUrl = (baseUrl == null || baseUrl.isEmpty() || baseUrl.equals("PENDING")) ? null : (baseUrl.endsWith("/") ? baseUrl : baseUrl + "/");
        this.apiKey = (apiKey == null || apiKey.isEmpty() || apiKey.equals("PENDING")) ? null : apiKey;
        this.httpClient = HttpClient.newBuilder().build();
        this.gson = new Gson();
        
        if (this.baseUrl != null && this.apiKey != null) {
            connectWebSocket();
        } else {
            MineBridge.LOGGER.warn("Backend configuration is PENDING. Use /minebridge set-url and set-key to initialize.");
        }
    }

    private void connectWebSocket() {
        if (baseUrl == null || apiKey == null) return;
        String wsUrl = baseUrl.replace("http", "ws") + "api/v1/ws/bridge";
        httpClient.newWebSocketBuilder()
            .header("X-API-Key", apiKey)
            .buildAsync(URI.create(wsUrl), new WebSocketListener())
            .thenAccept(ws -> {
                this.webSocket = ws;
                MineBridge.LOGGER.info("Connected to Backend WebSocket Bridge");
            })
            .exceptionally(t -> {
                MineBridge.LOGGER.error("Failed to connect to WebSocket: " + t.getMessage());
                return null;
            });
    }

    public void sendChatMessage(String player, String message) {
        JsonObject json = new JsonObject();
        json.addProperty("player", player);
        json.addProperty("message", message);
        json.addProperty("type", "chat");
        
        postAsync("api/v1/bridge/chat", json);
    }

    public void notifyPlayerJoin(String player, String uuid) {
        JsonObject json = new JsonObject();
        json.addProperty("player", player);
        json.addProperty("uuid", uuid);
        json.addProperty("type", "join");
        
        postAsync("api/v1/bridge/events", json);
    }

    public void notifyPlayerLeave(String player) {
        JsonObject json = new JsonObject();
        json.addProperty("player", player);
        json.addProperty("type", "leave");
        
        postAsync("api/v1/bridge/events", json);
    }

    public void notifyStatUpdate(String player, String stat, String value) {
        notifyStatUpdate(player, stat, value, 1);
    }

    public void notifyStatUpdate(String player, String stat, String value, int amount) {
        JsonObject json = new JsonObject();
        json.addProperty("player", player);
        json.addProperty("stat", stat);
        json.addProperty("value", value);
        json.addProperty("amount", amount);
        json.addProperty("type", "stat_update");
        
        postAsync("api/v1/bridge/stats", json);
    }

    public void notifyPlayerDeath(String player, String cause, String killer) {
        JsonObject json = new JsonObject();
        json.addProperty("player", player);
        json.addProperty("cause", cause);
        json.addProperty("killer", killer);
        json.addProperty("type", "death");
        
        postAsync("api/v1/bridge/events", json);
    }

    public void notifyPlayerState(String player, float health, int food, double x, double y, double z, String world) {
        JsonObject json = new JsonObject();
        json.addProperty("player", player);
        json.addProperty("health", health);
        json.addProperty("food", food);
        json.addProperty("pos_x", x);
        json.addProperty("pos_y", y);
        json.addProperty("pos_z", z);
        json.addProperty("world", world);
        json.addProperty("type", "player_state");
        
        postAsync("api/v1/bridge/status/player", json);
    }

    public void notifyServerState(String state) {
        JsonObject json = new JsonObject();
        json.addProperty("state", state);
        
        postAsync("api/v1/bridge/status", json);
    }

    public CompletableFuture<String> testConnection() {
        if (baseUrl.contains("PENDING") || apiKey.equals("PENDING")) {
            return CompletableFuture.completedFuture("CONFIG_ERROR");
        }

        HttpRequest request = HttpRequest.newBuilder()
            .uri(URI.create(baseUrl + "api/v1/bridge/test"))
            .header("X-API-Key", apiKey)
            .GET()
            .build();

        return httpClient.sendAsync(request, HttpResponse.BodyHandlers.ofString())
            .thenApply(res -> {
                if (res.statusCode() == 200) return "SUCCESS";
                if (res.statusCode() == 401) return "UNAUTHORIZED";
                return "ERROR: " + res.statusCode();
            })
            .exceptionally(t -> "FAILED: " + t.getMessage());
    }

    private void postAsync(String endpoint, JsonObject data) {
        if (baseUrl == null || apiKey == null) return;
        
        try {
            HttpRequest request = HttpRequest.newBuilder()
                .uri(URI.create(baseUrl + endpoint))
                .header("Content-Type", "application/json")
                .header("X-API-Key", apiKey)
                .POST(HttpRequest.BodyPublishers.ofString(gson.toJson(data)))
                .build();

            httpClient.sendAsync(request, HttpResponse.BodyHandlers.ofString())
                .thenAccept(res -> {
                    if (res.statusCode() >= 400) {
                        MineBridge.LOGGER.warn("Backend error (" + res.statusCode() + "): " + res.body());
                    }
                });
        } catch (Exception e) {
            MineBridge.LOGGER.error("Failed to send async request: " + e.getMessage());
        }
    }

    public void updateBaseUrl(String newUrl) {
        this.baseUrl = newUrl.endsWith("/") ? newUrl : newUrl + "/";
        // Reconnect websocket with new URL
        if (webSocket != null) {
            webSocket.sendClose(WebSocket.NORMAL_CLOSURE, "URL updated");
        }
        connectWebSocket();
    }

    public void updateApiKey(String newKey) {
        this.apiKey = newKey;
        // Reconnect websocket with new key
        if (webSocket != null) {
            webSocket.sendClose(WebSocket.NORMAL_CLOSURE, "API Key updated");
        }
        connectWebSocket();
    }

    public void close() {
        if (webSocket != null) {
            webSocket.sendClose(WebSocket.NORMAL_CLOSURE, "Server stopping");
        }
    }

    private class WebSocketListener implements WebSocket.Listener {
        @Override
        public void onOpen(WebSocket webSocket) {
            webSocket.request(1);
        }

        @Override
        public CompletionStage<?> onText(WebSocket webSocket, CharSequence data, boolean last) {
            try {
                JsonObject json = gson.fromJson(data.toString(), JsonObject.class);
                String action = json.get("action").getAsString();
                
                if ("command".equals(action)) {
                    String cmd = json.get("command").getAsString();
                    executeCommand(cmd);
                } else if ("kick".equals(action)) {
                    String target = json.get("player").getAsString();
                    String reason = json.has("reason") ? json.get("reason").getAsString() : "Kicked by admin";
                    executeCommand("kick " + target + " " + reason);
                } else if ("ban".equals(action)) {
                    String target = json.get("player").getAsString();
                    String reason = json.has("reason") ? json.get("reason").getAsString() : "Banned by admin";
                    executeCommand("ban " + target + " " + reason);
                }
            } catch (Exception e) {
                MineBridge.LOGGER.error("Error processing WebSocket message: " + e.getMessage());
            }
            webSocket.request(1);
            return null;
        }

        private void executeCommand(String cmd) {
            MineBridge.getServer().execute(() -> {
                MineBridge.getServer().getCommandManager().executeWithPrefix(
                    MineBridge.getServer().getCommandSource(), cmd
                );
            });
        }
    }
}
