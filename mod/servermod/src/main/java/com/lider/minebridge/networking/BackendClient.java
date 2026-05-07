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
    private String localUrl;
    private String activeUrl;
    private String apiKey;
    private final HttpClient httpClient;
    private final Gson gson;
    private WebSocket webSocket;
    private final java.util.concurrent.CopyOnWriteArrayList<JsonObject> batchEvents = new java.util.concurrent.CopyOnWriteArrayList<>();
    private final java.util.concurrent.CopyOnWriteArrayList<JsonObject> batchStats = new java.util.concurrent.CopyOnWriteArrayList<>();
    private final java.util.concurrent.CopyOnWriteArrayList<JsonObject> batchChats = new java.util.concurrent.CopyOnWriteArrayList<>();
    private java.util.concurrent.ScheduledExecutorService scheduler;

    public BackendClient(String baseUrl, String localUrl, String apiKey) {
        this.baseUrl = (baseUrl == null || baseUrl.isEmpty() || baseUrl.equals("PENDING")) ? null : (baseUrl.endsWith("/") ? baseUrl : baseUrl + "/");
        this.localUrl = (localUrl == null || localUrl.isEmpty() || localUrl.equals("PENDING")) ? null : (localUrl.endsWith("/") ? localUrl : localUrl + "/");
        this.apiKey = (apiKey == null || apiKey.isEmpty() || apiKey.equals("PENDING")) ? null : apiKey;
        this.activeUrl = this.localUrl != null ? this.localUrl : this.baseUrl;

        // Force HTTP/1.1 to avoid "Unsupported upgrade request" issues with some proxies/backends
        this.httpClient = HttpClient.newBuilder()
            .version(HttpClient.Version.HTTP_1_1)
            .build();
            
        this.gson = new Gson();
        
        if (this.activeUrl != null && this.apiKey != null) {
            detectBestUrlAndConnect();
        } else {
            MineBridge.LOGGER.warn("Backend configuration is PENDING. Use /minebridge set-url and set-key to initialize.");
        }
        
        scheduler = java.util.concurrent.Executors.newSingleThreadScheduledExecutor();
        // Telemetría cada 30 segundos para no saturar el servidor
        scheduler.scheduleAtFixedRate(this::flushBatch, 10, 30, java.util.concurrent.TimeUnit.SECONDS);
    }

    private void detectBestUrlAndConnect() {
        if (localUrl == null) {
            this.activeUrl = baseUrl;
            connectWebSocket();
            return;
        }

        // Probar si localhost responde
        HttpRequest request = HttpRequest.newBuilder()
            .uri(URI.create(localUrl + "api/v1/bridge/test"))
            .header("X-API-Key", apiKey)
            .GET()
            .timeout(java.time.Duration.ofSeconds(2))
            .build();

        httpClient.sendAsync(request, HttpResponse.BodyHandlers.ofString())
            .thenAccept(res -> {
                if (res.statusCode() == 200) {
                    this.activeUrl = localUrl;
                    MineBridge.LOGGER.info("Local backend detected. Using: " + activeUrl);
                } else {
                    this.activeUrl = baseUrl;
                    MineBridge.LOGGER.info("Local backend failed (HTTP " + res.statusCode() + "). Falling back to: " + activeUrl);
                }
                connectWebSocket();
            })
            .exceptionally(t -> {
                this.activeUrl = baseUrl;
                MineBridge.LOGGER.info("Local backend unreachable. Falling back to: " + activeUrl);
                connectWebSocket();
                return null;
            });
    }

    private void connectWebSocket() {
        if (activeUrl == null || apiKey == null) return;
        String wsUrl = activeUrl.replace("http", "ws") + "api/v1/ws/bridge";
        httpClient.newWebSocketBuilder()
            .header("X-API-Key", apiKey)
            .buildAsync(URI.create(wsUrl), new WebSocketListener())
            .thenAccept(ws -> {
                this.webSocket = ws;
                MineBridge.LOGGER.info("Connected to Backend WebSocket Bridge: " + activeUrl);
                // Notificar éxito al servidor (si ya existe)
                if (MineBridge.getServer() != null) {
                    MineBridge.getServer().execute(() -> {
                        MineBridge.LOGGER.info("§a[MineBridge] Conexión WebSocket establecida con éxito.");
                    });
                }
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
        
        batchChats.add(json);
    }

    public void notifyPlayerJoin(String player, String uuid) {
        JsonObject json = new JsonObject();
        json.addProperty("player", player);
        json.addProperty("uuid", uuid);
        json.addProperty("type", "join");
        
        // JOIN es urgente: enviar inmediatamente para actualizar la caché de jugadores
        batchEvents.add(json);
        flushUrgent();
    }

    public void notifyPlayerLeave(String player) {
        JsonObject json = new JsonObject();
        json.addProperty("player", player);
        json.addProperty("type", "leave");
        
        // LEAVE es urgente: enviar inmediatamente para actualizar la caché de jugadores
        batchEvents.add(json);
        flushUrgent();
    }

    public void notifyStatUpdate(String player, String stat, String value) {
        notifyStatUpdate(player, stat, value, 1);
    }

    public static void notifyStatUpdate(String player, String stat, String value, int amount) {
        // [DESACTIVADO] El servidor ya no lleva la cuenta de estadísticas individuales.
    }

    public void notifyPlayerDeath(String player, String cause, String killer) {
        // [DESACTIVADO] El servidor ya no procesa eventos de muerte.
    }

    public void notifyServerState(String state) {
        // [DESACTIVADO]
    }

    public CompletableFuture<String> testConnection() {
        if (baseUrl.contains("PENDING") || apiKey.equals("PENDING")) {
            return CompletableFuture.completedFuture("CONFIG_ERROR");
        }

        HttpRequest request = HttpRequest.newBuilder()
            .uri(URI.create(activeUrl + "api/v1/bridge/test"))
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

    private static final java.util.concurrent.ExecutorService networkExecutor = java.util.concurrent.Executors.newFixedThreadPool(2);

    private void postAsync(String endpoint, JsonObject data) {
        if (activeUrl == null || apiKey == null) return;
        
        networkExecutor.submit(() -> {
            try {
                String jsonBody = data.toString();
                HttpRequest request = HttpRequest.newBuilder()
                    .uri(URI.create(activeUrl + endpoint))
                    .version(HttpClient.Version.HTTP_1_1)
                    .header("Content-Type", "application/json")
                    .header("X-API-Key", apiKey)
                    .POST(HttpRequest.BodyPublishers.ofString(jsonBody))
                    .timeout(java.time.Duration.ofSeconds(5))
                    .build();

                httpClient.sendAsync(request, HttpResponse.BodyHandlers.ofString())
                    .thenAccept(res -> {
                        if (res.statusCode() >= 400) {
                            // MineBridge.LOGGER.warn("Backend error (" + res.statusCode() + ") on " + endpoint);
                        }
                    }).exceptionally(t -> null);
            } catch (Exception e) {
                // Silently fail to avoid console spam during lag
            }
        });
    }

    private void flushBatch() {
        if (baseUrl == null || apiKey == null) return;
        if (batchEvents.isEmpty() && batchStats.isEmpty() && batchChats.isEmpty()) return;

        JsonObject batch = new JsonObject();

        com.google.gson.JsonArray eventsArray = new com.google.gson.JsonArray();
        while (!batchEvents.isEmpty()) { eventsArray.add(batchEvents.remove(0)); }
        if (eventsArray.size() > 0) batch.add("events", eventsArray);

        com.google.gson.JsonArray statsArray = new com.google.gson.JsonArray();
        while (!batchStats.isEmpty()) { statsArray.add(batchStats.remove(0)); }
        if (statsArray.size() > 0) batch.add("stats", statsArray);

        com.google.gson.JsonArray chatsArray = new com.google.gson.JsonArray();
        while (!batchChats.isEmpty()) { chatsArray.add(batchChats.remove(0)); }
        if (chatsArray.size() > 0) batch.add("chats", chatsArray);

        postAsync("api/v1/bridge/batch", batch);
    }

    /** Flush inmediato para eventos críticos (join, leave, death) sin esperar el timer. */
    private void flushUrgent() {
        if (baseUrl == null || apiKey == null) return;
        if (batchEvents.isEmpty() && batchChats.isEmpty()) return;

        JsonObject batch = new JsonObject();

        com.google.gson.JsonArray eventsArray = new com.google.gson.JsonArray();
        while (!batchEvents.isEmpty()) { eventsArray.add(batchEvents.remove(0)); }
        if (eventsArray.size() > 0) batch.add("events", eventsArray);

        com.google.gson.JsonArray chatsArray = new com.google.gson.JsonArray();
        while (!batchChats.isEmpty()) { chatsArray.add(batchChats.remove(0)); }
        if (chatsArray.size() > 0) batch.add("chats", chatsArray);

        if (batch.size() > 0) {
            postAsync("api/v1/bridge/batch", batch);
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
        if (scheduler != null) {
            scheduler.shutdown();
        }
        flushBatch(); // flush remaining before stopping
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
                    MineBridge.LOGGER.info("§b[MineBridge] Ejecutando comando remoto: §f" + cmd);
                    executeCommand(cmd);
                } else if ("achievement".equals(action)) {
                    String target = json.get("player").getAsString();
                    String title = json.get("title").getAsString();
                    String desc = json.get("desc").getAsString();
                    
                    // Comandos para hacer que el logro "salte" visual y sonoramente
                    executeCommand("title " + target + " title {\"text\":\"\\u2605 Logro Desbloqueado \\u2605\",\"color\":\"gold\",\"bold\":true}");
                    executeCommand("title " + target + " subtitle {\"text\":\"" + title + "\",\"color\":\"yellow\"}");
                    executeCommand("execute as " + target + " at @s run playsound ui.toast.challenge_complete master @s ~ ~ ~ 1.0 1.0");
                    executeCommand("tellraw @a [\"\", {\"text\":\"\\uD83C\\uDFC6 \",\"color\":\"gold\"}, {\"text\":\"" + target + "\",\"color\":\"white\"}, {\"text\":\" ha conseguido el logro \",\"color\":\"gray\"}, {\"text\":\"[" + title + "]\",\"color\":\"yellow\",\"hoverEvent\":{\"action\":\"show_text\",\"contents\":\"" + desc + "\"}}]");
                } else if ("kick".equals(action)) {
                    String target = json.get("player").getAsString();
                    String reason = json.has("reason") ? json.get("reason").getAsString() : "Kicked by admin";
                    executeCommand("kick " + target + " " + reason);
                } else if ("ban".equals(action)) {
                    String target = json.get("player").getAsString();
                    String reason = json.has("reason") ? json.get("reason").getAsString() : "Banned by admin";
                    executeCommand("ban " + target + " " + reason);
                } else if ("sync-skin".equals(action)) {
                    String target = json.get("player").getAsString();
                    MineBridge.getServer().execute(() -> {
                        net.minecraft.server.network.ServerPlayerEntity p = MineBridge.getServer().getPlayerManager().getPlayer(target);
                        if (p != null) {
                            com.lider.minebridge.networking.SkinClient.syncSkin(p);
                        }
                    });
                } else if ("unban".equals(action)) {
                    String target = json.get("player").getAsString();
                    executeCommand("pardon " + target);
                } else if ("unban-ip".equals(action)) {
                    String target = json.get("ip").getAsString();
                    executeCommand("pardon-ip " + target);
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
