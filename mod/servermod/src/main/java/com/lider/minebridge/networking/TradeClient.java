package com.lider.minebridge.networking;

import com.google.gson.Gson;
import com.google.gson.JsonArray;
import com.google.gson.JsonObject;
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
                .GET()
                .timeout(java.time.Duration.ofSeconds(5))
                .build();

        return httpClient.sendAsync(request, HttpResponse.BodyHandlers.ofString())
                .thenApply(res -> {
                    if (res.statusCode() == 200) {
                        JsonObject json = gson.fromJson(res.body(), JsonObject.class);
                        return json.getAsJsonArray("data");
                    }
                    return new JsonArray();
                }).exceptionally(t -> new JsonArray());
    }

    public static CompletableFuture<Boolean> publishTrade(String sellerUuid, String sellerName, String title, JsonObject selling, com.google.gson.JsonElement asking) {
        String url = ModConfig.getBackendUrl() + "api/v1/trades/publish";
        JsonObject data = new JsonObject();
        data.addProperty("seller_uuid", sellerUuid);
        data.addProperty("seller_name", sellerName);
        data.addProperty("title", title);
        data.add("selling", selling);
        data.add("asking", asking);

        HttpRequest request = HttpRequest.newBuilder()
                .uri(URI.create(url))
                .POST(HttpRequest.BodyPublishers.ofString(data.toString()))
                .header("Content-Type", "application/json")
                .build();

        return httpClient.sendAsync(request, HttpResponse.BodyHandlers.ofString())
                .thenApply(res -> res.statusCode() == 200);
    }

    public static CompletableFuture<Boolean> completeTrade(int tradeId, String buyerUuid, String buyerName) {
        return completeTradeSecurely(tradeId, buyerUuid, buyerName);
    }

    public static CompletableFuture<Boolean> completeTradeSecurely(int tradeId, String buyerUuid, String buyerName) {
        String url = ModConfig.getBackendUrl() + "api/v1/trades/" + tradeId + "/complete?secure=true";
        JsonObject data = new JsonObject();
        data.addProperty("buyer_uuid", buyerUuid);
        data.addProperty("buyer_name", buyerName);

        HttpRequest request = HttpRequest.newBuilder()
                .uri(URI.create(url))
                .POST(HttpRequest.BodyPublishers.ofString(data.toString()))
                .header("Content-Type", "application/json")
                .build();

        return httpClient.sendAsync(request, HttpResponse.BodyHandlers.ofString())
                .thenApply(res -> res.statusCode() == 200);
    }

    public static CompletableFuture<Boolean> cancelTrade(int tradeId) {
        String url = ModConfig.getBackendUrl() + "api/v1/trades/" + tradeId + "/cancel";
        HttpRequest request = HttpRequest.newBuilder()
                .uri(URI.create(url))
                .POST(HttpRequest.BodyPublishers.noBody())
                .build();

        return httpClient.sendAsync(request, HttpResponse.BodyHandlers.ofString())
                .thenApply(res -> res.statusCode() == 200);
    }
}
