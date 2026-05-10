package com.lider.minebridge.marketplace.networking;

import com.google.gson.JsonArray;
import com.google.gson.JsonObject;
import java.util.concurrent.CompletableFuture;

/**
 * Cliente de Red específico para el Módulo Marketplace.
 */
public class TradeClient {
    private static final String API_URL = "trades/";

    public static CompletableFuture<JsonArray> getOpenTrades() {
        return com.lider.minebridge.networking.BackendClient.getJsonArray(API_URL + "open");
    }

    public static CompletableFuture<Boolean> publishTrade(String sellerUuid, String sellerName, String title, JsonObject selling, com.google.gson.JsonElement asking) {
        JsonObject json = new JsonObject();
        json.addProperty("seller_uuid", sellerUuid);
        json.addProperty("seller", sellerName);
        json.addProperty("title", title);
        json.add("selling", selling);
        json.add("asking", asking);
        return com.lider.minebridge.networking.BackendClient.postJson(API_URL + "publish", json);
    }

    public static CompletableFuture<Boolean> cancelTrade(int tradeId) {
        return com.lider.minebridge.networking.BackendClient.postJson(API_URL + tradeId + "/cancel/", new JsonObject());
    }
}
