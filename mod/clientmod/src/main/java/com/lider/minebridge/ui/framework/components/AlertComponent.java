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

    public static void draw(DrawContext context, TextRenderer renderer, AlertType type, String title, String desc, int x, int y, int width) {
        int height = 60;
        
        // 1. Fondo Glass Inmersivo (Con el color del tipo)
        com.lider.minebridge.ui.framework.UIGradients.drawGlassPanel(context, x, y, width, height, type.color | 0xAA000000);
        
        // 2. Icono y Título Centrados
        int iconX = x + (width / 2) - (renderer.getWidth(type.titlePrefix + ": " + title) / 2) - 10;
        int iconY = y + 10;
        
        switch(type) {
            case RESTART -> IconWidget.drawClock(context, iconX, iconY);
            case WARNING -> IconWidget.drawWarning(context, iconX, iconY);
            case INFO -> IconWidget.drawInfo(context, iconX, iconY);
            case SUCCESS -> IconWidget.drawSuccess(context, iconX, iconY);
        }
        
        LabelWidget.draw(context, renderer, "§l" + type.titlePrefix + ": §f" + title, iconX + 14, iconY, type.color, true);
        
        // 3. Separador sutil
        context.fill(x + 10, y + 28, x + width - 10, y + 29, 0x44FFFFFF);
        
        // 4. Descripción Centrada
        int descWidth = renderer.getWidth(desc);
        LabelWidget.draw(context, renderer, "§7" + desc, x + (width / 2) - (descWidth / 2), y + 36, 0xCCCCCC, false);
        
        // 5. Glow inferior animado (Efecto línea de progreso de tiempo)
        context.fill(x, y + height - 2, x + width, y + height, type.color);
    }
}
