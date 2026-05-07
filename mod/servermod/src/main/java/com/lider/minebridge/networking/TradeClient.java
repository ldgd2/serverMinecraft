package com.lider.minebridge.networking;

import com.google.gson.Gson;
import com.google.gson.JsonArray;
import com.google.gson.JsonObject;
import com.lider.minebridge.config.ModConfig;
import com.lider.minebridge.MineBridge;
import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.util.concurrent.CompletableFuture;

/**
 * Cliente para gestionar trades con el backend.
 * Utiliza NetworkManager para asegurar que el I/O y el procesamiento JSON no bloqueen el servidor.
 */
public class TradeClient {
    private static final HttpClient httpClient = NetworkManager.getHttpClient();
    private static final Gson gson = new Gson();

    public static CompletableFuture<JsonArray> getOpenTrades() {
        return CompletableFuture.supplyAsync(() -> {
            try {
                String baseUrl = ModConfig.getBackendUrl();
                String url = baseUrl + (baseUrl.endsWith("/") ? "" : "/") + "api/v1/trades/open";
                HttpRequest request = HttpRequest.newBuilder()
                        .uri(URI.create(url))
                        .GET()
                        .timeout(java.time.Duration.ofSeconds(5))
                        .build();

                return httpClient.send(request, HttpResponse.BodyHandlers.ofString());
            } catch (Exception e) {
                throw new RuntimeException(e);
            }
        }, NetworkManager.getExecutor()).thenApply(res -> {
            if (res.statusCode() == 200) {
                JsonObject json = gson.fromJson(res.body(), JsonObject.class);
                return json.getAsJsonArray("data");
            }
            return new JsonArray();
        }).exceptionally(t -> {
            MineBridge.LOGGER.error("Failed to fetch trades: " + t.getMessage());
            return new JsonArray();
        });
    }

    public static CompletableFuture<Boolean> publishTrade(String sellerUuid, String sellerName, String title, JsonObject selling, com.google.gson.JsonElement asking) {
        return CompletableFuture.supplyAsync(() -> {
            try {
                String baseUrl = ModConfig.getBackendUrl();
                String url = baseUrl + (baseUrl.endsWith("/") ? "" : "/") + "api/v1/trades/publish";
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
                        .header("X-API-Key", ModConfig.getApiKey())
                        .timeout(java.time.Duration.ofSeconds(5))
                        .build();

                return httpClient.send(request, HttpResponse.BodyHandlers.ofString());
            } catch (Exception e) {
                throw new RuntimeException(e);
            }
        }, NetworkManager.getExecutor()).thenApply(res -> res.statusCode() == 200)
          .exceptionally(t -> {
              MineBridge.LOGGER.error("Failed to publish trade: " + t.getMessage());
              return false;
          });
    }

    public static CompletableFuture<Boolean> completeTrade(int tradeId, String buyerUuid, String buyerName) {
        return completeTradeSecurely(tradeId, buyerUuid, buyerName);
    }

    public static CompletableFuture<Boolean> completeTradeSecurely(int tradeId, String buyerUuid, String buyerName) {
        return CompletableFuture.supplyAsync(() -> {
            try {
                String baseUrl = ModConfig.getBackendUrl();
                String url = baseUrl + (baseUrl.endsWith("/") ? "" : "/") + "api/v1/trades/" + tradeId + "/complete?secure=true";
                JsonObject data = new JsonObject();
                data.addProperty("buyer_uuid", buyerUuid);
                data.addProperty("buyer_name", buyerName);

                HttpRequest request = HttpRequest.newBuilder()
                        .uri(URI.create(url))
                        .POST(HttpRequest.BodyPublishers.ofString(data.toString()))
                        .header("Content-Type", "application/json")
                        .header("X-API-Key", ModConfig.getApiKey())
                        .timeout(java.time.Duration.ofSeconds(5))
                        .build();

                return httpClient.send(request, HttpResponse.BodyHandlers.ofString());
            } catch (Exception e) {
                throw new RuntimeException(e);
            }
        }, NetworkManager.getExecutor()).thenApply(res -> res.statusCode() == 200)
          .exceptionally(t -> {
              MineBridge.LOGGER.error("Failed to complete trade: " + t.getMessage());
              return false;
          });
    }

    public static CompletableFuture<Boolean> cancelTrade(int tradeId) {
        return CompletableFuture.supplyAsync(() -> {
            try {
                String baseUrl = ModConfig.getBackendUrl();
                String url = baseUrl + (baseUrl.endsWith("/") ? "" : "/") + "api/v1/trades/" + tradeId + "/cancel";
                HttpRequest request = HttpRequest.newBuilder()
                        .uri(URI.create(url))
                        .POST(HttpRequest.BodyPublishers.noBody())
                        .header("X-API-Key", ModConfig.getApiKey())
                        .timeout(java.time.Duration.ofSeconds(5))
                        .build();

                return httpClient.send(request, HttpResponse.BodyHandlers.ofString());
            } catch (Exception e) {
                throw new RuntimeException(e);
            }
        }, NetworkManager.getExecutor()).thenApply(res -> res.statusCode() == 200)
          .exceptionally(t -> {
              MineBridge.LOGGER.error("Failed to cancel trade: " + t.getMessage());
              return false;
          });
    }
}
