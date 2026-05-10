package com.lider.minebridge.marketplace.networking;

import com.google.gson.JsonArray;
import com.google.gson.JsonObject;
import com.lider.minebridge.MineBridge;
import java.util.concurrent.CompletableFuture;

/**
 * Cliente de Red específico para el Módulo Marketplace (Servidor).
 */
public class TradeClient {
    // Nota: El BackendClient del servidor ya gestiona la URL base dinámicamente.
    // Usamos una ruta relativa que se completará con la activeUrl + api/v1/
    private static String getBaseUrl() {
        String base = MineBridge.getBackendClient().getActiveUrl();
        if (!base.endsWith("/")) base += "/";
        return base + "api/v1/trades/";
    }

    public static CompletableFuture<JsonArray> getOpenTrades() {
        return com.lider.minebridge.networking.BackendClient.getJsonArray(getBaseUrl() + "open");
    }

    public static CompletableFuture<Boolean> publishTrade(String sellerUuid, String sellerName, String title, com.google.gson.JsonElement selling, com.google.gson.JsonElement asking) {
        JsonObject json = new JsonObject();
        json.addProperty("seller_uuid", sellerUuid);
        json.addProperty("seller", sellerName);
        json.addProperty("title", title);
        json.add("selling", selling);
        json.add("asking", asking);
        return com.lider.minebridge.networking.BackendClient.postJson(getBaseUrl() + "publish", json);
    }

    public static CompletableFuture<Boolean> cancelTrade(int tradeId) {
        return com.lider.minebridge.networking.BackendClient.postJson(getBaseUrl() + tradeId + "/cancel", new JsonObject());
    }

    public static CompletableFuture<Boolean> completeTrade(int tradeId, String buyerUuid, String buyerName) {
        JsonObject json = new JsonObject();
        json.addProperty("buyer_uuid", buyerUuid);
        json.addProperty("buyer", buyerName);
        return com.lider.minebridge.networking.BackendClient.postJson(getBaseUrl() + tradeId + "/complete", json);
    }
}
