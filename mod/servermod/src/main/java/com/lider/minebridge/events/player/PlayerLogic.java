package com.lider.minebridge.events.player;

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

    public static void init() {
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
        });

        ServerPlayConnectionEvents.DISCONNECT.register((handler, server) -> {
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
