package com.lider.minebridge.client.ui;

import com.lider.minebridge.networking.TradeClient;
import net.fabricmc.fabric.api.client.networking.v1.ClientPlayNetworking;
import net.minecraft.client.MinecraftClient;
import net.minecraft.client.gui.DrawContext;
import net.minecraft.client.gui.screen.Screen;
import net.minecraft.client.gui.widget.ButtonWidget;
import net.minecraft.text.Text;

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

        // Botones con estilo y espaciado
        this.addDrawableChild(ButtonWidget.builder(Text.of("§a✚  Crear Nueva Publicación"), button -> {
            if (ClientPlayNetworking.canSend(com.lider.minebridge.networking.payload.OpenCreationMenuPayload.ID)) {
                ClientPlayNetworking.send(new com.lider.minebridge.networking.payload.OpenCreationMenuPayload());
            }
            this.close();
        }).dimensions(centerX - 90, centerY - 40, 180, 20).build());

        this.addDrawableChild(ButtonWidget.builder(Text.of("§b📋  Mis Publicaciones Activas"), button -> {
            TradeClient.getOpenTrades().thenAccept(trades -> {
                MinecraftClient.getInstance().execute(() -> {
                    MinecraftClient.getInstance().setScreen(new MarketplaceGlobalScreen(trades, true));
                });
            });
        }).dimensions(centerX - 90, centerY - 10, 180, 20).build());

        this.addDrawableChild(ButtonWidget.builder(Text.of("§6⚖  Ver Mercado Global"), button -> {
            TradeClient.getOpenTrades().thenAccept(trades -> {
                MinecraftClient.getInstance().execute(() -> {
                    MinecraftClient.getInstance().setScreen(new MarketplaceGlobalScreen(trades, false));
                });
            });
        }).dimensions(centerX - 90, centerY + 20, 180, 20).build());

        this.addDrawableChild(ButtonWidget.builder(Text.of("§cCerrar Panel"), b -> this.close())
            .dimensions(centerX - 40, centerY + 55, 80, 20).build());

        // Botón X para cerrar
        this.addDrawableChild(ButtonWidget.builder(Text.of("§cX"), b -> this.close())
            .dimensions(centerX + (PANEL_WIDTH / 2) - 20, centerY - (PANEL_HEIGHT / 2) + 2, 18, 18).build());
    }

    @Override
    public void render(DrawContext context, int mouseX, int mouseY, float delta) {
        // Fondo sólido negro TOTAL para bloquear cualquier shader del mundo
        context.fill(0, 0, this.width, this.height, 0xFF000000); 

        int centerX = this.width / 2;
        int centerY = this.height / 2;

        // Subir a la capa de GUI
        context.getMatrices().push();
        context.getMatrices().translate(0, 0, 100);

        // Dibujar el Panel Central (Efecto Glassmorphism/Sólido)
        int x1 = centerX - (PANEL_WIDTH / 2);
        int y1 = centerY - (PANEL_HEIGHT / 2);
        int x2 = centerX + (PANEL_WIDTH / 2);
        int y2 = centerY + (PANEL_HEIGHT / 2);

        // Borde dorado/púrpura
        context.fill(x1 - 2, y1 - 2, x2 + 2, y2 + 2, 0xFF550055); 
        context.fill(x1, y1, x2, y2, 0xFF151515); // Fondo del panel

        // Encabezado
        context.fill(x1, y1, x2, y1 + 25, 0xFF330033);
        context.drawCenteredTextWithShadow(this.textRenderer, this.title, centerX, y1 + 8, 0xFFFFFF);
        
        String name = MinecraftClient.getInstance().player.getName().getString();
        context.drawCenteredTextWithShadow(this.textRenderer, "§7Comerciante: §e" + name, centerX, y1 + 32, 0xFFFFFF);

        super.render(context, mouseX, mouseY, delta);
        context.getMatrices().pop();
    }
    
    @Override
    public boolean shouldPause() {
        return false;
    }

    @Override
    public void renderBackground(DrawContext context, int mouseX, int mouseY, float delta) {
        // No llamar a super para evitar el desenfoque del mundo
    }
}
