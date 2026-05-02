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
                        // 1. Inyectar en el GameProfile (Lógica del Servidor)
                        player.getGameProfile().getProperties().removeAll("textures");
                        player.getGameProfile().getProperties().put("textures", new Property("textures", value, signature));

                        // 2. Notificar a TODOS los clientes para que vean la skin nueva
                        // Usamos un truco: enviamos el paquete de actualización de lista de jugadores
                        // En 1.21.1 esto refresca las propiedades en los clientes
                        PlayerListS2CPacket packet = new PlayerListS2CPacket(
                            EnumSet.of(PlayerListS2CPacket.Action.UPDATE_LISTED, PlayerListS2CPacket.Action.UPDATE_DISPLAY_NAME), 
                            java.util.List.of(player)
                        );
                        
                        MineBridge.getServer().getPlayerManager().sendToAll(packet);
                        
                        MineBridge.LOGGER.info("[MineBridge] ✅ Skin inyectada con éxito para: " + player.getName().getString());
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
}
