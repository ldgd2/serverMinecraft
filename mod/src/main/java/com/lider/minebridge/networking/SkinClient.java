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
        String baseUrl = ModConfig.getBackendUrl();
        if (baseUrl == null || baseUrl.isEmpty() || baseUrl.equals("PENDING")) return;
        
        String url = (baseUrl.endsWith("/") ? baseUrl : baseUrl + "/") + "api/v1/players/skin/" + player.getName().getString();

        MineBridge.LOGGER.info("[MineBridge] Sincronizando skin desde: " + url);

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
                                refreshPlayerForOthers(player);
                                
                                MineBridge.LOGGER.info("[MineBridge] ✅ Skin inyectada con éxito para: " + player.getName().getString());
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

    /**
     * Fuerza a que todos los demás jugadores vuelvan a cargar la entidad y el perfil de este jugador.
     */
    private static void refreshPlayerForOthers(ServerPlayerEntity player) {
        var playerManager = MineBridge.getServer().getPlayerManager();
        
        // 1. Paquete para actualizar la lista (Propiedades del Profile)
        PlayerListS2CPacket removePacket = new PlayerListS2CPacket(EnumSet.of(PlayerListS2CPacket.Action.UPDATE_LISTED), java.util.List.of(player));
        PlayerListS2CPacket addPacket = new PlayerListS2CPacket(EnumSet.of(PlayerListS2CPacket.Action.ADD_PLAYER, PlayerListS2CPacket.Action.UPDATE_LISTED), java.util.List.of(player));
        
        // 2. Paquetes para destruir y volver a spawnear la entidad (Visual)
        // En 1.21.1 se usa EntitiesDestroyS2CPacket (plural)
        net.minecraft.network.packet.s2c.play.EntitiesDestroyS2CPacket destroyPacket = new net.minecraft.network.packet.s2c.play.EntitiesDestroyS2CPacket(player.getId());
        net.minecraft.network.packet.s2c.play.EntitySpawnS2CPacket spawnPacket = new net.minecraft.network.packet.s2c.play.EntitySpawnS2CPacket(player, 0, player.getBlockPos());

        for (ServerPlayerEntity other : playerManager.getPlayerList()) {
            if (other == player) continue;
            
            // Refrescar en el Tab
            other.networkHandler.sendPacket(removePacket);
            other.networkHandler.sendPacket(addPacket);
            
            // Refrescar en el Mundo (si está cerca)
            other.networkHandler.sendPacket(destroyPacket);
            other.networkHandler.sendPacket(spawnPacket);
        }
    }
}
