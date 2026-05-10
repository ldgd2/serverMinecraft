package com.lider.minebridge.marketplace.ui;

import com.google.gson.JsonObject;
import com.lider.minebridge.ui.framework.core.UIConstants;
import com.lider.minebridge.ui.framework.widgets.*;
import com.lider.minebridge.ui.framework.components.*;
import com.lider.minebridge.marketplace.networking.TradeClient;
import net.minecraft.client.MinecraftClient;
import net.minecraft.client.gui.DrawContext;
import net.minecraft.client.gui.screen.Screen;
import net.minecraft.client.gui.widget.ButtonWidget;
import net.minecraft.item.ItemStack;
import net.minecraft.registry.Registries;
import net.minecraft.text.Text;
import net.minecraft.util.Identifier;
import net.fabricmc.fabric.api.client.networking.v1.ClientPlayNetworking;

/**
 * Vista: Detalle del Trato.
 */
public class MarketplaceDetailScreen extends Screen {
    private final JsonObject trade;
    private final int tradeId;
    private final ItemStack sellingStack;
    private final ItemStack askingStack1;
    private final ItemStack askingStack2;

    public MarketplaceDetailScreen(JsonObject trade) {
        super(Text.of("§6§lDetalle del Trato"));
        this.trade = trade;
        this.tradeId = trade.get("id").getAsInt();
        this.sellingStack = parseJsonItem(trade.getAsJsonObject("selling"));

        com.google.gson.JsonElement askingElement = trade.get("asking");
        if (askingElement.isJsonArray()) {
            com.google.gson.JsonArray array = askingElement.getAsJsonArray();
            this.askingStack1 = array.size() > 0 ? parseJsonItem(array.get(0).getAsJsonObject()) : ItemStack.EMPTY;
            this.askingStack2 = array.size() > 1 ? parseJsonItem(array.get(1).getAsJsonObject()) : ItemStack.EMPTY;
        } else {
            this.askingStack1 = parseJsonItem(askingElement.getAsJsonObject());
            this.askingStack2 = ItemStack.EMPTY;
        }
    }

    @Override
    protected void init() {
        int centerX = this.width / 2;
        int centerY = this.height / 2;
        String myUuid = MinecraftClient.getInstance().player.getUuidAsString();
        String sellerUuid = trade.has("seller_uuid") ? trade.get("seller_uuid").getAsString() : "unknown";

        if (sellerUuid.equals(myUuid)) {
            this.addDrawableChild(ButtonWidget.builder(Text.of("§cELIMINAR PUBLICACIÓN"), button -> {
                ClientPlayNetworking.send(new com.lider.minebridge.marketplace.networking.CancelTradePayload(tradeId));
                this.close();
            }).dimensions(centerX - 80, centerY + 35, 160, 20).build());
        } else {
            this.addDrawableChild(ButtonWidget.builder(Text.of("§a§lINICIAR TRUEQUE"), button -> {
                ClientPlayNetworking.send(new com.lider.minebridge.marketplace.networking.OpenTransactionMenuPayload(tradeId));
                this.close();
            }).dimensions(centerX - 80, centerY + 35, 160, 20).build());
        }

        this.addDrawableChild(ButtonWidget.builder(Text.of("Volver"), button -> {
            TradeClient.getOpenTrades().thenAccept(trades -> {
                MinecraftClient.getInstance().execute(() -> MinecraftClient.getInstance().setScreen(new MarketplaceGlobalScreen(trades)));
            });
        }).dimensions(centerX - 50, centerY + 70, 100, 20).build());
    }

    @Override
    public void render(DrawContext context, int mouseX, int mouseY, float delta) {
        context.fill(0, 0, this.width, this.height, 0xAA000000);

        int centerX = this.width / 2;
        int centerY = this.height / 2;
        int w = 240;
        int h = 160;
        int x1 = centerX - w / 2;
        int y1 = centerY - h / 2;

        PanelComponent.draw(context, x1, y1, w, h);
        context.fill(x1, y1, x1 + w, y1 + 25, 0xFF252525);
        LabelWidget.drawCentered(context, this.textRenderer, this.title, centerX, y1 + 8, 0xFFFFFF);

        String titleStr = trade.has("title") ? trade.get("title").getAsString() : "Sin título";
        String seller = trade.has("seller") ? trade.get("seller").getAsString() : "Anónimo";

        LabelWidget.drawCentered(context, this.textRenderer, Text.of("§e" + titleStr), centerX, y1 + 35, 0xFFFFFF);
        LabelWidget.drawCentered(context, this.textRenderer, Text.of("§7Vendedor: §f" + seller), centerX, y1 + 45, 0xFFFFFF);

        // Visualización de Ítems
        LabelWidget.drawCentered(context, this.textRenderer, Text.of("§cEntregas"), centerX - 60, y1 + 65, 0xFFFFFF);
        if (!askingStack1.isEmpty()) context.drawItem(askingStack1, centerX - 80, y1 + 75);
        if (!askingStack2.isEmpty()) context.drawItem(askingStack2, centerX - 45, y1 + 75);

        IconWidget.drawArrow(context, centerX - 5, y1 + 80, 0xFFFFFF);

        LabelWidget.drawCentered(context, this.textRenderer, Text.of("§bRecibes"), centerX + 60, y1 + 65, 0xFFFFFF);
        context.drawItem(sellingStack, centerX + 50, y1 + 75);

        super.render(context, mouseX, mouseY, delta);
    }

    private ItemStack parseJsonItem(JsonObject json) {
        if (json == null) return ItemStack.EMPTY;
        return new ItemStack(Registries.ITEM.get(Identifier.of(json.get("id").getAsString())), json.get("count").getAsInt());
    }
}
