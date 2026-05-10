package com.lider.minebridge.ui.framework.widgets;

import com.lider.minebridge.ui.framework.core.UIConstants;
import net.minecraft.client.gui.DrawContext;

/**
 * Átomo: Slot de Inventario individual.
 */
public class SlotWidget {
    public static void draw(DrawContext context, int x, int y) {
        context.fill(x, y, x + 18, y + 18, UIConstants.SLOT_BG);
        context.fill(x, y, x + 18, y + 1, UIConstants.SLOT_DARK);
        context.fill(x, y, x + 1, y + 18, UIConstants.SLOT_DARK);
        context.fill(x, y + 17, x + 18, y + 18, UIConstants.SLOT_LIGHT);
        context.fill(x + 17, y, x + 18, y + 18, UIConstants.SLOT_LIGHT);
    }
}
