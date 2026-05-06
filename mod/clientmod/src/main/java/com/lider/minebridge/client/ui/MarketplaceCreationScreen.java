package com.lider.minebridge.client.ui;

import com.google.gson.JsonObject;
import com.lider.minebridge.marketplace.MarketplaceCreationScreenHandler;
import com.lider.minebridge.networking.TradeClient;
import net.minecraft.client.MinecraftClient;
import net.minecraft.client.gui.DrawContext;
import net.minecraft.client.gui.screen.ingame.HandledScreen;
import net.minecraft.client.gui.widget.ButtonWidget;
import net.minecraft.entity.player.PlayerInventory;
import net.minecraft.item.ItemStack;
import net.minecraft.registry.Registries;
import net.minecraft.text.Text;
import net.minecraft.util.Identifier;

public class MarketplaceCreationScreen extends HandledScreen<MarketplaceCreationScreenHandler> {
    private static final int PANEL_WIDTH = 176;
    private static final int PANEL_HEIGHT = 166;

    public MarketplaceCreationScreen(MarketplaceCreationScreenHandler handler, PlayerInventory inventory, Text title) {
        super(handler, inventory, title);
        this.backgroundHeight = 166;
        this.playerInventoryTitleY = this.backgroundHeight - 94;
    }

    @Override
    protected void init() {
        super.init();
        this.titleX = (this.backgroundWidth - this.textRenderer.getWidth(this.title)) / 2;

        // Botón Publicar
        this.addDrawableChild(ButtonWidget.builder(Text.of("§a§lPUBLICAR"), button -> {
            ItemStack selling = this.handler.getTradeInventory().getStack(0);
            ItemStack asking = this.handler.getTradeInventory().getStack(1);

            if (selling.isEmpty() || asking.isEmpty()) {
                MinecraftClient.getInstance().player.sendMessage(Text.of("§cDebes poner qué vendes y qué pides."), false);
                return;
            }

            JsonObject sellingJson = new JsonObject();
            sellingJson.addProperty("id", Registries.ITEM.getId(selling.getItem()).toString());
            sellingJson.addProperty("count", selling.getCount());

            JsonObject askingJson = new JsonObject();
            askingJson.addProperty("id", Registries.ITEM.getId(asking.getItem()).toString());
            askingJson.addProperty("count", asking.getCount());

            TradeClient.publishTrade(
                MinecraftClient.getInstance().player.getUuidAsString(),
                MinecraftClient.getInstance().player.getName().getString(),
                "Oferta de " + selling.getName().getString(),
                sellingJson, askingJson
            );
            
            this.close();
        }).dimensions(this.x + this.backgroundWidth / 2 - 40, this.y + 140, 80, 20).build());
    }

    @Override
    protected void drawBackground(DrawContext context, float delta, int mouseX, int mouseY) {
        int i = (this.width - this.backgroundWidth) / 2;
        int j = (this.height - this.backgroundHeight) / 2;
        
        context.getMatrices().push();
        context.getMatrices().translate(0, 0, 10); // Un poco de aire sobre el fondo negro

        // Panel fondo
        context.fill(i, j, i + this.backgroundWidth, j + this.backgroundHeight, 0xFF151515);
        context.fill(i - 1, j - 1, i + this.backgroundWidth + 1, j + this.backgroundHeight + 1, 0xFF444444);

        // Cajas de slots
        context.fill(i + 43, j + 34, i + 43 + 18, j + 34 + 18, 0x4000FF00); // Venta
        context.fill(i + 115, j + 34, i + 115 + 18, j + 34 + 18, 0x40FF0000); // Pedido
        
        context.drawCenteredTextWithShadow(this.textRenderer, "LO QUE VENDES", i + 52, j + 20, 0xAAAAAA);
        context.drawCenteredTextWithShadow(this.textRenderer, "LO QUE PIDES", i + 124, j + 20, 0xAAAAAA);
        
        // Slot inventory slots (dummy boxes for visual)
        for (int row = 0; row < 3; row++) {
            for (int col = 0; col < 9; col++) {
                context.fill(i + 7 + col * 18, j + 83 + row * 18, i + 7 + col * 18 + 18, j + 83 + row * 18 + 18, 0x20FFFFFF);
            }
        }
        for (int col = 0; col < 9; col++) {
            context.fill(i + 7 + col * 18, j + 141, i + 7 + col * 18 + 18, j + 141 + 18, 0x20FFFFFF);
        }

        context.getMatrices().pop();
    }

    @Override
    public void render(DrawContext context, int mouseX, int mouseY, float delta) {
        context.fill(0, 0, this.width, this.height, 0xFF000000); // Fondo sólido negro
        super.render(context, mouseX, mouseY, delta);
        this.drawMouseoverTooltip(context, mouseX, mouseY);
    }

    @Override
    public void renderBackground(DrawContext context, int mouseX, int mouseY, float delta) {
        // Cero borroso
    }
}
