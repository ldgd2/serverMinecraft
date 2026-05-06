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
    private TextFieldWidget askingItemField;
    private TextFieldWidget askingCountField;
    private net.minecraft.item.ItemStack sellingStack;

    public MarketplaceCreationScreen() {
        super(Text.of("§6§lCrear Nueva Oferta"));
        this.sellingStack = MinecraftClient.getInstance().player.getMainHandStack();
    }

    @Override
    protected void init() {
        // Título de la venta
        this.addDrawable(new net.minecraft.client.gui.widget.TextWidget(this.width / 2 - 100, 30, 200, 20, Text.of("Título de la Oferta:"), this.textRenderer));
        this.titleField = new TextFieldWidget(this.textRenderer, this.width / 2 - 100, 45, 200, 20, Text.of("Título"));
        this.titleField.setPlaceholder(Text.of("Ej: Vendo Espada de Netherite"));
        if (!sellingStack.isEmpty()) {
            this.titleField.setText("Vendo " + sellingStack.getName().getString());
        }
        this.addDrawableChild(this.titleField);

        // Qué pides a cambio
        this.addDrawable(new net.minecraft.client.gui.widget.TextWidget(this.width / 2 - 100, 75, 140, 20, Text.of("¿Qué pides? (ID):"), this.textRenderer));
        this.askingItemField = new TextFieldWidget(this.textRenderer, this.width / 2 - 100, 90, 140, 20, Text.of("Item"));
        this.askingItemField.setPlaceholder(Text.of("diamond, gold_ingot..."));
        this.addDrawableChild(this.askingItemField);

        // Cantidad
        this.addDrawable(new net.minecraft.client.gui.widget.TextWidget(this.width / 2 + 50, 75, 50, 20, Text.of("Cant.:"), this.textRenderer));
        this.askingCountField = new TextFieldWidget(this.textRenderer, this.width / 2 + 50, 90, 50, 20, Text.of("Cant"));
        this.askingCountField.setText("1");
        this.addDrawableChild(this.askingCountField);

        // Botón Publicar
        this.addDrawableChild(ButtonWidget.builder(Text.of("§a§lPUBLICAR VENTA"), button -> {
            String title = this.titleField.getText();
            String askingId = this.askingItemField.getText().trim();
            int askingCount = 1;
            try { askingCount = Integer.parseInt(this.askingCountField.getText()); } catch(Exception e) {}

            if (title.isEmpty() || askingId.isEmpty() || sellingStack.isEmpty()) {
                MinecraftClient.getInstance().player.sendMessage(Text.of("§cDebes llenar todos los campos y tener un item en la mano."), false);
                return;
            }

            // Preparar JSONs
            JsonObject selling = new JsonObject();
            selling.addProperty("id", net.minecraft.registry.Registries.ITEM.getId(sellingStack.getItem()).toString());
            selling.addProperty("count", sellingStack.getCount());

            JsonObject asking = new JsonObject();
            // Intentar arreglar ID si el usuario no puso namespace
            if (!askingId.contains(":")) askingId = "minecraft:" + askingId;
            asking.addProperty("id", askingId);
            asking.addProperty("count", askingCount);

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
        }).dimensions(this.width / 2 - 100, 140, 200, 20).build());

        // Botón Cancelar
        this.addDrawableChild(ButtonWidget.builder(Text.of("§cCancelar"), button -> this.close())
            .dimensions(this.width / 2 - 100, 170, 200, 20).build());
    }

    @Override
    public void render(net.minecraft.client.gui.DrawContext context, int mouseX, int mouseY, float delta) {
        this.renderBackground(context, mouseX, mouseY, delta);
        context.drawCenteredTextWithShadow(this.textRenderer, this.title, this.width / 2, 10, 0xFFFFFF);
        
        // Mostrar qué está vendiendo (dibujar item)
        if (!sellingStack.isEmpty()) {
            context.drawTextWithShadow(this.textRenderer, "Vendiendo: " + sellingStack.getCount() + "x " + sellingStack.getName().getString(), this.width / 2 - 100, 120, 0xFFFF55);
        } else {
            context.drawTextWithShadow(this.textRenderer, "§c¡No tienes nada en la mano!", this.width / 2 - 100, 120, 0xFF5555);
        }

        super.render(context, mouseX, mouseY, delta);
    }
}
