package com.lider.minebridge.ui.framework.components;

import com.lider.minebridge.ui.framework.widgets.IconWidget;
import com.lider.minebridge.ui.framework.widgets.LabelWidget;
import net.minecraft.client.font.TextRenderer;
import net.minecraft.client.gui.DrawContext;
import net.minecraft.text.Text;

/**
 * Componente: Cuadro de Alerta / Mensaje Importante.
 */
public class AlertComponent {
    
    public enum AlertType {
        RESTART(0xFFFF5555, "REINICIO"),
        WARNING(0xFFFFAA00, "ADVERTENCIA"),
        INFO(0xFF5555FF, "AVISO"),
        SUCCESS(0xFF55FF55, "ÉXITO");
        
        final int color;
        final String titlePrefix;
        AlertType(int color, String titlePrefix) { this.color = color; this.titlePrefix = titlePrefix; }
    }

    public static void draw(DrawContext context, TextRenderer renderer, AlertType type, String message, int x, int y, int width) {
        int height = 50;
        
        // 1. Fondo del Panel
        PanelComponent.draw(context, x, y, width, height);
        
        // 2. Icono y Título
        int iconX = x + 8;
        int iconY = y + 8;
        
        switch(type) {
            case RESTART -> IconWidget.drawClock(context, iconX, iconY);
            case WARNING -> IconWidget.drawWarning(context, iconX, iconY);
            case INFO -> IconWidget.drawInfo(context, iconX, iconY);
            case SUCCESS -> IconWidget.drawSuccess(context, iconX, iconY);
        }
        
        LabelWidget.draw(context, renderer, "§l" + type.titlePrefix, iconX + 12, iconY, type.color, false);
        
        // 3. Mensaje (Cuerpo)
        LabelWidget.draw(context, renderer, "§7" + message, x + 10, y + 25, 0xFFFFFF, false);
    }
}
