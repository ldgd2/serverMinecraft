package com.lider.minebridge.marketplace.ui;

import com.lider.minebridge.marketplace.networking.TradeClient;
import com.lider.minebridge.marketplace.networking.OpenCreationMenuPayload;
import net.fabricmc.fabric.api.client.networking.v1.ClientPlayNetworking;
import net.minecraft.client.MinecraftClient;
import net.minecraft.client.gui.DrawContext;
import net.minecraft.client.gui.screen.Screen;
import net.minecraft.client.gui.widget.ButtonWidget;
import net.minecraft.text.Text;

/**
 * Vista de Perfil: Gestiona las acciones rápidas del usuario.
 */
public class MarketplaceProfileScreen extends Screen {
    private static final int PANEL_WIDTH = 220;
    private static final int PANEL_HEIGHT = 180;

    public MarketplaceProfileScreen() {
        super(Text.of("§d§lPERFIL DE VENDEDOR"));
    }

    @Override
    protected void init() {
        super.init();
        int centerX = this.width / 2;
        int centerY = this.height / 2;

        this.addDrawableChild(ButtonWidget.builder(Text.of("§a✚  Crear Nueva Publicación"), button -> {
            if (ClientPlayNetworking.canSend(OpenCreationMenuPayload.ID)) {
                ClientPlayNetworking.send(new OpenCreationMenuPayload());
            }
            this.close();
        }).dimensions(centerX - 90, centerY - 40, 180, 20).build());

        this.addDrawableChild(ButtonWidget.builder(Text.of("§b📋  Mis Publicaciones Activas"), button -> {
            TradeClient.getOpenTrades().thenAccept(trades -> {
                MinecraftClient.getInstance().execute(() -> {
                    MinecraftClient.getInstance().setScreen(new MarketplaceGlobalScreen(trades));
                });
            });
        }).dimensions(centerX - 90, centerY - 10, 180, 20).build());

        this.addDrawableChild(ButtonWidget.builder(Text.of("§6⚖  Ver Mercado Global"), button -> {
            TradeClient.getOpenTrades().thenAccept(trades -> {
                MinecraftClient.getInstance().execute(() -> {
                    MinecraftClient.getInstance().setScreen(new MarketplaceGlobalScreen(trades));
                });
            });
        }).dimensions(centerX - 90, centerY + 20, 180, 20).build());

        this.addDrawableChild(ButtonWidget.builder(Text.of("§cCerrar Panel"), b -> this.close())
            .dimensions(centerX - 40, centerY + 55, 80, 20).build());
    }

    @Override
    public void render(DrawContext context, int mouseX, int mouseY, float delta) {
        context.fill(0, 0, this.width, this.height, 0xFF000000); 
        int centerX = this.width / 2;
        int centerY = this.height / 2;
        int x1 = centerX - (PANEL_WIDTH / 2);
        int y1 = centerY - (PANEL_HEIGHT / 2);
        int x2 = centerX + (PANEL_WIDTH / 2);
        int y2 = centerY + (PANEL_HEIGHT / 2);

        context.fill(x1 - 2, y1 - 2, x2 + 2, y2 + 2, 0xFF550055); 
        context.fill(x1, y1, x2, y2, 0xFF151515);
        context.fill(x1, y1, x2, y1 + 25, 0xFF330033);
        context.drawCenteredTextWithShadow(this.textRenderer, this.title, centerX, y1 + 8, 0xFFFFFF);
        
        super.render(context, mouseX, mouseY, delta);
    }
}
