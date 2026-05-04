package com.lider.minebridge.networking;

import com.google.gson.JsonObject;
import com.google.gson.JsonParser;
import com.lider.minebridge.MineBridge;
import com.lider.minebridge.config.ModConfig;
import com.mojang.authlib.properties.Property;
import net.minecraft.network.packet.s2c.play.PlayerListS2CPacket;
import net.minecraft.server.network.ServerPlayerEntity;

import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.util.EnumSet;

/**
 * Cliente para sincronizar skins directamente desde el Backend al GameProfile del jugador.
 * Esto bypass-ea a SkinRestorer si este falla.
 */
public class SkinClient {
    private static final HttpClient client = HttpClient.newHttpClient();

    public static void syncSkin(ServerPlayerEntity player) {
        syncSkin(player, null);
    }

    public static void syncSkin(ServerPlayerEntity player, Runnable onComplete) {
        // Ejecutar de forma asíncrona sin retrasos innecesarios para que la skin esté lista
        // antes de que el jugador sea renderizado completamente para los demás.
        java.util.concurrent.CompletableFuture.runAsync(() -> {
            performSync(player, onComplete);
        });
    }

    private static void performSync(ServerPlayerEntity player, Runnable onComplete) {
        String baseUrl = ModConfig.getBackendUrl();
        if (baseUrl == null || baseUrl.isEmpty() || baseUrl.equals("PENDING")) return;
        
        String url = (baseUrl.endsWith("/") ? baseUrl : baseUrl + "/") + "api/v1/players/skin/" + player.getName().getString();

        // MineBridge.LOGGER.info("[MineBridge] Sincronizando skin desde: " + url);

        client.sendAsync(
            HttpRequest.newBuilder()
                .uri(URI.create(url))
                .header("X-API-Key", ModConfig.getApiKey())
                .GET()
                .build(),
            HttpResponse.BodyHandlers.ofString()
        ).thenAccept(response -> {
            if (response.statusCode() == 200) {
                try {
                    JsonObject json = JsonParser.parseString(response.body()).getAsJsonObject();
                    String value = json.get("value").getAsString();
                    String signature = json.get("signature").getAsString();

                    if (value != null && !value.isEmpty()) {
                        // Importante: Ejecutar en el hilo principal del servidor
                        MineBridge.getServer().execute(() -> {
                            try {
                                // 1. Inyectar en el GameProfile
                                player.getGameProfile().getProperties().removeAll("textures");
                                player.getGameProfile().getProperties().put("textures", new Property("textures", value, signature));

                                // 2. Notificar a TODOS los clientes (Refresco total)
                                refreshPlayerForOthers(player, value, signature);
                                
                                // MineBridge.LOGGER.info("[MineBridge] ✅ Skin inyectada con éxito para: " + player.getName().getString());
                                if (onComplete != null) onComplete.run();
                            } catch (Exception e) {
                                MineBridge.LOGGER.error("[MineBridge] Error inyectando skin en hilo principal: " + e.getMessage());
                            }
                        });
                    }
                } catch (Exception e) {
                    MineBridge.LOGGER.error("[MineBridge] Error procesando skin: " + e.getMessage());
                }
            } else {
                MineBridge.LOGGER.warn("[MineBridge] API de skin devolvió código: " + response.statusCode());
            }
        }).exceptionally(ex -> {
            MineBridge.LOGGER.error("[MineBridge] Fallo de red en SkinClient: " + ex.getMessage());
            return null;
        });
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
                // Client mod is installed, use the ultra-smooth native payload injection
                net.fabricmc.fabric.api.networking.v1.ServerPlayNetworking.send(other, payload);
            } else {
                // Vanilla client fallback: remove and add to tablist
                other.networkHandler.sendPacket(removePacket);
                other.networkHandler.sendPacket(addPacket);
            }
        }
    }
}
