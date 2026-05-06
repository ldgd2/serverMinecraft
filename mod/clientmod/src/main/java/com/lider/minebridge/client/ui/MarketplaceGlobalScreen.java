package com.lider.minebridge.client.ui;

import com.google.gson.JsonArray;
import com.google.gson.JsonObject;
import com.lider.minebridge.networking.TradeClient;
import net.minecraft.client.MinecraftClient;
import net.minecraft.client.gui.DrawContext;
import net.minecraft.client.gui.screen.Screen;
import net.minecraft.client.gui.widget.ButtonWidget;
import net.minecraft.item.ItemStack;
import net.minecraft.registry.Registries;
import net.minecraft.text.Text;
import net.minecraft.util.Identifier;

import java.util.HashMap;
import java.util.Map;

public class MarketplaceGlobalScreen extends Screen {
    private final JsonArray trades;
    private final Map<Integer, ItemStack[]> iconCache = new HashMap<>();
    private boolean showOnlyMine = false;

    public MarketplaceGlobalScreen(JsonArray trades) {
        super(Text.of("§6§lMarketplace Global"));
        this.trades = trades;
        precacheIcons();
    }

    private void precacheIcons() {
        for (int i = 0; i < trades.size(); i++) {
            try {
                JsonObject trade = trades.get(i).getAsJsonObject();
                if (trade == null || !trade.has("id")) continue;
                
                int tradeId = trade.get("id").getAsInt();
                
                JsonObject sellingJson = trade.getAsJsonObject("selling");
                JsonObject askingJson = trade.getAsJsonObject("asking");

                if (sellingJson != null && askingJson != null) {
                    ItemStack selling = new ItemStack(Registries.ITEM.get(Identifier.of(sellingJson.get("id").getAsString())), sellingJson.get("count").getAsInt());
                    ItemStack asking = new ItemStack(Registries.ITEM.get(Identifier.of(askingJson.get("id").getAsString())), askingJson.get("count").getAsInt());
                    iconCache.put(tradeId, new ItemStack[]{selling, asking});
                }
            } catch (Exception ignored) {}
        }
    }

    @Override
    protected void init() {
        super.init();
        this.clearChildren();
        
        // Botón Toggle: Todas / Mis Publicaciones
        String toggleText = showOnlyMine ? "§bVer: TODAS" : "§dVer: MIS PUBLICACIONES";
        this.addDrawableChild(ButtonWidget.builder(Text.of(toggleText), button -> {
            this.showOnlyMine = !this.showOnlyMine;
            this.init(); // Re-inicializar para actualizar botones
        }).dimensions(this.width / 2 - 100, 30, 200, 20).build());

        int y = 60;
        String myUuid = MinecraftClient.getInstance().player.getUuidAsString();

        for (int i = 0; i < trades.size(); i++) {
            JsonObject trade = trades.get(i).getAsJsonObject();
            if (trade == null) continue;

            String sellerUuid = trade.has("seller_uuid") ? trade.get("seller_uuid").getAsString() : "unknown";
            boolean isSelf = sellerUuid.equals(myUuid);

            if (showOnlyMine && !isSelf) continue;

            int tradeId = trade.get("id").getAsInt();

            // Botón para Comprar / Borrar
            Text buttonText = isSelf ? Text.of("§cELIMINAR") : Text.of("§aCOMPRAR");
            this.addDrawableChild(ButtonWidget.builder(buttonText, button -> {
                if (isSelf) {
                    TradeClient.resolveOffer(tradeId, "cancel", null);
                } else {
                    TradeClient.completeTrade(tradeId, myUuid, MinecraftClient.getInstance().player.getName().getString());
                }
                this.close();
            }).dimensions(this.width / 2 + 60, y, 70, 20).build());

            y += 25;
            if (y > this.height - 60) break; // Límite simple de scroll
        }

        // Botón Cerrar
        this.addDrawableChild(ButtonWidget.builder(Text.of("Cerrar"), b -> this.close())
            .dimensions(this.width / 2 - 50, this.height - 30, 100, 20).build());
    }

    @Override
    public void render(DrawContext context, int mouseX, int mouseY, float delta) {
        this.renderBackground(context, mouseX, mouseY, delta);
        context.drawCenteredTextWithShadow(this.textRenderer, this.title, this.width / 2, 10, 0xFFFFFF);

        int y = 60;
        String myUuid = MinecraftClient.getInstance().player.getUuidAsString();

        for (int i = 0; i < trades.size(); i++) {
            JsonObject trade = trades.get(i).getAsJsonObject();
            if (trade == null) continue;

            String sellerUuid = trade.has("seller_uuid") ? trade.get("seller_uuid").getAsString() : "unknown";
            boolean isSelf = sellerUuid.equals(myUuid);

            if (showOnlyMine && !isSelf) continue;

            int tradeId = trade.get("id").getAsInt();
            String title = trade.has("title") ? trade.get("title").getAsString() : "Sin título";
            String seller = trade.has("seller") ? trade.get("seller").getAsString() : "Anónimo";
            
            // Dibujar información
            context.drawTextWithShadow(this.textRenderer, "§e" + title + " §7(por " + seller + ")", this.width / 2 - 180, y + 5, 0xFFFFFF);
            
            // Usar cache de iconos
            ItemStack[] icons = iconCache.get(tradeId);
            if (icons != null) {
                context.drawItem(icons[0], this.width / 2 - 20, y);
                context.drawTextWithShadow(this.textRenderer, "➔", this.width / 2 + 5, y + 5, 0xFFFFFF);
                context.drawItem(icons[1], this.width / 2 + 25, y);
            }

            y += 25;
            if (y > this.height - 60) break;
        }

        super.render(context, mouseX, mouseY, delta);
    }
}
