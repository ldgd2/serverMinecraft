package com.lider.minebridge.networking;

import com.google.gson.JsonObject;
import com.google.gson.JsonParser;
import com.lider.minebridge.MineBridge;
import com.lider.minebridge.config.ModConfig;
import com.mojang.authlib.properties.Property;
import net.minecraft.network.packet.s2c.play.PlayerListS2CPacket;
import net.minecraft.server.network.ServerPlayerEntity;

import java.util.concurrent.CompletableFuture;
import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.util.EnumSet;

/**
 * Cliente para sincronizar skins directamente desde el Backend al GameProfile del jugador.
 * Optimizado para no bloquear el hilo principal del servidor utilizando NetworkManager.
 */
public class SkinClient {
    private static final HttpClient client = NetworkManager.getHttpClient();

    public static void syncSkin(ServerPlayerEntity player) {
        syncSkin(player, null);
    }

    public static void syncSkin(ServerPlayerEntity player, Runnable onComplete) {
        NetworkManager.getExecutor().submit(() -> {
            performSync(player, onComplete);
        });
    }

    private static void performSync(ServerPlayerEntity player, Runnable onComplete) {
        CompletableFuture.supplyAsync(() -> {
            try {
                String baseUrl = ModConfig.getBackendUrl();
                if (baseUrl == null || baseUrl.isEmpty() || baseUrl.equals("PENDING")) return null;
                
                String url = baseUrl + (baseUrl.endsWith("/") ? "" : "/") + "api/v1/players/skin/" + player.getName().getString();

                HttpRequest request = HttpRequest.newBuilder()
                        .uri(URI.create(url))
                        .header("X-API-Key", ModConfig.getApiKey())
                        .timeout(java.time.Duration.ofSeconds(5))
                        .GET()
                        .build();

                return client.send(request, HttpResponse.BodyHandlers.ofString());
            } catch (Exception e) {
                return null;
            }
        }, NetworkManager.getExecutor()).thenAccept(response -> {
            if (response != null && response.statusCode() == 200) {
                try {
                    JsonObject json = JsonParser.parseString(response.body()).getAsJsonObject();
                    String value = json.get("value").getAsString();
                    String signature = json.get("signature").getAsString();

                    if (value != null && !value.isEmpty()) {
                        MineBridge.getServer().execute(() -> {
                            try {
                                player.getGameProfile().getProperties().removeAll("textures");
                                player.getGameProfile().getProperties().put("textures", new Property("textures", value, signature));
                                refreshPlayerForOthers(player, value, signature);
                                if (onComplete != null) onComplete.run();
                            } catch (Exception e) {}
                        });
                    }
                } catch (Exception e) {}
            }
        }).exceptionally(ex -> null);
    }

    public static void refreshPlayerForOthers(ServerPlayerEntity player, String value, String signature) {
        var playerManager = MineBridge.getServer().getPlayerManager();
        if (playerManager == null) return;

        net.minecraft.network.packet.s2c.play.PlayerRemoveS2CPacket removePacket = 
            new net.minecraft.network.packet.s2c.play.PlayerRemoveS2CPacket(java.util.List.of(player.getUuid()));
            
        PlayerListS2CPacket addPacket = 
            new PlayerListS2CPacket(EnumSet.of(PlayerListS2CPacket.Action.ADD_PLAYER, PlayerListS2CPacket.Action.UPDATE_LISTED), java.util.List.of(player));
            
        com.lider.minebridge.networking.payload.SyncSkinPayload payload = 
            new com.lider.minebridge.networking.payload.SyncSkinPayload(player.getUuid(), value, signature);

        for (ServerPlayerEntity other : playerManager.getPlayerList()) {
            if (net.fabricmc.fabric.api.networking.v1.ServerPlayNetworking.canSend(other, com.lider.minebridge.networking.payload.SyncSkinPayload.ID)) {
                net.fabricmc.fabric.api.networking.v1.ServerPlayNetworking.send(other, payload);
            } else {
                other.networkHandler.sendPacket(removePacket);
                other.networkHandler.sendPacket(addPacket);
            }
        }
    }
}
