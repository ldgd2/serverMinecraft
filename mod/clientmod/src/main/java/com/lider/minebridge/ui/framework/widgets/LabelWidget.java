package com.lider.minebridge.ui.framework.widgets;

import com.lider.minebridge.ui.framework.core.UIConstants;
import net.minecraft.client.font.TextRenderer;
import net.minecraft.client.gui.DrawContext;
import net.minecraft.text.Text;

/**
 * Átomo: Etiqueta de texto genérica.
 */
public class LabelWidget {
    public static void draw(DrawContext context, TextRenderer renderer, String text, int x, int y, int color, boolean shadow) {
        if (shadow) {
            context.drawTextWithShadow(renderer, text, x, y, color);
        } else {
            context.drawText(renderer, text, x, y, color, false);
        }
    }

    public static void drawCentered(DrawContext context, TextRenderer renderer, Text text, int centerX, int y, int color) {
        context.drawCenteredTextWithShadow(renderer, text, centerX, y, color);
    }
}
