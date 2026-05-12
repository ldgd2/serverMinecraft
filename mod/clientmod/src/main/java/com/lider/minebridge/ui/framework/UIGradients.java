package com.lider.minebridge.ui.framework;

import net.minecraft.client.gui.DrawContext;

public class UIGradients {
    
    /**
     * Dibuja un gradiente vertical premium (Glow).
     */
    public static void drawVerticalGradient(DrawContext context, int x, int y, int width, int height, int startColor, int endColor) {
        context.fillGradient(x, y, x + width, y + height, startColor, endColor);
    }

    /**
     * Dibuja un fondo de cristal (Glassmorphism) con borde brillante.
     */
    public static void drawGlassPanel(DrawContext context, int x, int y, int width, int height, int glowColor) {
        // Cuerpo translúcido
        context.fill(x, y, x + width, y + height, 0xAA000000);
        
        // Brillo superior (Efecto cristal)
        context.fillGradient(x, y, x + width, y + (height / 2), 0x33FFFFFF, 0x00FFFFFF);
        
        // Borde fino brillante
        context.fill(x, y, x + width, y + 1, glowColor); // Top
        context.fill(x, y + height - 1, x + width, y + height, glowColor); // Bottom
        context.fill(x, y, x + 1, y + height, glowColor); // Left
        context.fill(x + width - 1, y, x + width, y + height, glowColor); // Right
    }
}
