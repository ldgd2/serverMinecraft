package com.lider.minebridge.ui.framework.components;

import com.lider.minebridge.ui.framework.core.UIConstants;
import com.lider.minebridge.ui.framework.widgets.LabelWidget;
import net.minecraft.client.font.TextRenderer;
import net.minecraft.client.gui.DrawContext;
import net.minecraft.text.Text;

/**
 * Componente: Bloque completo de Inventario.
 */
public class InventoryComponent {
    public static void drawFull(DrawContext context, TextRenderer renderer, int x, int y) {
        LabelWidget.draw(context, renderer, Text.translatable("container.inventory").getString(), x, y, UIConstants.TEXT_DEFAULT, false);
        GridComponent.draw(context, x - 1, y + 11, 9, 3);
        GridComponent.draw(context, x - 1, y + 69, 9, 1);
    }
}
