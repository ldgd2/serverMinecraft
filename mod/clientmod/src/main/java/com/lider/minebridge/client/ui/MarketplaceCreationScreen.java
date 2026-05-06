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
    private static final Identifier TEXTURE = Identifier.of("minecraft", "textures/gui/container/generic_54.png"); // Placeholder texture

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
        }).dimensions(this.x + this.backgroundWidth / 2 - 40, this.y + 60, 80, 20).build());
    }

    @Override
    protected void drawBackground(DrawContext context, float delta, int mouseX, int mouseY) {
        int i = (this.width - this.backgroundWidth) / 2;
        int j = (this.height - this.backgroundHeight) / 2;
        context.drawTexture(TEXTURE, i, j, 0, 0, this.backgroundWidth, this.backgroundHeight);
        
        // Dibujar cajas personalizadas para los slots
        context.fill(i + 43, j + 34, i + 43 + 18, j + 34 + 18, 0x8000FF00); // Selling box (verde)
        context.fill(i + 115, j + 34, i + 115 + 18, j + 34 + 18, 0x80FF0000); // Asking box (rojo)
        
        context.drawCenteredTextWithShadow(this.textRenderer, "Vendes", i + 52, j + 24, 0xFFFFFF);
        context.drawCenteredTextWithShadow(this.textRenderer, "Pides", i + 124, j + 24, 0xFFFFFF);
    }

    @Override
    public void render(DrawContext context, int mouseX, int mouseY, float delta) {
        this.renderBackground(context, mouseX, mouseY, delta);
        super.render(context, mouseX, mouseY, delta);
        this.drawMouseoverTooltip(context, mouseX, mouseY);
    }
}
