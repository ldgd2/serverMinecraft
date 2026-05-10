package com.lider.minebridge.marketplace.ui;

import com.google.gson.JsonArray;
import com.google.gson.JsonObject;
import com.lider.minebridge.marketplace.networking.TradeClient;
import net.minecraft.client.MinecraftClient;
import net.minecraft.client.gui.DrawContext;
import net.minecraft.client.gui.screen.Screen;
import net.minecraft.client.gui.widget.ButtonWidget;
import net.minecraft.text.Text;

public class MarketplaceGlobalScreen extends Screen {
    private JsonArray trades = new JsonArray();
    private boolean loading = true;
    private static final int PANEL_WIDTH = 320;
    private static final int PANEL_HEIGHT = 220;

    public MarketplaceGlobalScreen() {
        super(Text.of("§6§lMERCADO GLOBAL"));
    }

    public MarketplaceGlobalScreen(JsonArray trades) {
        super(Text.of("§6§lMERCADO GLOBAL"));
        this.trades = trades;
        this.loading = false;
    }

    @Override
    protected void init() {
        super.init();
        int centerX = this.width / 2;
        int centerY = this.height / 2;

        if (loading) {
            TradeClient.getOpenTrades().thenAccept(data -> {
                this.trades = data;
                this.loading = false;
            }).exceptionally(ex -> {
                this.loading = false;
                return null;
            });
        }

        this.addDrawableChild(ButtonWidget.builder(Text.of("§7Regresar"), button -> {
            MinecraftClient.getInstance().setScreen(new com.lider.minebridge.client.ui.MainLauncherScreen());
        }).dimensions(centerX - 40, centerY + 95, 80, 20).build());
    }

    @Override
    public void render(DrawContext context, int mouseX, int mouseY, float delta) {
        // Fondo semi-transparente oscuro (Sólido, sin blur)
        context.fill(0, 0, this.width, this.height, 0x99000000);
        
        int centerX = this.width / 2;
        int centerY = this.height / 2;
        int x1 = centerX - (PANEL_WIDTH / 2);
        int y1 = centerY - (PANEL_HEIGHT / 2);
        int x2 = centerX + (PANEL_WIDTH / 2);
        int y2 = centerY + (PANEL_HEIGHT / 2);

        // Fondo y Borde Dorado
        context.fill(x1 - 2, y1 - 2, x2 + 2, y2 + 2, 0xFFFFD700); 
        context.fill(x1, y1, x2, y2, 0xFF121212);
        // Cabecera
        context.fill(x1, y1, x2, y1 + 25, 0xFF2A2A2A);
        context.drawCenteredTextWithShadow(this.textRenderer, this.title, centerX, y1 + 8, 0xFFFFFF);

        if (loading) {
            context.drawCenteredTextWithShadow(this.textRenderer, "§eCargando ofertas...", centerX, centerY, 0xFFFFFF);
        } else if (trades == null || trades.size() == 0) {
            context.drawCenteredTextWithShadow(this.textRenderer, "§7No hay ofertas activas en este momento.", centerX, centerY, 0xAAAAAA);
        } else {
            for (int i = 0; i < Math.min(trades.size(), 7); i++) {
                JsonObject trade = trades.get(i).getAsJsonObject();
                String title = trade.get("title").getAsString();
                String seller = trade.get("seller").getAsString();
                int tradeId = trade.get("id").getAsInt();

                int rowY = y1 + 35 + (i * 24);
                context.fill(x1 + 8, rowY, x2 - 8, rowY + 22, 0xFF1E1E1E);
                context.drawText(this.textRenderer, "§6" + title, x1 + 15, rowY + 7, 0xFFFFFF, false);
                context.drawText(this.textRenderer, "§7por " + seller, x1 + 140, rowY + 7, 0xAAAAAA, false);
                
                // Botón Ver (Simulado con texto por ahora o añadir widget real en init)
                context.drawText(this.textRenderer, "§a[VER]", x2 - 45, rowY + 7, 0x55FF55, false);
            }
        }

        super.render(context, mouseX, mouseY, delta);
    }

    @Override
    public boolean shouldPause() { return false; }
}
