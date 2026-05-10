package com.lider.minebridge.ui.framework;

import net.minecraft.client.font.TextRenderer;
import net.minecraft.client.gui.DrawContext;
import net.minecraft.text.Text;

/**
 * Biblioteca de Widgets Atómicos (Genéricos)
 */
public class UIWidgets {

    /**
     * Dibuja un slot genérico.
     */
    public static void drawSlot(DrawContext context, int x, int y) {
        context.fill(x, y, x + 18, y + 18, UIBase.SLOT_BG);
        context.fill(x, y, x + 18, y + 1, UIBase.SLOT_DARK);
        context.fill(x, y, x + 1, y + 18, UIBase.SLOT_DARK);
        context.fill(x, y + 17, x + 18, y + 18, UIBase.SLOT_LIGHT);
        context.fill(x + 17, y, x + 18, y + 18, UIBase.SLOT_LIGHT);
    }

    /**
     * Dibuja un texto con estilo (Sombra opcional, color opcional).
     */
    public static void drawText(DrawContext context, TextRenderer renderer, String text, int x, int y, int color, boolean shadow) {
        if (shadow) {
            context.drawTextWithShadow(renderer, text, x, y, color);
        } else {
            context.drawText(renderer, text, x, y, color, false);
        }
    }

    /**
     * Dibuja una línea separadora horizontal.
     */
    public static void drawHorizontalLine(DrawContext context, int x, int y, int width, int color) {
        context.fill(x, y, x + width, y + 1, color);
    }

    /**
     * Icono de flecha genérico.
     */
    public static void drawIconArrow(DrawContext context, int x, int y, int color) {
        context.drawText(net.minecraft.client.MinecraftClient.getInstance().textRenderer, "➔", x, y, color, false);
    }
    
    /**
     * Dibuja un badge (etiqueta pequeña con fondo).
     */
    public static void drawBadge(DrawContext context, TextRenderer renderer, String text, int x, int y, int bgColor, int textColor) {
        int width = renderer.getWidth(text) + 4;
        context.fill(x, y, x + width, y + 11, bgColor);
        context.drawText(renderer, text, x + 2, y + 2, textColor, false);
    }
}
