package com.lider.minebridge.system.ui.views;

import com.lider.minebridge.ui.framework.core.UIConstants;
import com.lider.minebridge.ui.framework.widgets.*;
import com.lider.minebridge.ui.framework.components.*;
import net.minecraft.client.gui.DrawContext;
import net.minecraft.client.gui.screen.Screen;
import net.minecraft.text.Text;

/**
 * Vista de Sistema: Advertencia de Reinicio del Servidor.
 * Utiliza componentes modulares para avisos urgentes.
 */
public class ServerRestartScreen extends Screen {
    private final int secondsLeft;

    public ServerRestartScreen(int secondsLeft) {
        super(Text.of("§c§lAVISO DE SISTEMA"));
        this.secondsLeft = secondsLeft;
    }

    @Override
    public void renderBackground(DrawContext context, int mouseX, int mouseY, float delta) {
        com.lider.minebridge.ui.framework.UIBackgrounds.renderWarning(context, this.width, this.height);
    }

    @Override
    public void render(DrawContext context, int mouseX, int mouseY, float delta) {
        super.render(context, mouseX, mouseY, delta);        
        int centerX = this.width / 2;
        int centerY = this.height / 2;
        int panelW = 200;
        
        // 1. Alerta Central
        AlertComponent.draw(context, this.textRenderer, 
            AlertComponent.AlertType.RESTART, 
            "El servidor se reiniciará en " + secondsLeft + "s",
            "Guarda tus pertenencias inmediatamente",
            centerX - (panelW / 2), centerY - 40, panelW);
        
        // 2. Barra de Progreso (Modular)
        float progress = Math.max(0, Math.min(1.0f, secondsLeft / 60.0f)); // Asumiendo aviso de 1min
        ProgressBarWidget.draw(context, centerX - 80, centerY + 20, 160, 10, progress, 0xFFFF5555);

        super.render(context, mouseX, mouseY, delta);
    }
    
    @Override
    public boolean shouldPause() { return false; }
    @Override
    public boolean shouldCloseOnEsc() { return false; }
}
