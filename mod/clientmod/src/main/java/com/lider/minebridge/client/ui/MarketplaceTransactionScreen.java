package com.lider.minebridge.client.ui;

import com.lider.minebridge.marketplace.MarketplaceTransactionScreenHandler;
import com.lider.minebridge.networking.TradeClient;
import net.minecraft.client.MinecraftClient;
import net.minecraft.client.gui.DrawContext;
import net.minecraft.client.gui.screen.ingame.HandledScreen;
import net.minecraft.client.gui.widget.ButtonWidget;
import net.minecraft.entity.player.PlayerInventory;
import net.minecraft.item.ItemStack;
import net.minecraft.text.Text;
import net.minecraft.util.Identifier;

public class MarketplaceTransactionScreen extends HandledScreen<MarketplaceTransactionScreenHandler> {
    private static final Identifier TEXTURE = Identifier.of("minecraft", "textures/gui/container/generic_54.png");

    public MarketplaceTransactionScreen(MarketplaceTransactionScreenHandler handler, PlayerInventory inventory, Text title) {
        super(handler, inventory, title);
        this.backgroundWidth = 176;
        this.backgroundHeight = 166;
        this.playerInventoryTitleY = this.backgroundHeight - 94;
    }

    @Override
    protected void init() {
        super.init();
        this.titleX = (this.backgroundWidth - this.textRenderer.getWidth(this.title)) / 2;

        // Botón Confirmar Pago - Estilo Minecraft pero destacado
        this.addDrawableChild(ButtonWidget.builder(Text.of("§6§lCONFIRMAR"), button -> {
            if (net.fabricmc.fabric.api.client.networking.v1.ClientPlayNetworking.canSend(com.lider.minebridge.networking.payload.CompleteTradePayload.ID)) {
                net.fabricmc.fabric.api.client.networking.v1.ClientPlayNetworking.send(new com.lider.minebridge.networking.payload.CompleteTradePayload(this.handler.getTradeId()));
            }
            this.close();
        }).dimensions(this.x + 62, this.y + 48, 52, 20).build());
    }

    @Override
    protected void drawBackground(DrawContext context, float delta, int mouseX, int mouseY) {
        int i = this.x;
        int j = this.y;
        
        // Dibujar textura de contenedor (Cofre)
        context.drawTexture(TEXTURE, i, j, 0, 0, this.backgroundWidth, 71);
        context.drawTexture(TEXTURE, i, j + 71, 0, 126, this.backgroundWidth, 96);
        
        // Dibujar slots resaltados para el pago
        drawSlotHighlight(context, i + 34, j + 27, this.handler.getReq1());
        drawSlotHighlight(context, i + 60, j + 27, this.handler.getReq2());
        
        // Flecha de intercambio
        context.drawText(this.textRenderer, "§6§l➡", i + 100, j + 32, 0xFFFFFF, false);
        
        // Slot de resultado (visual)
        context.drawTexture(TEXTURE, i + 124, j + 27, 7, 17, 18, 18);
    }

    private void drawSlotHighlight(DrawContext context, int x, int y, ItemStack req) {
        context.drawTexture(TEXTURE, x, y, 7, 17, 18, 18); // Dibujar un slot vacío
        
        if (!req.isEmpty()) {
            context.getMatrices().push();
            context.getMatrices().translate(0, 0, 100);
            
            // Ítem fantasma indicando el requisito
            context.drawItem(req, x + 1, y + 1);
            context.fill(x + 1, y + 1, x + 17, y + 17, 0xAA222222); 
            
            String count = String.valueOf(req.getCount());
            context.drawTextWithShadow(this.textRenderer, "§e" + count, x + 17 - this.textRenderer.getWidth(count), y + 10, 0xFFFFFF);
            
            context.getMatrices().pop();
        }
    }

    @Override
    public void render(DrawContext context, int mouseX, int mouseY, float delta) {
        // Fondo desenfocado clásico de Minecraft
        this.renderBackground(context, mouseX, mouseY, delta);
        super.render(context, mouseX, mouseY, delta);
        this.drawMouseoverTooltip(context, mouseX, mouseY);
    }

    @Override
    public void renderBackground(DrawContext context, int mouseX, int mouseY, float delta) {
        super.renderBackground(context, mouseX, mouseY, delta);
    }
}
