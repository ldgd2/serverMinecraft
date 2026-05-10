package com.lider.minebridge.networking;

import com.google.gson.Gson;
import com.google.gson.JsonArray;
import com.google.gson.JsonObject;
import java.net.URI;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.util.concurrent.CompletableFuture;

/**
 * Cliente API simplificado para la interfaz del cliente.
 */
public class BackendClient {
    private static final Gson gson = new Gson();
    private static String activeUrl = "http://localhost:8000/api/v1/";

    public static void updateUrl(String url) {
        if (url == null) return;
        String base = url.endsWith("/") ? url : url + "/";
        activeUrl = base + "api/v1/";
    }

    public static CompletableFuture<JsonArray> getJsonArray(String endpoint) {
        String fullUrl = endpoint.startsWith("http") ? endpoint : activeUrl + endpoint;
        HttpRequest request = HttpRequest.newBuilder()
            .uri(URI.create(fullUrl))
            .GET()
            .build();
        return NetworkManager.getHttpClient().sendAsync(request, HttpResponse.BodyHandlers.ofString())
            .thenApply(res -> {
                try {
                    JsonObject root = gson.fromJson(res.body(), JsonObject.class);
                    if (root.has("data") && root.get("data").isJsonArray()) {
                        return root.getAsJsonArray("data");
                    }
                    return new JsonArray();
                } catch (Exception e) {
                    System.err.println("[MineBridge] Error parseando JSON: " + e.getMessage());
                    return new JsonArray();
                }
            });
    }

    public static CompletableFuture<Boolean> postJson(String endpoint, JsonObject data) {
        String fullUrl = endpoint.startsWith("http") ? endpoint : activeUrl + endpoint;
        HttpRequest request = HttpRequest.newBuilder()
            .uri(URI.create(fullUrl))
            .header("Content-Type", "application/json")
            .POST(HttpRequest.BodyPublishers.ofString(data.toString()))
            .build();
        return NetworkManager.getHttpClient().sendAsync(request, HttpResponse.BodyHandlers.ofString())
            .thenApply(res -> res.statusCode() == 200 || res.statusCode() == 201);
    }
}
