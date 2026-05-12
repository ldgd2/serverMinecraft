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
import org.lwjgl.glfw.GLFW;

public class MarketplaceCreationScreen extends HandledScreen<MarketplaceCreationScreenHandler> {
    private TextFieldWidget titleField;

    public MarketplaceCreationScreen(MarketplaceCreationScreenHandler handler, PlayerInventory inventory, Text title) {
        super(handler, inventory, title);
        this.backgroundWidth = 196;
        this.backgroundHeight = 220; // Más alto para evitar amontonamiento
        this.playerInventoryTitleY = 100; // Etiqueta de inventario justo arriba de los slots
    }

    @Override
    protected void init() {
        super.init();
        
        // Campo de título (Premium Dark)
        this.titleField = new TextFieldWidget(this.textRenderer, this.x + 10, this.y + 12, 176, 12, Text.of("Título del Trueque"));
        this.titleField.setMaxLength(32);
        this.titleField.setDrawsBackground(true);
        this.titleField.setEditableColor(0xFFD700);
        this.titleField.setText("Mi Oferta");
        this.addSelectableChild(this.titleField);

        // Botón Publicar
        this.addDrawableChild(ButtonWidget.builder(Text.of("§6§lPUBLICAR"), button -> {
            ClientPlayNetworking.send(new PublishTradePayload(this.titleField.getText()));
        }).dimensions(this.x + 103, this.y + 198, 76, 16).build());

        // Botón Cancelar
        this.addDrawableChild(ButtonWidget.builder(Text.of("§7Cancelar"), button -> this.close())
            .dimensions(this.x + 17, this.y + 198, 60, 16).build());
    }

    @Override
    public boolean keyPressed(int keyCode, int scanCode, int modifiers) {
        if (this.titleField.isActive() && this.titleField.isFocused()) {
            if (keyCode == GLFW.GLFW_KEY_ESCAPE) {
                this.titleField.setFocused(false);
                return true;
            }
            // Importante: No cerrar si se presiona E mientras se escribe
            if (keyCode == GLFW.GLFW_KEY_E) return true; 
            return this.titleField.keyPressed(keyCode, scanCode, modifiers);
        }
        return super.keyPressed(keyCode, scanCode, modifiers);
    }

    @Override
    public void renderBackground(DrawContext context, int mouseX, int mouseY, float delta) {
        com.lider.minebridge.ui.framework.UIBackgrounds.renderStandard(context, this.width, this.height);
    }

    @Override
    protected void drawBackground(DrawContext context, float delta, int mouseX, int mouseY) {
        // 1. Panel Principal
        context.fill(this.x, this.y, this.x + this.backgroundWidth, this.y + this.backgroundHeight, 0xFF121212);
        
        // 3. Bordes Dorados de Precisión
        drawBorder(context, this.x, this.y, this.backgroundWidth, this.backgroundHeight, 0xFFFFD700);

        // 4. Mapeo de Slots (Pixel Perfect con el Servidor)
        // Oferta (Izquierda)
        drawSlotGrid(context, this.x + 34, this.y + 40, 3, 3);
        // Pedido (Derecha)
        drawSlotGrid(context, this.x + 108, this.y + 40, 3, 3);
        // Inventario Jugador
        drawSlotGrid(context, this.x + 17, this.y + 112, 9, 3);
        // Hotbar
        drawSlotGrid(context, this.x + 17, this.y + 172, 9, 1);
        
        // Flecha indicadora central
        context.drawText(this.textRenderer, "➡", this.x + 94, this.y + 55, 0x666666, false);
    }

    private void drawBorder(DrawContext context, int x, int y, int w, int h, int color) {
        context.fill(x - 1, y - 1, x + w + 1, y, color); 
        context.fill(x - 1, y + h, x + w + 1, y + h + 1, color); 
        context.fill(x - 1, y, x, y + h, color); 
        context.fill(x + w, y, x + w + 1, y + h, color); 
    }

    private void drawSlotGrid(DrawContext context, int startX, int startY, int cols, int rows) {
        for (int r = 0; r < rows; r++) {
            for (int c = 0; c < cols; c++) {
                int px = startX + (c * 18);
                int py = startY + (r * 18);
                context.fill(px - 1, py - 1, px + 17, py + 17, 0xFF353535); 
                context.fill(px, py, px + 16, py + 16, 0xFF0A0A0A); 
            }
        }
    }

    @Override
    public void render(DrawContext context, int mouseX, int mouseY, float delta) {
        super.render(context, mouseX, mouseY, delta);
        this.titleField.render(context, mouseX, mouseY, delta);
        this.drawMouseoverTooltip(context, mouseX, mouseY);
    }

    @Override
    protected void drawForeground(DrawContext context, int mouseX, int mouseY) {
        context.drawText(this.textRenderer, "§7Tú Ofreces", 34, 28, 0xAAAAAA, false);
        context.drawText(this.textRenderer, "§7Tú Pides", 108, 28, 0xAAAAAA, false);
        context.drawText(this.textRenderer, "§8" + this.playerInventoryTitle.getString(), 17, 100, 0x777777, false);
    }
}
