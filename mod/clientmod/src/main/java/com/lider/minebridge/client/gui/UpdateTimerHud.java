package com.lider.minebridge.client.gui;

import net.fabricmc.fabric.api.client.rendering.v1.HudRenderCallback;
import net.minecraft.client.MinecraftClient;
import net.minecraft.client.gui.DrawContext;
import net.minecraft.text.Text;

public class UpdateTimerHud {
    private static int remainingTicks = -1;

    public static void startTimer(int seconds) {
        remainingTicks = seconds * 20;
    }

    public static void tick() {
        if (remainingTicks > 0) {
            remainingTicks--;
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
                int width = client.getWindow().getScaledWidth();
                
                int seconds = remainingTicks / 20;
                String time = String.format("%02d:%02d", seconds / 60, seconds % 60);
                Text text = Text.literal("§b§l¡ACTUALIZACIÓN DE SERVIDOR! §fReinicio en: §e" + time);

                int textWidth = client.textRenderer.getWidth(text);
                int x = (width - textWidth) / 2;
                int y = 20;

                // Native style blue background
                drawContext.fill(x - 6, y - 4, x + textWidth + 6, y + 12, 0xBB0000AA);
                
                // Outer light blue border
                drawContext.fill(x - 7, y - 5, x + textWidth + 7, y - 4, 0xFF0055FF); // Top
                drawContext.fill(x - 7, y + 12, x + textWidth + 7, y + 13, 0xFF0055FF); // Bottom
                drawContext.fill(x - 7, y - 4, x - 6, y + 12, 0xFF0055FF); // Left
                drawContext.fill(x + textWidth + 6, y - 4, x + textWidth + 7, y + 12, 0xFF0055FF); // Right

                drawContext.drawText(client.textRenderer, text, x, y, 0xFFFFFF, true);
            }
        });
    }
}
