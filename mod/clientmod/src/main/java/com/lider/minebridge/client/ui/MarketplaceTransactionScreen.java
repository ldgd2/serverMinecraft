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
        this.backgroundHeight = 166;
        this.playerInventoryTitleY = this.backgroundHeight - 94;
    }

    @Override
    protected void init() {
        super.init();
        this.titleX = (this.backgroundWidth - this.textRenderer.getWidth(this.title)) / 2;

        // Botón Confirmar Pago
        this.addDrawableChild(ButtonWidget.builder(Text.of("§6§lCONFIRMAR PAGO"), button -> {
            ItemStack payment = this.handler.getInventory().getStack(0);
            if (payment.isEmpty()) {
                MinecraftClient.getInstance().player.sendMessage(Text.of("§cDebes poner el pago en el slot."), false);
                return;
            }

            // Enviamos un paquete al servidor para que él verifique el slot y complete el trade
            if (net.fabricmc.fabric.api.client.networking.v1.ClientPlayNetworking.canSend(com.lider.minebridge.networking.payload.CompleteTradePayload.ID)) {
                net.fabricmc.fabric.api.client.networking.v1.ClientPlayNetworking.send(new com.lider.minebridge.networking.payload.CompleteTradePayload(this.handler.getTradeId()));
            }
            
            this.close();
        }).dimensions(this.x + this.backgroundWidth / 2 - 60, this.y + 60, 120, 20).build());

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

        // Dibujar cajas de pago centradas
        int slotX1 = i + (this.backgroundWidth / 2) - 20;
        int slotX2 = i + (this.backgroundWidth / 2) + 6;
        int slotY = j + 40;

        context.fill(slotX1, slotY, slotX1 + 18, slotY + 18, 0x80FFAA00); 
        context.fill(slotX2, slotY, slotX2 + 18, slotY + 18, 0x80FFAA00); 
        
        context.drawCenteredTextWithShadow(this.textRenderer, "Coloca el PAGO aquí", i + this.backgroundWidth / 2, j + 30, 0xFFFFFF);
        
        context.drawTextWithShadow(this.textRenderer, "Inventario", i + 8, j + 72, 0x404040);
    }

    @Override
    public void render(DrawContext context, int mouseX, int mouseY, float delta) {
        context.fill(0, 0, this.width, this.height, 0xFF000000); // Fondo sólido negro
        super.render(context, mouseX, mouseY, delta);
        this.drawMouseoverTooltip(context, mouseX, mouseY);
    }

    @Override
    public void renderBackground(DrawContext context, int mouseX, int mouseY, float delta) {
        // Bloquear borroso
    }
}
