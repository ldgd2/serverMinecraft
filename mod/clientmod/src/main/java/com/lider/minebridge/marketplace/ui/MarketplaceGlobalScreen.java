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
    private boolean buttonsAdded = false;
    private static final int PANEL_WIDTH = 320;
    private static final int PANEL_HEIGHT = 220;
    private static final int MAX_ROWS = 7;
    private static final int ROW_HEIGHT = 24;

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

        // Botón de regreso siempre presente
        this.addDrawableChild(ButtonWidget.builder(Text.of("§7← Volver"), button -> {
            MinecraftClient.getInstance().setScreen(new com.lider.minebridge.client.ui.MainLauncherScreen());
        }).dimensions(centerX - 40, centerY + 98, 80, 18).build());

        // Botón de actualizar
        this.addDrawableChild(ButtonWidget.builder(Text.of("§e↺"), button -> {
            this.loading = true;
            this.buttonsAdded = false;
            this.clearChildren();
            this.init();
        }).dimensions(centerX + 145, centerY + 98, 18, 18).build());

        if (!loading) {
            addTradeButtons();
        } else {
            TradeClient.getOpenTrades().thenAccept(data -> {
                this.trades = data;
                this.loading = false;
                // Re-añadir botones en el hilo de render
                MinecraftClient.getInstance().execute(() -> {
                    clearChildren();
                    init();
                });
            }).exceptionally(ex -> {
                this.loading = false;
                return null;
            });
        }
    }

    private void addTradeButtons() {
        if (buttonsAdded || trades == null) return;
        buttonsAdded = true;
        int centerX = this.width / 2;
        int centerY = this.height / 2;
        int x1 = centerX - (PANEL_WIDTH / 2);
        int y1 = centerY - (PANEL_HEIGHT / 2);

        int count = Math.min(trades.size(), MAX_ROWS);
        for (int i = 0; i < count; i++) {
            final JsonObject trade = trades.get(i).getAsJsonObject();
            int rowY = y1 + 35 + (i * ROW_HEIGHT);

            this.addDrawableChild(ButtonWidget.builder(Text.of("§a▶"), button -> {
                MinecraftClient.getInstance().setScreen(new MarketplaceDetailScreen(trade));
            }).dimensions(x1 + PANEL_WIDTH - 52, rowY + 3, 36, 16).build());
        }
    }

    @Override
    public void renderBackground(DrawContext context, int mouseX, int mouseY, float delta) {
        com.lider.minebridge.ui.framework.UIBackgrounds.renderDark(context, this.width, this.height);
    }

    @Override
    public void render(DrawContext context, int mouseX, int mouseY, float delta) {
        super.render(context, mouseX, mouseY, delta);
        int centerX = this.width / 2;
        int centerY = this.height / 2;
        int x1 = centerX - (PANEL_WIDTH / 2);
        int y1 = centerY - (PANEL_HEIGHT / 2);
        int x2 = centerX + (PANEL_WIDTH / 2);
        int y2 = centerY + (PANEL_HEIGHT / 2);

        // Panel premium central
        com.lider.minebridge.ui.framework.UIBackgrounds.drawPanel(context, x1, y1, PANEL_WIDTH, PANEL_HEIGHT);
        
        // Cabecera
        context.fill(x1 + 1, y1 + 1, x2 - 1, y1 + 25, 0xFF2A2A2A);
        context.drawCenteredTextWithShadow(this.textRenderer, this.title, centerX, y1 + 8, 0xFFFFFF);

        if (loading) {
            context.drawCenteredTextWithShadow(this.textRenderer, "§eCargando ofertas...", centerX, centerY, 0xFFFFFF);
        } else if (trades == null || trades.size() == 0) {
            context.drawCenteredTextWithShadow(this.textRenderer, "§7No hay ofertas activas en este momento.", centerX, centerY, 0xAAAAAA);
        } else {
            int count = Math.min(trades.size(), MAX_ROWS);
            for (int i = 0; i < count; i++) {
                JsonObject trade = trades.get(i).getAsJsonObject();
                String title = trade.has("title") ? trade.get("title").getAsString() : "Sin título";
                String seller = trade.has("seller") ? trade.get("seller").getAsString() : "?";

                int rowY = y1 + 35 + (i * ROW_HEIGHT);
                // Filas con efecto inset/hundido
                com.lider.minebridge.ui.framework.UIBackgrounds.drawInset(context, x1 + 8, rowY, PANEL_WIDTH - 16, 22);
                context.drawText(this.textRenderer, "§6" + title, x1 + 14, rowY + 7, 0xFFFFFF, false);
                context.drawText(this.textRenderer, "§7" + seller, x1 + 140, rowY + 7, 0xAAAAAA, false);
            }
            if (trades.size() > MAX_ROWS) {
                context.drawCenteredTextWithShadow(this.textRenderer,
                    "§8... y " + (trades.size() - MAX_ROWS) + " más", centerX, y2 - 14, 0x888888);
            }
        }

        super.render(context, mouseX, mouseY, delta);
    }

    @Override
    public boolean shouldPause() { return false; }
}
