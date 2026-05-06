package com.lider.minebridge.networking;

import com.google.gson.Gson;
import com.google.gson.JsonArray;
import com.google.gson.JsonObject;
import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.util.concurrent.CompletableFuture;

import com.lider.minebridge.config.ClientConfig;

public class TradeClient {
    private static final HttpClient httpClient = HttpClient.newBuilder()
            .version(HttpClient.Version.HTTP_1_1)
            .build();
    private static final Gson gson = new Gson();

    public static CompletableFuture<JsonArray> getOpenTrades() {
        String url = ClientConfig.getApiUrl() + "api/v1/trades/open";
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

    public static CompletableFuture<Boolean> publishTrade(String sellerUuid, String sellerName, String title, JsonObject selling, JsonObject asking) {
        String url = ClientConfig.getApiUrl() + "api/v1/trades/publish";
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

    public static CompletableFuture<Boolean> sendCounterOffer(int tradeId, String buyerUuid, String buyerName, JsonArray offeredItems) {
        String url = ClientConfig.getApiUrl() + "api/v1/trades/" + tradeId + "/counter-offer";
        JsonObject data = new JsonObject();
        data.addProperty("buyer_uuid", buyerUuid);
        data.addProperty("buyer_name", buyerName);
        data.add("offered_items", offeredItems);

        HttpRequest request = HttpRequest.newBuilder()
                .uri(URI.create(url))
                .POST(HttpRequest.BodyPublishers.ofString(data.toString()))
                .header("Content-Type", "application/json")
                .build();

        return httpClient.sendAsync(request, HttpResponse.BodyHandlers.ofString())
                .thenApply(res -> res.statusCode() == 200);
    }

    public static CompletableFuture<Boolean> resolveOffer(int offerId, String action, String reason) {
        String url = ClientConfig.getApiUrl() + "api/v1/trades/resolve-offer/" + offerId + "?action=" + action + (reason != null ? "&reason=" + reason : "");
        HttpRequest request = HttpRequest.newBuilder()
                .uri(URI.create(url))
                .POST(HttpRequest.BodyPublishers.noBody())
                .build();

        return httpClient.sendAsync(request, HttpResponse.BodyHandlers.ofString())
                .thenApply(res -> res.statusCode() == 200);
    }

    public static CompletableFuture<Boolean> completeTrade(int tradeId, String buyerUuid, String buyerName) {
        String url = ClientConfig.getApiUrl() + "api/v1/trades/" + tradeId + "/complete";
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
}
