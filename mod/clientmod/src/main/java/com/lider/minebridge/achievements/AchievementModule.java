package com.lider.minebridge.achievements;

import com.lider.minebridge.achievements.networking.AchievementUnlockPayload;
import com.lider.minebridge.ui.framework.components.AchievementToastComponent;
import net.fabricmc.fabric.api.client.networking.v1.ClientPlayNetworking;
import net.fabricmc.fabric.api.client.rendering.v1.HudRenderCallback;
import net.minecraft.client.MinecraftClient;

/**
 * Módulo de Logros (Cliente): Gestiona la visualización de notificaciones premium.
 */
public class AchievementModule {
    private static String currentToastTitle = null;
    private static long toastStartTime = 0;
    private static final long TOAST_DURATION = 5000; // 5 segundos

    public static void initClient() {
        // Receptor de desbloqueo de logros
        ClientPlayNetworking.registerGlobalReceiver(AchievementUnlockPayload.ID, (payload, context) -> {
            context.client().execute(() -> {
                currentToastTitle = payload.title();
                toastStartTime = System.currentTimeMillis();
                
                // Sonido premium de logro
                context.client().player.playSound(net.minecraft.sound.SoundEvents.UI_TOAST_CHALLENGE_COMPLETE, 1.0f, 1.0f);
            });
        });

        // Callback de renderizado en el HUD (HUD es la pantalla de juego normal)
        HudRenderCallback.EVENT.register((context, delta) -> {
            if (currentToastTitle != null) {
                long elapsed = System.currentTimeMillis() - toastStartTime;
                if (elapsed < TOAST_DURATION) {
                    // Dibujar el toast en la esquina superior derecha
                    int x = context.getScaledWindowWidth() - 170;
                    int y = 10;
                    
                    // Efecto de entrada/salida (opcional pero premium)
                    AchievementToastComponent.draw(context, MinecraftClient.getInstance().textRenderer, currentToastTitle, x, y);
                } else {
                    currentToastTitle = null;
                }
            }
        });
    }
}
