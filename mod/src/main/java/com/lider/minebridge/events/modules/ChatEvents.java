package com.lider.minebridge.events.modules;

import com.lider.minebridge.MineBridge;
import com.lider.minebridge.networking.AchievementClient;
import net.fabricmc.fabric.api.message.v1.ServerMessageEvents;
import net.fabricmc.fabric.api.networking.v1.ServerPlayConnectionEvents;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.network.ServerPlayerEntity;
import net.minecraft.text.Text;

public class ChatEvents {

    public static void register() {
        // 1. SALIENTE: Chat del Juego -> App
        ServerMessageEvents.CHAT_MESSAGE.register((message, sender, params) -> {
            String content = message.getContent().getString();
            AchievementClient.sendChatMessage(sender.getUuidAsString(), sender.getName().getString(), content, "chat");
            
            // Incrementar contador de logros sociales
            AchievementClient.sendEvent(sender.getUuidAsString(), "chat_message", 1);
        });

        // 2. SISTEMA: Join -> App
        ServerPlayConnectionEvents.JOIN.register((handler, sender, server) -> {
            ServerPlayerEntity player = handler.getPlayer();
            AchievementClient.sendChatMessage(player.getUuidAsString(), player.getName().getString(), "se ha unido al servidor.", "join");
        });

        // 3. SISTEMA: Leave -> App
        ServerPlayConnectionEvents.DISCONNECT.register((handler, server) -> {
            ServerPlayerEntity player = handler.getPlayer();
            AchievementClient.sendChatMessage(player.getUuidAsString(), player.getName().getString(), "ha abandonado el servidor.", "leave");
        });
    }

    /**
     * MÉTODO REAL: Broadcast desde la App hacia el Juego
     */
    public static void broadcastFromApp(String userFromApp, String message) {
        MinecraftServer server = MineBridge.getServer();
        if (server != null) {
            Text formatted = Text.literal("§8[§bAPP§8] §3" + userFromApp + "§7: " + message);
            server.getPlayerManager().broadcast(formatted, false);
        } else {
            MineBridge.LOGGER.error("Cannot broadcast from App: Server instance is null");
        }
    }

    /**
     * MÉTODO REAL: Enviar muertes a la App
     */
    public static void onPlayerDeath(ServerPlayerEntity player, Text deathMessage) {
        AchievementClient.sendChatMessage(
            player.getUuidAsString(), 
            player.getName().getString(), 
            deathMessage.getString(), 
            "death"
        );
    }
}
