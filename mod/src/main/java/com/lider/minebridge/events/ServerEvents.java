package com.lider.minebridge.events;

import com.lider.minebridge.MineBridge;
import net.fabricmc.fabric.api.entity.event.v1.ServerEntityCombatEvents;
import net.fabricmc.fabric.api.event.lifecycle.v1.ServerLifecycleEvents;
import net.fabricmc.fabric.api.event.player.PlayerBlockBreakEvents;
import net.fabricmc.fabric.api.message.v1.ServerMessageEvents;
import net.fabricmc.fabric.api.networking.v1.ServerPlayConnectionEvents;

public class ServerEvents {
    
    public static void init() {
        // Lifecycle events
        ServerLifecycleEvents.SERVER_STARTED.register(server -> {
            MineBridge.getBackendClient().notifyServerState("STARTED");
        });

        ServerLifecycleEvents.SERVER_STOPPING.register(server -> {
            MineBridge.getBackendClient().notifyServerState("STOPPING");
            MineBridge.getBackendClient().close();
        });

        // Chat events
        ServerMessageEvents.CHAT_MESSAGE.register((message, sender, params) -> {
            String content = message.getContent().getString();
            String player = sender.getName().getString();
            MineBridge.getBackendClient().sendChatMessage(player, content);
        });

        // Connection events
        ServerPlayConnectionEvents.JOIN.register((handler, sender, server) -> {
            String player = handler.getPlayer().getName().getString();
            String uuid = handler.getPlayer().getUuidAsString();
            MineBridge.getBackendClient().notifyPlayerJoin(player, uuid);
        });

        ServerPlayConnectionEvents.DISCONNECT.register((handler, server) -> {
            String player = handler.getPlayer().getName().getString();
            MineBridge.getBackendClient().notifyPlayerLeave(player);
        });

        // Statistics and Actions
        PlayerBlockBreakEvents.AFTER.register((world, player, pos, state, entity) -> {
            if (!world.isClient) {
                MineBridge.getBackendClient().notifyStatUpdate(player.getName().getString(), "block_broken", state.getBlock().getTranslationKey());
            }
        });

        ServerEntityCombatEvents.AFTER_KILLED_OTHER_ENTITY.register((world, entity, killedEntity) -> {
            if (entity instanceof net.minecraft.server.network.ServerPlayerEntity player) {
                MineBridge.getBackendClient().notifyStatUpdate(player.getName().getString(), "kill", killedEntity.getType().getTranslationKey());
            }
        });
    }
}
