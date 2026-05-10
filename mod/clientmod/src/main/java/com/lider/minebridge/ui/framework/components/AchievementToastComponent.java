package com.lider.minebridge.ui.framework.components;

import com.lider.minebridge.ui.framework.core.UIConstants;
import com.lider.minebridge.ui.framework.widgets.IconWidget;
import com.lider.minebridge.ui.framework.widgets.LabelWidget;
import net.minecraft.client.font.TextRenderer;
import net.minecraft.client.gui.DrawContext;

/**
 * Componente: Notificación de Logro Desbloqueado (Premium).
 */
public class AchievementToastComponent {
    
    public static void draw(DrawContext context, TextRenderer renderer, String title, int x, int y) {
        int width = 160;
        int height = 32;
        
        // 1. Fondo del Panel (Estilo Oscuro Premium)
        context.fill(x, y, x + width, y + height, 0xEE1A1A1A);
        
        // Bordes Dorados
        context.fill(x, y, x + width, y + 1, 0xFFFFAA00);
        context.fill(x, y + height - 1, x + width, y + height, 0xFFFFAA00);
        context.fill(x, y, x + 1, y + height, 0xFFFFAA00);
        context.fill(x + width - 1, y, x + width, y + height, 0xFFFFAA00);
        
        // 2. Icono de Trofeo
        context.drawText(renderer, "🏆", x + 8, y + 10, 0xFFFFFF, true);
        
        // 3. Textos
        LabelWidget.draw(context, renderer, "§6§l¡LOGRO OBTENIDO!", x + 24, y + 6, 0xFFFFFF, false);
        LabelWidget.draw(context, renderer, "§f" + title, x + 24, y + 17, 0xFFFFFF, false);
        
        // Brillo decorativo lateral
        context.fill(x + 1, y + 1, x + 3, y + height - 1, 0xFFFFFF00);
    }
}
