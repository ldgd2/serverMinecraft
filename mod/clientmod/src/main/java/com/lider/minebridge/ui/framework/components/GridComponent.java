package com.lider.minebridge.ui.framework.components;

import com.lider.minebridge.ui.framework.widgets.SlotWidget;
import net.minecraft.client.gui.DrawContext;

/**
 * Componente: Cuadrícula de slots.
 */
public class GridComponent {
    public static void draw(DrawContext context, int x, int y, int cols, int rows) {
        for (int r = 0; r < rows; r++) {
            for (int c = 0; c < cols; c++) {
                SlotWidget.draw(context, x + c * 18, y + r * 18);
            }
        }
    }
}
