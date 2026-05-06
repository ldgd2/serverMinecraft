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
    private final boolean showOnlyMine;
    
    private static final int PANEL_WIDTH = 340;
    private static final int PANEL_HEIGHT = 200;

    public MarketplaceGlobalScreen(JsonArray trades) {
        this(trades, false);
    }

    public MarketplaceGlobalScreen(JsonArray trades, boolean showOnlyMine) {
        super(showOnlyMine ? Text.of("§d§lMIS PUBLICACIONES") : Text.of("§6§lMARKETPLACE GLOBAL"));
        this.trades = trades;
        this.showOnlyMine = showOnlyMine;
        precacheIcons();
    }

    private void precacheIcons() {
        for (int i = 0; i < trades.size(); i++) {
            try {
                JsonObject trade = trades.get(i).getAsJsonObject();
                if (trade == null || !trade.has("id")) continue;
                int tradeId = trade.get("id").getAsInt();
                JsonObject sellingJson = trade.getAsJsonObject("selling");
                com.google.gson.JsonElement askingElement = trade.get("asking");
                if (sellingJson != null && askingElement != null) {
                    ItemStack selling = new ItemStack(Registries.ITEM.get(Identifier.of(sellingJson.get("id").getAsString())), sellingJson.get("count").getAsInt());
                    ItemStack asking1 = ItemStack.EMPTY;
                    ItemStack asking2 = ItemStack.EMPTY;

                    if (askingElement.isJsonArray()) {
                        JsonArray array = askingElement.getAsJsonArray();
                        if (array.size() > 0) asking1 = parseJsonItem(array.get(0).getAsJsonObject());
                        if (array.size() > 1) asking2 = parseJsonItem(array.get(1).getAsJsonObject());
                    } else if (askingElement.isJsonObject()) {
                        asking1 = parseJsonItem(askingElement.getAsJsonObject());
                    }
                    
                    iconCache.put(tradeId, new ItemStack[]{selling, asking1, asking2});
                }
            } catch (Exception ignored) {}
        }
    }

    @Override
    protected void init() {
        super.init();
        this.clearChildren();
        
        int centerX = this.width / 2;
        int centerY = this.height / 2;
        int startY = centerY - (PANEL_HEIGHT / 2) + 40;
        
        String myUuid = MinecraftClient.getInstance().player.getUuidAsString();

        int renderedCount = 0;
        for (int i = 0; i < trades.size(); i++) {
            JsonObject trade = trades.get(i).getAsJsonObject();
            if (trade == null) continue;

            String sellerUuid = trade.has("seller_uuid") ? trade.get("seller_uuid").getAsString() : "unknown";
            boolean isSelf = sellerUuid.equals(myUuid);
            if (showOnlyMine && !isSelf) continue;

            int tradeId = trade.get("id").getAsInt();

            Text buttonText = isSelf ? Text.of("§cELIMINAR") : Text.of("§bVER");
            this.addDrawableChild(ButtonWidget.builder(buttonText, button -> {
                if (isSelf) {
                    TradeClient.cancelTrade(tradeId);
                    this.close();
                } else {
                    MinecraftClient.getInstance().setScreen(new MarketplaceDetailScreen(trade));
                }
            }).dimensions(centerX + 85, startY + (renderedCount * 25), 65, 20).build());

            renderedCount++;
            if (startY + (renderedCount * 25) > centerY + (PANEL_HEIGHT / 2) - 30) break;
        }

        this.addDrawableChild(ButtonWidget.builder(Text.of("Cerrar"), b -> this.close())
            .dimensions(centerX - 50, centerY + (PANEL_HEIGHT / 2) - 25, 100, 20).build());

        // Botón X para cerrar (Esquina superior derecha)
        this.addDrawableChild(ButtonWidget.builder(Text.of("§cX"), b -> this.close())
            .dimensions(centerX + (PANEL_WIDTH / 2) - 20, centerY - (PANEL_HEIGHT / 2) + 2, 18, 18).build());
    }

    @Override
    public void render(DrawContext context, int mouseX, int mouseY, float delta) {
        // Dibujar fondo sólido primero para bloquear el mundo
        context.fill(0, 0, this.width, this.height, 0xFF000000); 

        int centerX = this.width / 2;
        int centerY = this.height / 2;
        int x1 = centerX - (PANEL_WIDTH / 2);
        int y1 = centerY - (PANEL_HEIGHT / 2);
        int x2 = centerX + (PANEL_WIDTH / 2);
        int y2 = centerY + (PANEL_HEIGHT / 2);

        // Subir a la capa de GUI (Z=100)
        context.getMatrices().push();
        context.getMatrices().translate(0, 0, 100);

        // Panel Principal
        context.fill(x1 - 1, y1 - 1, x2 + 1, y2 + 1, 0xFF444444);
        context.fill(x1, y1, x2, y2, 0xFF101010);
        
        // Cabecera
        context.fill(x1, y1, x2, y1 + 25, 0xFF222222);
        context.drawCenteredTextWithShadow(this.textRenderer, this.title, centerX, y1 + 8, 0xFFFFFF);

        int startY = y1 + 40;
        String myUuid = MinecraftClient.getInstance().player.getUuidAsString();

        int renderedCount = 0;
        for (int i = 0; i < trades.size(); i++) {
            JsonObject trade = trades.get(i).getAsJsonObject();
            if (trade == null) continue;

            String sellerUuid = trade.has("seller_uuid") ? trade.get("seller_uuid").getAsString() : "unknown";
            boolean isSelf = sellerUuid.equals(myUuid);
            if (showOnlyMine && !isSelf) continue;

            int tradeId = trade.get("id").getAsInt();
            String title = trade.has("title") ? trade.get("title").getAsString() : "Sin título";
            String seller = trade.has("seller") ? trade.get("seller").getAsString() : "Anónimo";
            
            int currentY = startY + (renderedCount * 25);
            
            // Fila de item
            context.fill(x1 + 5, currentY - 2, x2 - 5, currentY + 22, 0x33FFFFFF);
            context.drawTextWithShadow(this.textRenderer, "§e" + truncate(title, 10), x1 + 10, currentY + 2, 0xFFFFFF);
            context.drawTextWithShadow(this.textRenderer, "§7de §f" + truncate(seller, 8), x1 + 10, currentY + 11, 0xFFFFFF);
            
            ItemStack[] icons = iconCache.get(tradeId);
            if (icons != null) {
                // Venta
                context.drawItem(icons[0], centerX - 60, currentY);
                context.drawTextWithShadow(this.textRenderer, "➔", centerX - 35, currentY + 6, 0xFFFFFF);
                
                // Pedido 1
                if (!icons[1].isEmpty()) {
                    context.drawItem(icons[1], centerX - 10, currentY);
                }
                
                // Pedido 2
                if (!icons[2].isEmpty()) {
                    context.drawItem(icons[2], centerX + 15, currentY);
                }
            }

            renderedCount++;
            if (currentY + 25 > y2 - 30) break;
        }

        super.render(context, mouseX, mouseY, delta);
        context.getMatrices().pop(); // Restaurar capa
    }
    
    private ItemStack parseJsonItem(JsonObject json) {
        if (json == null) return ItemStack.EMPTY;
        return new ItemStack(Registries.ITEM.get(Identifier.of(json.get("id").getAsString())), json.get("count").getAsInt());
    }

    private String truncate(String text, int max) {
        return text.length() > max ? text.substring(0, max - 1) + "…" : text;
    }

    @Override
    public boolean shouldPause() {
        return false;
    }

    @Override
    public void renderBackground(DrawContext context, int mouseX, int mouseY, float delta) {
        // Evitar el desenfoque
    }
}
