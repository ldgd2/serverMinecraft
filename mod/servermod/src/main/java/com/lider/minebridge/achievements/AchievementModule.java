package com.lider.minebridge.achievements;

import com.lider.minebridge.achievements.networking.AchievementUnlockPayload;
import net.fabricmc.fabric.api.networking.v1.PayloadTypeRegistry;
import net.fabricmc.fabric.api.networking.v1.ServerPlayNetworking;
import com.lider.minebridge.MineBridge;

/**
 * Módulo de Logros (Servidor).
 */
public class AchievementModule {

    public static void initCommon() {
        PayloadTypeRegistry.playC2S().register(AchievementUnlockPayload.ID, AchievementUnlockPayload.CODEC);
        
        ServerPlayNetworking.registerGlobalReceiver(AchievementUnlockPayload.ID, (payload, context) -> {
            context.server().execute(() -> {
                String key = payload.achievementId();
                String title = payload.title();
                String playerName = context.player().getName().getString();
                
                // Anuncio global
                context.server().getPlayerManager().broadcast(
                    net.minecraft.text.Text.of("§6[Logro] §f" + playerName + " ha desbloqueado: §e" + title),
                    false
                );

                if (MineBridge.getBackendClient() != null) {
                    com.lider.minebridge.networking.AchievementClient.sendEvent(
                        context.player().getUuidAsString(),
                        key,
                        1
                    );
                }
            });
        });
    }
}
