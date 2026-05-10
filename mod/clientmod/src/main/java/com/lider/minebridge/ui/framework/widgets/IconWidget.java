package com.lider.minebridge.ui.framework.widgets;

import net.minecraft.client.MinecraftClient;
import net.minecraft.client.gui.DrawContext;

/**
 * Átomo: Iconos y Símbolos de estado.
 */
public class IconWidget {
    
    public static void drawArrow(DrawContext context, int x, int y, int color) {
        context.drawText(MinecraftClient.getInstance().textRenderer, "➔", x, y, color, false);
    }

    public static void drawWarning(DrawContext context, int x, int y) {
        context.drawText(MinecraftClient.getInstance().textRenderer, "⚠", x, y, 0xFFFF5555, true);
    }

    public static void drawInfo(DrawContext context, int x, int y) {
        context.drawText(MinecraftClient.getInstance().textRenderer, "ℹ", x, y, 0xFF5555FF, true);
    }

    public static void drawSuccess(DrawContext context, int x, int y) {
        context.drawText(MinecraftClient.getInstance().textRenderer, "✔", x, y, 0xFF55FF55, true);
    }
    
    public static void drawClock(DrawContext context, int x, int y) {
        context.drawText(MinecraftClient.getInstance().textRenderer, "⌚", x, y, 0xFFFFAA00, true);
    }
}
