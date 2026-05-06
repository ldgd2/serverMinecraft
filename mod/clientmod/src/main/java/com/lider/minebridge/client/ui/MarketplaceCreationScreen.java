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
            ItemStack asking1 = this.handler.getTradeInventory().getStack(1);
            ItemStack asking2 = this.handler.getTradeInventory().getStack(2);

            if (selling.isEmpty() || (asking1.isEmpty() && asking2.isEmpty())) {
                MinecraftClient.getInstance().player.sendMessage(Text.of("§cDebes poner qué vendes y al menos qué pides."), false);
                return;
            }

            JsonObject sellingJson = serializeItemStack(selling);
            com.google.gson.JsonElement askingData;
            
            if (!asking1.isEmpty() && !asking2.isEmpty()) {
                com.google.gson.JsonArray array = new com.google.gson.JsonArray();
                array.add(serializeItemStack(asking1));
                array.add(serializeItemStack(asking2));
                askingData = array;
            } else {
                askingData = serializeItemStack(!asking1.isEmpty() ? asking1 : asking2);
            }

            TradeClient.publishTrade(
                MinecraftClient.getInstance().player.getUuidAsString(),
                MinecraftClient.getInstance().player.getName().getString(),
                "Oferta de " + selling.getName().getString(),
                sellingJson, askingData
            );
            
            this.close();
        }).dimensions(this.x + this.backgroundWidth / 2 - 40, this.y + 140, 80, 20).build());

        // Botón X para cerrar
        this.addDrawableChild(ButtonWidget.builder(Text.of("§cX"), b -> this.close())
            .dimensions(this.x + this.backgroundWidth - 15, this.y + 5, 12, 12).build());
    }

    @Override
    protected void drawBackground(DrawContext context, float delta, int mouseX, int mouseY) {
        int i = this.x;
        int j = this.y;
        
        // Panel fondo (Estilo Global)
        context.fill(i - 1, j - 1, i + this.backgroundWidth + 1, j + this.backgroundHeight + 1, 0xFF444444);
        context.fill(i, j, i + this.backgroundWidth, j + this.backgroundHeight, 0xFF101010);
        
        // Cabecera
        context.fill(i, j, i + this.backgroundWidth, j + 25, 0xFF222222);

        // Cajas de slots
        context.fill(i + 43, j + 34, i + 43 + 18, j + 34 + 18, 0x4000FF00); // Venta
        context.fill(i + 115, j + 34, i + 115 + 18, j + 34 + 18, 0x40FF0000); // Pedido
        
        context.drawCenteredTextWithShadow(this.textRenderer, "LO QUE VENDES", i + 52, j + 24, 0xAAAAAA);
        context.drawCenteredTextWithShadow(this.textRenderer, "LO QUE PIDES", i + 124, j + 24, 0xAAAAAA);
        
        context.drawTextWithShadow(this.textRenderer, "Inventario", i + 8, j + 72, 0x404040);
    }

    private JsonObject serializeItemStack(ItemStack stack) {
        JsonObject json = new JsonObject();
        json.addProperty("id", Registries.ITEM.getId(stack.getItem()).toString());
        json.addProperty("count", stack.getCount());
        return json;
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
