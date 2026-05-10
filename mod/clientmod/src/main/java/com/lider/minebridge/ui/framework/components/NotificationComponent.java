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
        int width = textWidth + 30;
        int height = 24;
        
        // Fondo tipo Inset para notificaciones
        PanelComponent.draw(context, x, y, width, height);
        
        // Icono de información
        IconWidget.drawInfo(context, x + 6, y + 8);
        
        // Texto
        LabelWidget.draw(context, renderer, "§f" + message, x + 20, y + 8, 0xFFFFFF, false);
        
        // Borde decorativo lateral (Color del mod)
        context.fill(x, y, x + 2, y + height, 0xFFFFCC00);
    }
}
