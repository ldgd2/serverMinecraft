package com.lider.minebridge.ui.framework.components;

import com.lider.minebridge.ui.framework.core.UIConstants;
import net.minecraft.client.gui.DrawContext;

/**
 * Componente: Contenedor tipo Panel Minecraft.
 */
public class PanelComponent {
    public static void draw(DrawContext context, int x, int y, int width, int height) {
        context.fill(x, y, x + width, y + height, UIConstants.PANEL_BG);
        context.fill(x, y, x + width, y + 1, UIConstants.PANEL_LIGHT);
        context.fill(x, y, x + 1, y + height, UIConstants.PANEL_LIGHT);
        context.fill(x, y + height - 1, x + width, y + height, UIConstants.PANEL_DARK);
        context.fill(x + width - 1, y, x + width, y + height, UIConstants.PANEL_DARK);
    }
    
    public static void drawInset(DrawContext context, int x, int y, int width, int height) {
        context.fill(x, y, x + width, y + height, 0xFF000000);
        context.fill(x, y, x + width, y + 1, UIConstants.PANEL_DARK);
        context.fill(x, y, x + 1, y + height, UIConstants.PANEL_DARK);
        context.fill(x, y + height - 1, x + width, y + height, UIConstants.PANEL_LIGHT);
        context.fill(x + width - 1, y, x + width, y + height, UIConstants.PANEL_LIGHT);
    }
}
