package com.lider.minebridge.client.ui;

import com.lider.minebridge.marketplace.ui.MarketplaceGlobalScreen;
import com.lider.minebridge.marketplace.ui.MarketplaceProfileScreen;
import com.lider.minebridge.marketplace.networking.TradeClient;
import com.lider.minebridge.achievements.ui.AchievementListScreen;
import com.lider.minebridge.networking.AchievementClient;
import net.minecraft.client.MinecraftClient;
import net.minecraft.client.gui.DrawContext;
import net.minecraft.client.gui.screen.Screen;
import net.minecraft.client.gui.widget.ButtonWidget;
import net.minecraft.text.Text;

/**
 * Lanzador Central de MineBridge: El punto de entrada a todas las interfaces.
 */
public class MainLauncherScreen extends Screen {
    private static final int PANEL_WIDTH = 260;
    private static final int PANEL_HEIGHT = 160;

    public MainLauncherScreen() {
        super(Text.of("§6§lMINEBRIDGE LAUNCHER"));
    }

    @Override
    protected void init() {
        super.init();
        int centerX = this.width / 2;
        int centerY = this.height / 2;

        // Botón 1: Mercado Global
        this.addDrawableChild(ButtonWidget.builder(Text.of("§6⚖ Mercado Global"), button -> {
            MinecraftClient.getInstance().setScreen(new MarketplaceGlobalScreen());
        }).dimensions(centerX - 100, centerY - 40, 200, 20).build());

        // Botón 2: Mi Perfil
        this.addDrawableChild(ButtonWidget.builder(Text.of("§d👤 Mi Perfil de Vendedor"), button -> {
            MinecraftClient.getInstance().setScreen(new MarketplaceProfileScreen());
        }).dimensions(centerX - 100, centerY - 10, 200, 20).build());

        // Botón 3: Logros
        this.addDrawableChild(ButtonWidget.builder(Text.of("§e🏆 Ver Mis Logros"), button -> {
            MinecraftClient.getInstance().setScreen(new AchievementListScreen());
        }).dimensions(centerX - 100, centerY + 20, 200, 20).build());

        // Botón Cerrar
        this.addDrawableChild(ButtonWidget.builder(Text.of("§cCerrar"), b -> this.close())
            .dimensions(centerX - 40, centerY + 50, 80, 20).build());
    }

    @Override
    public void render(DrawContext context, int mouseX, int mouseY, float delta) {
        // Fondo semi-transparente oscuro global
        com.lider.minebridge.ui.framework.UIBackgrounds.renderDark(context, this.width, this.height);

        int centerX = this.width / 2;
        int centerY = this.height / 2;
        int x1 = centerX - (PANEL_WIDTH / 2);
        int y1 = centerY - (PANEL_HEIGHT / 2);

        // Panel central premium
        com.lider.minebridge.ui.framework.UIBackgrounds.drawPanel(context, x1, y1, PANEL_WIDTH, PANEL_HEIGHT);
        
        // Cabecera del panel
        context.fill(x1 + 1, y1 + 1, x1 + PANEL_WIDTH - 1, y1 + 25, 0xFF2A2A2A);
        context.drawCenteredTextWithShadow(this.textRenderer, this.title, centerX, y1 + 8, 0xFFFFFF);

        super.render(context, mouseX, mouseY, delta);
    }
    
    @Override
    public boolean shouldPause() { return false; }
}
