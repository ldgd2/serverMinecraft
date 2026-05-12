package com.lider.minebridge.marketplace.ui;

import com.lider.minebridge.ui.framework.core.UIConstants;
import com.lider.minebridge.ui.framework.widgets.*;
import com.lider.minebridge.ui.framework.components.*;
import com.lider.minebridge.marketplace.handler.MarketplaceTransactionScreenHandler;
import net.minecraft.client.gui.DrawContext;
import net.minecraft.client.gui.screen.ingame.HandledScreen;
import net.minecraft.client.gui.widget.ButtonWidget;
import net.minecraft.entity.player.PlayerInventory;
import net.minecraft.item.ItemStack;
import net.minecraft.text.Text;

import java.util.List;

/**
 * Vista: Marketplace - Transacción.
 */
public class MarketplaceTransactionScreen extends HandledScreen<MarketplaceTransactionScreenHandler> {

    public MarketplaceTransactionScreen(MarketplaceTransactionScreenHandler handler, PlayerInventory inventory, Text title) {
        super(handler, inventory, title);
        this.backgroundWidth = 176;
        this.backgroundHeight = 166;
    }

    @Override
    protected void init() {
        super.init();
        this.addDrawableChild(ButtonWidget.builder(Text.of("§6Cerrar Trato"), button -> {
            net.fabricmc.fabric.api.client.networking.v1.ClientPlayNetworking.send(
                new com.lider.minebridge.marketplace.networking.CompleteTradePayload(this.handler.getTradeId())
            );
            this.close();
        }).dimensions(this.x + 105, this.y + 60, 65, 16).build());
    }

    @Override
    protected void drawBackground(DrawContext context, float delta, int mouseX, int mouseY) {
        int i = this.x;
        int j = this.y;
        
        // Estructura Mapeada
        PanelComponent.draw(context, i, j, backgroundWidth, backgroundHeight);
        LabelWidget.drawCentered(context, this.textRenderer, this.title, i + backgroundWidth / 2, j + 8, UIConstants.TEXT_DEFAULT);

        // Pago
        LabelWidget.draw(context, this.textRenderer, "§8Tu Pago:", i + 35, j + 18, UIConstants.TEXT_DEFAULT, false);
        GridComponent.draw(context, i + 34, j + 25, 3, 3);
        
        IconWidget.drawArrow(context, i + 95, j + 35, UIConstants.TEXT_DEFAULT);

        // Requerimientos
        List<ItemStack> reqs = this.handler.getRequirements();
        if (reqs != null) {
            for (int k = 0; k < Math.min(reqs.size(), 3); k++) {
                int rx = i + 120;
                int ry = j + 25 + k * 18;
                SlotWidget.draw(context, rx, ry);
                
                context.getMatrices().push();
                context.getMatrices().translate(0, 0, 100);
                context.drawItem(reqs.get(k), rx + 1, ry + 1);
                // Dibujamos la cantidad manualmente si es mayor a 1
                if (reqs.get(k).getCount() > 1) {
                    String count = String.valueOf(reqs.get(k).getCount());
                    context.drawText(this.textRenderer, count, rx + 19 - this.textRenderer.getWidth(count), ry + 9, 0xFFFFFF, true);
                }
                context.getMatrices().pop();
            }
        }

        // Inventario
        InventoryComponent.drawFull(context, this.textRenderer, i + 8, j + 72);
    }

    @Override
    public void renderBackground(DrawContext context, int mouseX, int mouseY, float delta) {
        com.lider.minebridge.ui.framework.UIBackgrounds.renderStandard(context, this.width, this.height);
    }

    @Override
    public void render(DrawContext context, int mouseX, int mouseY, float delta) {
        super.render(context, mouseX, mouseY, delta);
        this.drawMouseoverTooltip(context, mouseX, mouseY);
    }
}
