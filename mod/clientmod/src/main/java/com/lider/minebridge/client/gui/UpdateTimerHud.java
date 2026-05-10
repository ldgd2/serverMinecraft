package com.lider.minebridge.client.gui;

import net.fabricmc.fabric.api.client.rendering.v1.HudRenderCallback;
import net.minecraft.client.MinecraftClient;
import net.minecraft.client.gui.DrawContext;
import net.minecraft.text.Text;
import net.minecraft.util.math.MathHelper;

public class UpdateTimerHud {
    private static int remainingTicks = -1;
    private static int elapsedTicks = 0;
    
    // Animation states
    private static final int ANIM_START_DELAY = 60; // 3s in center
    private static final int ANIM_MOVE_DURATION = 100; // 5s moving
    private static float currentX = -1;

    public static void startTimer(int seconds) {
        remainingTicks = seconds * 20;
        elapsedTicks = 0;
        currentX = -1; // Reset animation
    }

    public static void tick() {
        if (remainingTicks > 0) {
            remainingTicks--;
            elapsedTicks++;
            if (remainingTicks == 0) {
                MinecraftClient client = MinecraftClient.getInstance();
                if (client.world != null && client.getNetworkHandler() != null) {
                    client.getNetworkHandler().getConnection().disconnect(Text.literal("§b[MineBridge] §fActualización lista. El servidor se está reiniciando. Vuelve en un minuto."));
                }
            }
        }
    }

    public static void register() {
        HudRenderCallback.EVENT.register((drawContext, tickCounter) -> {
            if (remainingTicks > 0) {
                MinecraftClient client = MinecraftClient.getInstance();
                int screenWidth = client.getWindow().getScaledWidth();
                
                int seconds = remainingTicks / 20;
                String time = String.format("%02d:%02d", seconds / 60, seconds % 60);
                Text text = Text.literal("§b§l¡MANTENIMIENTO! §fReinicio en: §e" + time);

                int textWidth = client.textRenderer.getWidth(text);
                int centerX = (screenWidth - textWidth) / 2;
                int rightX = screenWidth - textWidth - 20;
                int y = 20;

                // --- Animation Logic ---
                float targetX;
                if (elapsedTicks < ANIM_START_DELAY) {
                    // Stage 1: Fade in/Stay at center
                    targetX = centerX;
                } else if (elapsedTicks < ANIM_START_DELAY + ANIM_MOVE_DURATION) {
                    // Stage 2: Slide to right
                    float progress = (float)(elapsedTicks - ANIM_START_DELAY) / ANIM_MOVE_DURATION;
                    // Use smooth step for premium feel
                    float smoothProgress = progress * progress * (3 - 2 * progress);
                    targetX = MathHelper.lerp(smoothProgress, centerX, rightX);
                } else {
                    // Stage 3: Stay at right
                    targetX = rightX;
                }

                // Smooth interpolation for currentX (avoids jitter)
                if (currentX == -1) currentX = targetX;
                currentX = MathHelper.lerp(0.1f, currentX, targetX);

                int x = (int)currentX;

                // --- Premium Drawing ---
                // Dark background with gradient-like border
                drawContext.fill(x - 8, y - 6, x + textWidth + 8, y + 14, 0xDD000000); // Black shadow
                drawContext.fill(x - 6, y - 4, x + textWidth + 6, y + 12, 0xCC000044); // Deep blue main
                
                // Animated glow border (subtle)
                int borderColor = 0xFF00AAFF;
                drawContext.fill(x - 7, y - 5, x + textWidth + 7, y - 4, borderColor); // Top
                drawContext.fill(x - 7, y + 12, x + textWidth + 7, y + 13, borderColor); // Bottom
                drawContext.fill(x - 7, y - 4, x - 6, y + 12, borderColor); // Left
                drawContext.fill(x + textWidth + 6, y - 4, x + textWidth + 7, y + 12, borderColor); // Right

                // Text with shadow
                drawContext.drawText(client.textRenderer, text, x, y, 0xFFFFFF, true);
            }
        });
    }
}
