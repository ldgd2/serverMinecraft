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
        AchievementPersistence.load();
        PayloadTypeRegistry.playC2S().register(AchievementUnlockPayload.ID, AchievementUnlockPayload.CODEC);
        PayloadTypeRegistry.playS2C().register(AchievementUnlockPayload.ID, AchievementUnlockPayload.CODEC);
        
        ServerPlayNetworking.registerGlobalReceiver(AchievementUnlockPayload.ID, (payload, context) -> {
            String key = payload.achievementId();
            String uuid = context.player().getUuidAsString();
            
            // Si ya está desbloqueado, ignorar totalmente
            if (AchievementPersistence.hasUnlocked(uuid, key)) return;

            com.lider.minebridge.core.MineCore.sync(() -> {
                // Doble verificación dentro del hilo principal por seguridad
                if (AchievementPersistence.hasUnlocked(uuid, key)) return;
                
                AchievementPersistence.unlock(uuid, key);
                String title = payload.title();
                String playerName = context.player().getName().getString();
                
                // Anuncio global (solo la primera vez)
                context.server().getPlayerManager().broadcast(
                    net.minecraft.text.Text.of("§6[Logro] §f" + playerName + " ha desbloqueado: §e" + title),
                    false
                );

                if (MineBridge.getBackendClient() != null) {
                    String ip = context.player().getIp();
                    com.lider.minebridge.core.MineCore.async(() -> {
                        com.lider.minebridge.networking.AchievementClient.sendEvent(
                            uuid,
                            key,
                            1,
                            ip
                        );
                    });
                }
            });
        });
    }
}
