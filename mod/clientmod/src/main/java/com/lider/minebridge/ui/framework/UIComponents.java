package com.lider.minebridge.ui.framework;

import net.minecraft.client.font.TextRenderer;
import net.minecraft.client.gui.DrawContext;

/**
 * Biblioteca de Componentes Compuestos (Genéricos)
 */
public class UIComponents {

    /**
     * Dibuja una cuadrícula genérica de slots.
     */
    public static void drawSlotGrid(DrawContext context, int x, int y, int cols, int rows) {
        for (int r = 0; r < rows; r++) {
            for (int c = 0; c < cols; c++) {
                UIWidgets.drawSlot(context, x + c * 18, y + r * 18);
            }
        }
    }

    /**
     * Dibuja un grupo de ítems con título superior (Card Style).
     */
    public static void drawLabeledGrid(DrawContext context, TextRenderer renderer, String label, int x, int y, int cols, int rows) {
        UIWidgets.drawText(context, renderer, label, x, y, UIBase.TEXT_DEFAULT, false);
        drawSlotGrid(context, x, y + 10, cols, rows);
    }

    /**
     * Dibuja una sección de lista (Item List).
     */
    public static void drawListContainer(DrawContext context, int x, int y, int width, int height) {
        UIBackgrounds.drawInsetPanel(context, x, y, width, height);
    }

    /**
     * Dibuja un bloque de inventario (9x3).
     */
    public static void drawInventoryBlock(DrawContext context, int x, int y) {
        drawSlotGrid(context, x, y, 9, 3);
    }

    /**
     * Dibuja la hotbar (9x1).
     */
    public static void drawHotbarBlock(DrawContext context, int x, int y) {
        drawSlotGrid(context, x, y, 9, 1);
    }
}
