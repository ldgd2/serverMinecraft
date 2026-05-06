package com.lider.minebridge.client.ui;

import com.google.gson.JsonArray;
import com.google.gson.JsonObject;
import com.lider.minebridge.networking.TradeClient;
import net.minecraft.client.MinecraftClient;
import net.minecraft.client.gui.DrawContext;
import net.minecraft.client.gui.screen.Screen;
import net.minecraft.client.gui.widget.ButtonWidget;
import net.minecraft.item.ItemStack;
import net.minecraft.registry.Registries;
import net.minecraft.text.Text;
import net.minecraft.util.Identifier;

import java.util.ArrayList;
import java.util.List;

public class MarketplaceGlobalScreen extends Screen {
    private final JsonArray trades;
    private int scrollOffset = 0;

    public MarketplaceGlobalScreen(JsonArray trades) {
        super(Text.of("§6§lMarketplace Global"));
        this.trades = trades;
    }

    @Override
    protected void init() {
        super.init();
        int y = 40;
        for (int i = 0; i < trades.size(); i++) {
            JsonObject trade = trades.get(i).getAsJsonObject();
            int tradeId = trade.get("id").getAsInt();
            String title = trade.get("title").getAsString();
            String seller = trade.get("seller").getAsString();
            String sellerUuid = trade.get("seller_uuid").getAsString();
            boolean isSelf = sellerUuid.equals(MinecraftClient.getInstance().player.getUuidAsString());

            // Botón para Comprar / Borrar
            Text buttonText = isSelf ? Text.of("§cELIMINAR") : Text.of("§aCOMPRAR");
            this.addDrawableChild(ButtonWidget.builder(buttonText, button -> {
                if (isSelf) {
                    TradeClient.resolveOffer(tradeId, "cancel", null);
                } else {
                    TradeClient.completeTrade(tradeId, MinecraftClient.getInstance().player.getUuidAsString(), MinecraftClient.getInstance().player.getName().getString());
                }
                this.close();
            }).dimensions(this.width / 2 + 60, y, 70, 20).build());

            y += 25;
        }

        // Botón Cerrar
        this.addDrawableChild(ButtonWidget.builder(Text.of("Cerrar"), b -> this.close())
            .dimensions(this.width / 2 - 50, this.height - 30, 100, 20).build());
    }

    @Override
    public void render(DrawContext context, int mouseX, int mouseY, float delta) {
        this.renderBackground(context, mouseX, mouseY, delta);
        context.drawCenteredTextWithShadow(this.textRenderer, this.title, this.width / 2, 15, 0xFFFFFF);

        int y = 40;
        for (int i = 0; i < trades.size(); i++) {
            JsonObject trade = trades.get(i).getAsJsonObject();
            String title = trade.get("title").getAsString();
            String seller = trade.get("seller").getAsString();
            
            JsonObject selling = trade.getAsJsonObject("selling");
            JsonObject asking = trade.getAsJsonObject("asking");

            // Dibujar información
            context.drawTextWithShadow(this.textRenderer, "§e" + title + " §7(por " + seller + ")", this.width / 2 - 180, y + 5, 0xFFFFFF);
            
            // Iconos (aproximado)
            drawItemIcon(context, selling, this.width / 2 - 20, y);
            context.drawTextWithShadow(this.textRenderer, "➔", this.width / 2 + 5, y + 5, 0xFFFFFF);
            drawItemIcon(context, asking, this.width / 2 + 25, y);

            y += 25;
        }

        super.render(context, mouseX, mouseY, delta);
    }

    private void drawItemIcon(DrawContext context, JsonObject itemJson, int x, int y) {
        try {
            String id = itemJson.get("id").getAsString();
            int count = itemJson.get("count").getAsInt();
            ItemStack stack = new ItemStack(Registries.ITEM.get(Identifier.of(id)), count);
            context.drawItem(stack, x, y);
            context.drawItemInGuiWithOverrides(this.textRenderer, stack, x, y);
        } catch (Exception e) {}
    }
}
