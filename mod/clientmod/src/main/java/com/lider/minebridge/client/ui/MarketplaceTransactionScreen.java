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

            // Aquí el cliente avisa que ya puso las cosas. 
            // Pero lo ideal es que el servidor lo verifique al darle click al botón.
            // Para simplicidad en este prototipo, enviamos la resolución.
            TradeClient.completeTrade(this.handler.getTradeId(), 
                MinecraftClient.getInstance().player.getUuidAsString(), 
                MinecraftClient.getInstance().player.getName().getString());
            
            this.close();
        }).dimensions(this.x + this.backgroundWidth / 2 - 60, this.y + 60, 120, 20).build());
    }

    @Override
    protected void drawBackground(DrawContext context, float delta, int mouseX, int mouseY) {
        int i = (this.width - this.backgroundWidth) / 2;
        int j = (this.height - this.backgroundHeight) / 2;
        context.drawTexture(TEXTURE, i, j, 0, 0, this.backgroundWidth, this.backgroundHeight);
        
        // Dibujar caja de pago
        context.fill(i + 79, j + 34, i + 79 + 18, j + 34 + 18, 0x80FFAA00); 
        context.drawCenteredTextWithShadow(this.textRenderer, "Coloca el PAGO aquí", i + 88, j + 24, 0xFFFFFF);
    }

    @Override
    public void render(DrawContext context, int mouseX, int mouseY, float delta) {
        context.fill(0, 0, this.width, this.height, 0xFF000000); // Bloqueo total
        
        int i = (this.width - this.backgroundWidth) / 2;
        int j = (this.height - this.backgroundHeight) / 2;
        
        context.getMatrices().push();
        context.getMatrices().translate(0, 0, 100);

        // Dibujar un borde elegante alrededor de la textura del inventario
        context.fill(i - 2, j - 2, i + this.backgroundWidth + 2, j + this.backgroundHeight + 2, 0xFF664400); 

        context.getMatrices().pop();

        super.render(context, mouseX, mouseY, delta);
        this.drawMouseoverTooltip(context, mouseX, mouseY);
    }

    @Override
    public void renderBackground(DrawContext context, int mouseX, int mouseY, float delta) {
        // Bloquear borroso
    }
}
