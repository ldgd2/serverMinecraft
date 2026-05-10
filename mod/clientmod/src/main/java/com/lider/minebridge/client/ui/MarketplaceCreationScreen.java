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
    private static final Identifier TEXTURE = Identifier.of("minecraft", "textures/gui/container/generic_54.png");

    public MarketplaceCreationScreen(MarketplaceCreationScreenHandler handler, PlayerInventory inventory, Text title) {
        super(handler, inventory, title);
        this.backgroundWidth = 176;
        this.backgroundHeight = 188;
        this.playerInventoryTitleY = this.backgroundHeight - 94;
    }

    @Override
    protected void init() {
        super.init();
        this.titleX = (this.backgroundWidth - this.textRenderer.getWidth(this.title)) / 2;

        // Botón Publicar - Estilo Minecraft
        this.addDrawableChild(ButtonWidget.builder(Text.of("§2§lPUBLICAR"), button -> {
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
        }).dimensions(this.x + 58, this.y + 50, 60, 18).build());
    }

    @Override
    protected void drawBackground(DrawContext context, float delta, int mouseX, int mouseY) {
        int i = this.x;
        int j = this.y;
        
        // Dibujar textura de contenedor
        context.drawTexture(TEXTURE, i, j, 0, 0, this.backgroundWidth, 71);
        context.drawTexture(TEXTURE, i, j + 71, 0, 126, this.backgroundWidth, 117);
        
        // Dibujar slots con etiquetas
        drawLabeledSlot(context, i + 34, j + 27, "§2VENTA");
        drawLabeledSlot(context, i + 96, j + 27, "§cPRECIO");
        drawLabeledSlot(context, i + 122, j + 27, null);
        
        // Flecha central
        context.drawText(this.textRenderer, "§6➡", i + 70, j + 32, 0xFFFFFF, false);
    }

    private void drawLabeledSlot(DrawContext context, int x, int y, String label) {
        context.drawTexture(TEXTURE, x, y, 7, 17, 18, 18);
        if (label != null) {
            context.drawCenteredTextWithShadow(this.textRenderer, label, x + 9, y - 10, 0xFFFFFF);
        }
    }

    private JsonObject serializeItemStack(ItemStack stack) {
        JsonObject json = new JsonObject();
        json.addProperty("id", Registries.ITEM.getId(stack.getItem()).toString());
        json.addProperty("count", stack.getCount());
        return json;
    }

    @Override
    public void render(DrawContext context, int mouseX, int mouseY, float delta) {
        this.renderBackground(context, mouseX, mouseY, delta);
        super.render(context, mouseX, mouseY, delta);
        this.drawMouseoverTooltip(context, mouseX, mouseY);
    }

    @Override
    public void renderBackground(DrawContext context, int mouseX, int mouseY, float delta) {
        super.renderBackground(context, mouseX, mouseY, delta);
    }
}
