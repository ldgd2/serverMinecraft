package com.lider.minebridge.ui.framework;

import net.minecraft.client.gui.DrawContext;

/**
 * Módulo de Fondos: Maneja la renderización de contenedores y superficies.
 */
public class UIBackgrounds {
    
    /**
     * Dibuja un panel estilo Minecraft con bordes 3D.
     */
    public static void drawPanel(DrawContext context, int x, int y, int width, int height) {
        // Fondo base
        context.fill(x, y, x + width, y + height, UIBase.PANEL_BG);
        
        // Bordes de luz (Arriba e Izquierda)
        context.fill(x, y, x + width, y + 1, UIBase.PANEL_LIGHT);
        context.fill(x, y, x + 1, y + height, UIBase.PANEL_LIGHT);
        
        // Bordes de sombra (Abajo y Derecha)
        context.fill(x, y + height - 1, x + width, y + height, UIBase.PANEL_DARK);
        context.fill(x + width - 1, y, x + width, y + height, UIBase.PANEL_DARK);
    }
    
    /**
     * Dibuja un overlay oscuro estándar para fondos de menús.
     */
    public static void drawWorldBlur(DrawContext context, int screenWidth, int screenHeight) {
        context.fill(0, 0, screenWidth, screenHeight, 0x88000000);
    }

    /**
     * Dibuja un recuadro hundido (tipo campo de texto o lista).
     */
    public static void drawInsetPanel(DrawContext context, int x, int y, int width, int height) {
        context.fill(x, y, x + width, y + height, 0xFF000000); // Fondo negro
        context.fill(x, y, x + width, y + 1, UIBase.PANEL_DARK);
        context.fill(x, y, x + 1, y + height, UIBase.PANEL_DARK);
        context.fill(x, y + height - 1, x + width, y + height, UIBase.PANEL_LIGHT);
        context.fill(x + width - 1, y, x + width, y + height, UIBase.PANEL_LIGHT);
    }
}
