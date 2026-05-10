package com.lider.minebridge.ui.framework.widgets;

import net.minecraft.client.gui.DrawContext;

/**
 * Átomo: Barra de progreso genérica.
 */
public class ProgressBarWidget {
    
    /**
     * Dibuja una barra de progreso con estilo Minecraft.
     * @param progress Valor de 0.0 a 1.0
     */
    public static void draw(DrawContext context, int x, int y, int width, int height, float progress, int color) {
        // Fondo (Contenedor hundido)
        context.fill(x, y, x + width, y + height, 0xFF000000);
        context.fill(x, y, x + width, y + 1, 0xFF555555);
        context.fill(x, y, x + 1, y + height, 0xFF555555);
        context.fill(x, y + height - 1, x + width, y + height, 0xFFFFFFFF);
        context.fill(x + width - 1, y, x + width, y + height, 0xFFFFFFFF);
        
        // Relleno de progreso
        int fillWidth = (int) ((width - 2) * progress);
        if (fillWidth > 0) {
            context.fill(x + 1, y + 1, x + 1 + fillWidth, y + height - 1, color);
        }
    }
}
