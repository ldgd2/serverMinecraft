package com.lider.minebridge.client.ui;

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
import net.fabricmc.fabric.api.client.networking.v1.ClientPlayNetworking;
import com.lider.minebridge.networking.payload.OpenTransactionMenuPayload;

public class MarketplaceDetailScreen extends Screen {
    private final JsonObject trade;
    private final int tradeId;
    private final ItemStack sellingStack;
    private final ItemStack askingStack1;
    private final ItemStack askingStack2;
    
    private static final int PANEL_WIDTH = 240;
    private static final int PANEL_HEIGHT = 160;

    public MarketplaceDetailScreen(JsonObject trade) {
        super(Text.of("§6§lDetalle del Trato"));
        this.trade = trade;
        this.tradeId = trade.get("id").getAsInt();
        
        JsonObject sellingJson = trade.getAsJsonObject("selling");
        this.sellingStack = parseJsonItem(sellingJson);

        com.google.gson.JsonElement askingElement = trade.get("asking");
        ItemStack a1 = ItemStack.EMPTY;
        ItemStack a2 = ItemStack.EMPTY;

        if (askingElement.isJsonArray()) {
            com.google.gson.JsonArray array = askingElement.getAsJsonArray();
            if (array.size() > 0) a1 = parseJsonItem(array.get(0).getAsJsonObject());
            if (array.size() > 1) a2 = parseJsonItem(array.get(1).getAsJsonObject());
        } else {
            a1 = parseJsonItem(askingElement.getAsJsonObject());
        }
        
        this.askingStack1 = a1;
        this.askingStack2 = a2;
    }

    @Override
    protected void init() {
        super.init();
        int centerX = this.width / 2;
        int centerY = this.height / 2;

        String myUuid = MinecraftClient.getInstance().player.getUuidAsString();
        String sellerUuid = trade.has("seller_uuid") ? trade.get("seller_uuid").getAsString() : "unknown";
        boolean isSelf = sellerUuid.equals(myUuid);

        if (isSelf) {
            this.addDrawableChild(ButtonWidget.builder(Text.of("§cELIMINAR PUBLICACIÓN"), button -> {
                TradeClient.cancelTrade(tradeId);
                this.close();
            }).dimensions(centerX - 80, centerY + 35, 160, 20).build());
        } else {
            this.addDrawableChild(ButtonWidget.builder(Text.of("§a§lINICIAR TRUEQUE"), button -> {
                if (ClientPlayNetworking.canSend(OpenTransactionMenuPayload.ID)) {
                    ClientPlayNetworking.send(new OpenTransactionMenuPayload(tradeId));
                }
                this.close();
            }).dimensions(centerX - 80, centerY + 35, 160, 20).build());
        }

        this.addDrawableChild(ButtonWidget.builder(Text.of("Volver"), button -> {
            TradeClient.getOpenTrades().thenAccept(trades -> {
                MinecraftClient.getInstance().execute(() -> {
                    MinecraftClient.getInstance().setScreen(new MarketplaceGlobalScreen(trades));
                });
            });
        }).dimensions(centerX - 50, centerY + 70, 100, 20).build());

        // Botón X para cerrar
        this.addDrawableChild(ButtonWidget.builder(Text.of("§cX"), b -> this.close())
            .dimensions(centerX + (PANEL_WIDTH / 2) - 20, centerY - (PANEL_HEIGHT / 2) + 2, 18, 18).build());
    }

    @Override
    public void render(DrawContext context, int mouseX, int mouseY, float delta) {
        context.fill(0, 0, this.width, this.height, 0xFF000000); // Fondo sólido negro

        int centerX = this.width / 2;
        int centerY = this.height / 2;
        int x1 = centerX - (PANEL_WIDTH / 2);
        int y1 = centerY - (PANEL_HEIGHT / 2);
        int x2 = centerX + (PANEL_WIDTH / 2);
        int y2 = centerY + (PANEL_HEIGHT / 2);

        // Subir a la capa GUI
        context.getMatrices().push();
        context.getMatrices().translate(0, 0, 100);

        // Panel
        context.fill(x1 - 1, y1 - 1, x2 + 1, y2 + 1, 0xFF555555);
        context.fill(x1, y1, x2, y2, 0xFF121212);
        
        context.fill(x1, y1, x2, y1 + 25, 0xFF252525);
        context.drawCenteredTextWithShadow(this.textRenderer, this.title, centerX, y1 + 8, 0xFFFFFF);

        String title = trade.has("title") ? trade.get("title").getAsString() : "Sin título";
        String seller = trade.has("seller") ? trade.get("seller").getAsString() : "Anónimo";

        context.drawCenteredTextWithShadow(this.textRenderer, "§e" + title, centerX, y1 + 35, 0xFFFFFF);
        context.drawCenteredTextWithShadow(this.textRenderer, "§7Vendedor: §f" + seller, centerX, y1 + 45, 0xFFFFFF);

        // Ítems (Flow: Entregas -> Recibes)
        context.drawCenteredTextWithShadow(this.textRenderer, "§cEntregas", centerX - 60, y1 + 65, 0xFFFFFF);
        
        // Entrega 1
        if (!askingStack1.isEmpty()) {
            context.drawItem(askingStack1, centerX - 80, y1 + 75);
            context.drawTextWithShadow(this.textRenderer, "x" + askingStack1.getCount(), centerX - 60, y1 + 85, 0xFFFFFF);
        }
        
        // Entrega 2
        if (!askingStack2.isEmpty()) {
            context.drawItem(askingStack2, centerX - 45, y1 + 75);
            context.drawTextWithShadow(this.textRenderer, "x" + askingStack2.getCount(), centerX - 25, y1 + 85, 0xFFFFFF);
        }

        context.drawCenteredTextWithShadow(this.textRenderer, "➔", centerX + 5, y1 + 80, 0xFFFFFF);

        context.drawCenteredTextWithShadow(this.textRenderer, "§bRecibes", centerX + 60, y1 + 65, 0xFFFFFF);
        context.drawItem(sellingStack, centerX + 50, y1 + 75);
        context.drawTextWithShadow(this.textRenderer, "x" + sellingStack.getCount(), centerX + 70, y1 + 85, 0xFFFFFF);

        super.render(context, mouseX, mouseY, delta);
        context.getMatrices().pop();
    }

    private ItemStack parseJsonItem(JsonObject json) {
        if (json == null) return ItemStack.EMPTY;
        return new ItemStack(Registries.ITEM.get(Identifier.of(json.get("id").getAsString())), json.get("count").getAsInt());
    }

    @Override
    public void renderBackground(DrawContext context, int mouseX, int mouseY, float delta) {
        // Nada de borroso
    }
}
