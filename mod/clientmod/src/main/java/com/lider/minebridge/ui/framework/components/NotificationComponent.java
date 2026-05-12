package com.lider.minebridge.ui.framework.components;

import com.lider.minebridge.ui.framework.core.UIConstants;
import com.lider.minebridge.ui.framework.widgets.IconWidget;
import com.lider.minebridge.ui.framework.widgets.LabelWidget;
import net.minecraft.client.font.TextRenderer;
import net.minecraft.client.gui.DrawContext;

/**
 * Componente: Notificación flotante (Toast).
 */
public class NotificationComponent {
    
    public static void draw(DrawContext context, TextRenderer renderer, String message, int x, int y) {
        int textWidth = renderer.getWidth(message);
        int width = textWidth + 35;
        int height = 28;
        
        // 1. Fondo Glass Premium
        com.lider.minebridge.ui.framework.UIGradients.drawGlassPanel(context, x, y, width, height, 0xAAFFCC00);
        
        // 2. Icono de información con Glow
        IconWidget.drawInfo(context, x + 8, y + 8);
        
        // 3. Texto con sombra nítida
        LabelWidget.draw(context, renderer, "§f" + message, x + 24, y + 10, 0xFFFFFF, true);
        
        // 4. Barra lateral de estado animada (Color Oro)
        context.fill(x, y, x + 3, y + height, 0xFFFFCC00);
    }
}
