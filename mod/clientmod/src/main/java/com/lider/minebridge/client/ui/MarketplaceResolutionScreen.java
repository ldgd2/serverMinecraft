package com.lider.minebridge.client.ui;

import com.google.gson.JsonArray;
import com.google.gson.JsonObject;
import com.lider.minebridge.networking.TradeClient;
import net.minecraft.client.MinecraftClient;
import net.minecraft.client.gui.screen.Screen;
import net.minecraft.client.gui.widget.ButtonWidget;
import net.minecraft.client.gui.widget.TextFieldWidget;
import net.minecraft.text.Text;

public class MarketplaceResolutionScreen extends Screen {
    private final int offerId;
    private final String buyerName;
    private final JsonArray offeredItems;
    private TextFieldWidget reasonField;

    public MarketplaceResolutionScreen(int offerId, String buyerName, JsonArray offeredItems) {
        super(Text.of("§6Resolución de Contra-oferta"));
        this.offerId = offerId;
        this.buyerName = buyerName;
        this.offeredItems = offeredItems;
    }

    @Override
    protected void init() {
        // Campo para motivo de rechazo
        this.reasonField = new TextFieldWidget(this.textRenderer, this.width / 2 - 100, 100, 200, 20, Text.of("Motivo"));
        this.reasonField.setPlaceholder(Text.of("Motivo del rechazo (opcional)"));
        this.addDrawableChild(this.reasonField);

        // Botón Aceptar
        this.addDrawableChild(ButtonWidget.builder(Text.of("§a§lACEPTAR TRATO"), button -> {
            TradeClient.resolveOffer(this.offerId, "accept", null).thenAccept(success -> {
                if (success) {
                    MinecraftClient.getInstance().execute(() -> {
                        this.close();
                        MinecraftClient.getInstance().player.sendMessage(Text.of("§6[Market] §a¡Trato cerrado! Los items se han intercambiado."), false);
                    });
                }
            });
        }).dimensions(this.width / 2 - 100, 140, 200, 20).build());

        // Botón Rechazar
        this.addDrawableChild(ButtonWidget.builder(Text.of("§cRechazar"), button -> {
            String reason = this.reasonField.getText();
            TradeClient.resolveOffer(this.offerId, "reject", reason).thenAccept(success -> {
                if (success) {
                    MinecraftClient.getInstance().execute(() -> {
                        this.close();
                        MinecraftClient.getInstance().player.sendMessage(Text.of("§6[Market] §cOferta rechazada."), false);
                    });
                }
            });
        }).dimensions(this.width / 2 - 100, 170, 200, 20).build());
    }

    @Override
    public void render(net.minecraft.client.gui.DrawContext context, int mouseX, int mouseY, float delta) {
        this.renderBackground(context, mouseX, mouseY, delta);
        context.drawCenteredTextWithShadow(this.textRenderer, this.title, this.width / 2, 20, 0xFFFFFF);
        context.drawCenteredTextWithShadow(this.textRenderer, Text.of("§b" + this.buyerName + " §foferta:"), this.width / 2, 50, 0xFFFFFF);
        
        // Renderizar nombres de los items ofrecidos
        for (int i = 0; i < offeredItems.size(); i++) {
            JsonObject item = offeredItems.get(i).getAsJsonObject();
            String name = item.get("id").getAsString().split(":")[1];
            int count = item.get("count").getAsInt();
            context.drawCenteredTextWithShadow(this.textRenderer, Text.of("§e" + count + "x " + name), this.width / 2, 70 + (i * 10), 0xFFFFFF);
        }
        
        super.render(context, mouseX, mouseY, delta);
    }
}
