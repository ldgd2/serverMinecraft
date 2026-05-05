package com.lider.minebridge.networking;

import com.google.gson.Gson;
import com.google.gson.JsonArray;
import com.google.gson.JsonObject;
import com.lider.minebridge.MineBridge;
import com.lider.minebridge.config.ModConfig;
import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.util.concurrent.CompletableFuture;

public class TradeClient {
    private static final HttpClient httpClient = HttpClient.newBuilder()
            .version(HttpClient.Version.HTTP_1_1)
            .build();
    private static final Gson gson = new Gson();

    public static CompletableFuture<JsonArray> getOpenTrades() {
        String url = ModConfig.getBackendUrl() + "api/v1/trades/open";
        HttpRequest request = HttpRequest.newBuilder()
                .uri(URI.create(url))
                .header("X-API-Key", ModConfig.getApiKey())
                .GET()
                .build();

        return httpClient.sendAsync(request, HttpResponse.BodyHandlers.ofString())
                .thenApply(res -> {
                    if (res.statusCode() == 200) {
                        JsonObject json = gson.fromJson(res.body(), JsonObject.class);
                        return json.getAsJsonArray("data");
                    }
                    return new JsonArray();
                });
    }

    public static void publishTrade(String seller, JsonObject selling, JsonObject asking) {
        JsonObject data = new JsonObject();
        data.addProperty("seller", seller);
        data.add("selling", selling);
        data.add("asking", asking);

        String url = ModConfig.getBackendUrl() + "api/v1/trades/publish";
        HttpRequest request = HttpRequest.newBuilder()
                .uri(URI.create(url))
                .header("Content-Type", "application/json")
                .header("X-API-Key", ModConfig.getApiKey())
                .POST(HttpRequest.BodyPublishers.ofString(data.toString()))
                .build();

        httpClient.sendAsync(request, HttpResponse.BodyHandlers.ofString());
    }

    public static void resolveTrade(int tradeId, String action) {
        String url = ModConfig.getBackendUrl() + "api/v1/trades/" + tradeId + "/resolve?action=" + action;
        HttpRequest request = HttpRequest.newBuilder()
                .uri(URI.create(url))
                .header("X-API-Key", ModConfig.getApiKey())
                .POST(HttpRequest.BodyPublishers.noBody())
                .build();

        httpClient.sendAsync(request, HttpResponse.BodyHandlers.ofString());
    }
}
