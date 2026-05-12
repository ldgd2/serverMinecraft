package com.lider.minebridge.networking;

import com.google.gson.JsonObject;
import com.lider.minebridge.MineBridge;
import java.net.URI;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.util.concurrent.CompletableFuture;

public class SecurityClient {

    public static CompletableFuture<Boolean> verifyPlayerSession(String username, String token) {
        if (MineBridge.getBackendClient() == null) return CompletableFuture.completedFuture(false);
        
        String activeUrl = MineBridge.getBackendClient().getActiveUrl();
        if (activeUrl == null || activeUrl.equals("None")) return CompletableFuture.completedFuture(false);

        JsonObject payload = new JsonObject();
        payload.addProperty("username", username);
        payload.addProperty("token", token);

        HttpRequest request = HttpRequest.newBuilder()
                .uri(URI.create(activeUrl + "api/v1/bridge/verify-mod"))
                .header("Content-Type", "application/json")
                .timeout(java.time.Duration.ofSeconds(10))
                .POST(HttpRequest.BodyPublishers.ofString(payload.toString()))
                .build();

        return NetworkManager.getHttpClient().sendAsync(request, HttpResponse.BodyHandlers.ofString())
                .thenApply(res -> {
                    if (res.statusCode() == 200) {
                        return res.body().contains("verified");
                    }
                    return false;
                })
                .exceptionally(t -> {
                    MineBridge.LOGGER.error("Security verification failed for " + username + ": " + t.getMessage());
                    return false;
                });
    }
}
