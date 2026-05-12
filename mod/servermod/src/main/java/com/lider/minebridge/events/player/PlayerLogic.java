package com.lider.minebridge.events.player;

import com.lider.minebridge.MineBridge;
import com.lider.minebridge.networking.AchievementClient;
import net.fabricmc.fabric.api.message.v1.ServerMessageEvents;
import net.fabricmc.fabric.api.networking.v1.ServerPlayConnectionEvents;
import net.minecraft.entity.damage.DamageSource;
import net.minecraft.server.network.ServerPlayerEntity;
import net.minecraft.text.Text;

import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;

/**
 * PlayerLogic — Versión ultraligera.
 */
public class PlayerLogic {

    private static final ConcurrentHashMap<String, Integer> chatMessagesSession = new ConcurrentHashMap<>();
    private static final ConcurrentHashMap<String, Integer> deathsTotalSession = new ConcurrentHashMap<>();
    private static final ConcurrentHashMap<String, Boolean> verifiedPlayers = new ConcurrentHashMap<>();

    public static void init() {
        // Receptor de Handshake de Seguridad
        net.fabricmc.fabric.api.networking.v1.ServerPlayNetworking.registerGlobalReceiver(com.lider.minebridge.networking.payload.ModHandshakePayload.ID, (payload, context) -> {
            String name = context.player().getName().getString();
            String token = payload.token();
            
            com.lider.minebridge.networking.SecurityClient.verifyPlayerSession(name, token).thenAccept(success -> {
                if (success) {
                    verifiedPlayers.put(name, true);
                    MineBridge.LOGGER.info("[Security] Player " + name + " verified successfully via Mod.");
                } else {
                    MineBridge.LOGGER.warn("[Security] Player " + name + " failed mod verification.");
                    context.player().getServer().execute(() -> {
                        context.player().networkHandler.disconnect(Text.literal("§cError de Autenticación:\n§7No se pudo validar tu sesión con el Mod."));
                    });
                }
            });
        });
        ServerMessageEvents.CHAT_MESSAGE.register((message, sender, params) -> {
            String uuid = sender.getUuidAsString();
            String content = message.getContent().getString();
            AchievementClient.sendChatMessage(uuid, sender.getName().getString(), content, "chat");
            chatMessagesSession.merge(uuid, 1, Integer::sum);
        });

        ServerPlayConnectionEvents.INIT.register((handler, server) -> {
            com.lider.minebridge.networking.SkinClient.syncSkin(handler.getPlayer());
        });

        ServerPlayConnectionEvents.JOIN.register((handler, sender, server) -> {
            ServerPlayerEntity player = handler.getPlayer();
            String uuid = player.getUuidAsString();
            String name = player.getName().getString();
            
            String ip = "unknown";
            try { ip = player.getIp(); } catch (Exception e) {}
            
            AchievementClient.sendJoinEvent(uuid, name, ip);
            AchievementClient.sendChatMessage(uuid, name, "se ha unido.", "join");

            // --- SEGURIDAD: Iniciar Proceso de Verificación ---
            // 1. Enviar petición de Handshake
            net.fabricmc.fabric.api.networking.v1.ServerPlayNetworking.send(player, new com.lider.minebridge.networking.payload.ModHandshakePayload("request"));

            // 2. Programar Kick si no se verifica en 10 segundos
            com.lider.minebridge.networking.NetworkManager.getScheduler().schedule(() -> {
                if (!verifiedPlayers.getOrDefault(name, false)) {
                    server.execute(() -> {
                        if (player.networkHandler.isConnectionOpen()) {
                            MineBridge.LOGGER.warn("[Security] Kicking " + name + " - Mod Handshake Timeout");
                            player.networkHandler.disconnect(Text.literal("§cAcceso Denegado:\n§7Debes usar el Launcher oficial con el Mod instalado."));
                        }
                    });
                }
            }, 10, java.util.concurrent.TimeUnit.SECONDS);
        });

        ServerPlayConnectionEvents.DISCONNECT.register((handler, server) -> {
            String name = handler.getPlayer().getName().getString();
            verifiedPlayers.remove(name);
            onPlayerLeaveCleanup(handler.getPlayer().getUuidAsString());
        });
    }

    public static void onPlayerDeath(ServerPlayerEntity player, DamageSource source, Text deathMsg) {
        String uuid = player.getUuidAsString();
        deathsTotalSession.merge(uuid, 1, Integer::sum);
        AchievementClient.sendChatMessage(uuid, player.getName().getString(), deathMsg.getString(), "death");
    }

    private static void onPlayerLeaveCleanup(String uuid) {
        AchievementClient.clearSessionCache(uuid);
        Map<String, Integer> stats = new java.util.HashMap<>();
        Integer chat = chatMessagesSession.remove(uuid);
        if (chat != null) stats.put("chat_message", chat);
        Integer deaths = deathsTotalSession.remove(uuid);
        if (deaths != null) stats.put("death_total", deaths);
        if (!stats.isEmpty()) AchievementClient.sendSessionSummary(uuid, stats);
    }
}
