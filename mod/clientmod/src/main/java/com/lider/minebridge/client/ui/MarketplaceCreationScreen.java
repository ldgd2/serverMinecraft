package com.lider.minebridge.client.ui;

import com.google.gson.JsonArray;
import com.google.gson.JsonObject;
import com.lider.minebridge.networking.TradeClient;
import net.minecraft.client.MinecraftClient;
import net.minecraft.client.gui.screen.Screen;
import net.minecraft.client.gui.widget.ButtonWidget;
import net.minecraft.client.gui.widget.TextFieldWidget;
import net.minecraft.text.Text;

public class MarketplaceCreationScreen extends Screen {
    private TextFieldWidget titleField;
    private JsonObject sellingItem;
    private JsonObject askingItem;

    public MarketplaceCreationScreen() {
        super(Text.of("§6Crear Nueva Oferta"));
    }

    @Override
    protected void init() {
        // Título de la venta
        this.titleField = new TextFieldWidget(this.textRenderer, this.width / 2 - 100, 40, 200, 20, Text.of("Título"));
        this.titleField.setPlaceholder(Text.of("Ej: Vendo Espada de Netherite"));
        this.addDrawableChild(this.titleField);

        // Botón Publicar
        this.addDrawableChild(ButtonWidget.builder(Text.of("§a§lPUBLICAR VENTA"), button -> {
            String title = this.titleField.getText();
            if (title.isEmpty()) return;

            // En un caso real, aquí capturaríamos el item seleccionado
            // Por ahora usamos placeholders para validar el flujo
            JsonObject selling = new JsonObject();
            selling.addProperty("id", "minecraft:diamond");
            selling.addProperty("count", 64);

            JsonObject asking = new JsonObject();
            asking.addProperty("id", "minecraft:netherite_ingot");
            asking.addProperty("count", 1);

            TradeClient.publishTrade(
                MinecraftClient.getInstance().player.getUuidAsString(),
                MinecraftClient.getInstance().player.getName().getString(),
                title, selling, asking
            ).thenAccept(success -> {
                if (success) {
                    MinecraftClient.getInstance().execute(() -> {
                        this.close();
                        MinecraftClient.getInstance().player.sendMessage(Text.of("§6[Market] §a¡Venta publicada con éxito!"), false);
                    });
                }
            });
        }).dimensions(this.width / 2 - 100, 160, 200, 20).build());

        // Botón Cancelar
        this.addDrawableChild(ButtonWidget.builder(Text.of("§cCancelar"), button -> this.close())
            .dimensions(this.width / 2 - 100, 190, 200, 20).build());
    }

    @Override
    public void render(net.minecraft.client.gui.DrawContext context, int mouseX, int mouseY, float delta) {
        this.renderBackground(context, mouseX, mouseY, delta);
        context.drawCenteredTextWithShadow(this.textRenderer, this.title, this.width / 2, 20, 0xFFFFFF);
        super.render(context, mouseX, mouseY, delta);
    }
}
