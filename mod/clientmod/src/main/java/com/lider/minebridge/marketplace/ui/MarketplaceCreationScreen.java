package com.lider.minebridge.marketplace.ui;

import com.lider.minebridge.marketplace.handler.MarketplaceCreationScreenHandler;
import com.lider.minebridge.marketplace.networking.PublishTradePayload;
import net.fabricmc.fabric.api.client.networking.v1.ClientPlayNetworking;
import net.minecraft.client.gui.DrawContext;
import net.minecraft.client.gui.screen.ingame.HandledScreen;
import net.minecraft.client.gui.widget.ButtonWidget;
import net.minecraft.client.gui.widget.TextFieldWidget;
import net.minecraft.entity.player.PlayerInventory;
import net.minecraft.text.Text;

public class MarketplaceCreationScreen extends HandledScreen<MarketplaceCreationScreenHandler> {
    private TextFieldWidget titleField;

    public MarketplaceCreationScreen(MarketplaceCreationScreenHandler handler, PlayerInventory inventory, Text title) {
        super(handler, inventory, title);
        this.backgroundWidth = 196;
        this.backgroundHeight = 186;
        this.playerInventoryTitleY = this.backgroundHeight - 94;
    }

    @Override
    protected void init() {
        super.init();
        int centerX = this.x + this.backgroundWidth / 2;
        
        // Campo de título (Premium Dark)
        this.titleField = new TextFieldWidget(this.textRenderer, this.x + 10, this.y + 18, 176, 12, Text.of("Título del Trueque"));
        this.titleField.setMaxLength(32);
        this.titleField.setDrawsBackground(true);
        this.titleField.setEditableColor(0xFFD700);
        this.titleField.setUneditableColor(0xAAAAAA);
        this.titleField.setText("Mi Oferta");
        this.addSelectableChild(this.titleField);

        // Botón Publicar
        this.addDrawableChild(ButtonWidget.builder(Text.of("§6§lPUBLICAR"), button -> {
            ClientPlayNetworking.send(new PublishTradePayload(this.titleField.getText()));
            this.close();
        }).dimensions(this.x + 110, this.y + 162, 76, 18).build());

        // Botón Cancelar
        this.addDrawableChild(ButtonWidget.builder(Text.of("§7Cancelar"), button -> this.close())
            .dimensions(this.x + 10, this.y + 162, 60, 18).build());
    }

    @Override
    protected void drawBackground(DrawContext context, float delta, int mouseX, int mouseY) {
        // Fondo Principal (Sólido y Premium)
        context.fill(this.x, this.y, this.x + this.backgroundWidth, this.y + this.backgroundHeight, 0xFF121212);
        
        // Bordes Dorados
        context.fill(this.x - 1, this.y - 1, this.x + this.backgroundWidth + 1, this.y, 0xFFFFD700); // Top
        context.fill(this.x - 1, this.y + this.backgroundHeight, this.x + this.backgroundWidth + 1, this.y + this.backgroundHeight + 1, 0xFFFFD700); // Bottom
        context.fill(this.x - 1, this.y, this.x, this.y + this.backgroundHeight, 0xFFFFD700); // Left
        context.fill(this.x + this.backgroundWidth, this.y, this.x + this.backgroundWidth + 1, this.y + this.backgroundHeight, 0xFFFFD700); // Right

        // Secciones (Sombras sutiles)
        context.fill(this.x + 7, this.y + 35, this.x + 189, this.y + 88, 0xFF1E1E1E);
        
        // Dibujar Slots de forma manual o dejar que el engine lo haga sobre nuestro fondo
        // Nota: Los slots se renderizan automáticamente en las coordenadas del handler
    }

    @Override
    public void render(DrawContext context, int mouseX, int mouseY, float delta) {
        this.renderBackground(context, mouseX, mouseY, delta);
        super.render(context, mouseX, mouseY, delta);
        this.titleField.render(context, mouseX, mouseY, delta);
        this.drawMouseoverTooltip(context, mouseX, mouseY);
    }

    @Override
    protected void drawForeground(DrawContext context, int mouseX, int mouseY) {
        context.drawText(this.textRenderer, this.title, 8, 6, 0xFFFFD700, false);
        context.drawText(this.textRenderer, "Tú Ofreces", 10, 38, 0xAAAAAA, false);
        context.drawText(this.textRenderer, "Tú Pides", 106, 38, 0xAAAAAA, false);
        context.drawText(this.textRenderer, this.playerInventoryTitle, 8, this.playerInventoryTitleY, 0x777777, false);
    }
}
