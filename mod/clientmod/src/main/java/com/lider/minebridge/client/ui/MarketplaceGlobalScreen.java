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
    
    private static final int PANEL_WIDTH = 380;
    private static final int PANEL_HEIGHT = 220;
    private static final int ROWS = 4;
    private static final int COLS = 3;
    private static final int PAGE_SIZE = ROWS * COLS;
    
    private int currentPage = 0;

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
        int startX = centerX - (PANEL_WIDTH / 2) + 15;
        int startY = centerY - (PANEL_HEIGHT / 2) + 35;
        
        String myUuid = MinecraftClient.getInstance().player.getUuidAsString();

        // Filtrar trades visibles
        java.util.List<JsonObject> visibleTrades = new java.util.ArrayList<>();
        for (int i = 0; i < trades.size(); i++) {
            JsonObject trade = trades.get(i).getAsJsonObject();
            String sellerUuid = trade.has("seller_uuid") ? trade.get("seller_uuid").getAsString() : "unknown";
            if (showOnlyMine && !sellerUuid.equals(myUuid)) continue;
            visibleTrades.add(trade);
        }

        int maxPage = (int) Math.ceil((double) visibleTrades.size() / PAGE_SIZE) - 1;
        if (currentPage > maxPage) currentPage = Math.max(0, maxPage);

        int startIndex = currentPage * PAGE_SIZE;
        for (int i = 0; i < PAGE_SIZE && (startIndex + i) < visibleTrades.size(); i++) {
            JsonObject trade = visibleTrades.get(startIndex + i);
            int tradeId = trade.get("id").getAsInt();
            String sellerUuid = trade.has("seller_uuid") ? trade.get("seller_uuid").getAsString() : "unknown";
            boolean isSelf = sellerUuid.equals(myUuid);

            int col = i % COLS;
            int row = i / COLS;
            int x = startX + (col * 120);
            int y = startY + (row * 40);

            Text buttonText = isSelf ? Text.of("§cDEL") : Text.of("§bVER");
            this.addDrawableChild(ButtonWidget.builder(buttonText, button -> {
                if (isSelf) {
                    TradeClient.cancelTrade(tradeId);
                    this.close();
                } else {
                    MinecraftClient.getInstance().setScreen(new MarketplaceDetailScreen(trade));
                }
            }).dimensions(x + 75, y + 10, 35, 20).build());
        }

        // Navegación
        if (currentPage > 0) {
            this.addDrawableChild(ButtonWidget.builder(Text.of("§e<<"), b -> { currentPage--; init(); })
                .dimensions(centerX - 120, centerY + (PANEL_HEIGHT / 2) - 25, 30, 20).build());
        }
        if (startIndex + PAGE_SIZE < visibleTrades.size()) {
            this.addDrawableChild(ButtonWidget.builder(Text.of("§e>>"), b -> { currentPage++; init(); })
                .dimensions(centerX + 90, centerY + (PANEL_HEIGHT / 2) - 25, 30, 20).build());
        }

        this.addDrawableChild(ButtonWidget.builder(Text.of("Cerrar"), b -> this.close())
            .dimensions(centerX - 40, centerY + (PANEL_HEIGHT / 2) - 25, 80, 20).build());

        // Botón X
        this.addDrawableChild(ButtonWidget.builder(Text.of("§cX"), b -> this.close())
            .dimensions(centerX + (PANEL_WIDTH / 2) - 18, centerY - (PANEL_HEIGHT / 2) + 4, 14, 14).build());
    }

    @Override
    public void render(DrawContext context, int mouseX, int mouseY, float delta) {
        context.fill(0, 0, this.width, this.height, 0xCC000000); 

        int centerX = this.width / 2;
        int centerY = this.height / 2;
        int x1 = centerX - (PANEL_WIDTH / 2);
        int y1 = centerY - (PANEL_HEIGHT / 2);
        int x2 = centerX + (PANEL_WIDTH / 2);
        int y2 = centerY + (PANEL_HEIGHT / 2);

        context.getMatrices().push();
        context.getMatrices().translate(0, 0, 100);

        // Panel Principal
        context.fill(x1 - 1, y1 - 1, x2 + 1, y2 + 1, 0xFF555555);
        context.fill(x1, y1, x2, y2, 0xFF181818);
        
        // Cabecera
        context.fill(x1, y1, x2, y1 + 25, 0xFF252525);
        context.drawCenteredTextWithShadow(this.textRenderer, this.title, centerX, y1 + 8, 0xFFFFFF);

        int startX = x1 + 15;
        int startY = y1 + 35;
        String myUuid = MinecraftClient.getInstance().player.getUuidAsString();

        java.util.List<JsonObject> visibleTrades = new java.util.ArrayList<>();
        for (int i = 0; i < trades.size(); i++) {
            JsonObject trade = trades.get(i).getAsJsonObject();
            String sellerUuid = trade.has("seller_uuid") ? trade.get("seller_uuid").getAsString() : "unknown";
            if (showOnlyMine && !sellerUuid.equals(myUuid)) continue;
            visibleTrades.add(trade);
        }

        int startIndex = currentPage * PAGE_SIZE;
        for (int i = 0; i < PAGE_SIZE && (startIndex + i) < visibleTrades.size(); i++) {
            JsonObject trade = visibleTrades.get(startIndex + i);
            int tradeId = trade.get("id").getAsInt();
            String seller = trade.has("seller") ? trade.get("seller").getAsString() : "Anónimo";
            
            int col = i % COLS;
            int row = i / COLS;
            int x = startX + (col * 120);
            int y = startY + (row * 40);
            
            // Tarjeta de trade
            context.fill(x, y, x + 115, y + 36, 0x22FFFFFF);
            context.fill(x, y, x + 115, y + 1, 0x44FFFFFF); // Borde superior sutil
            
            context.drawTextWithShadow(this.textRenderer, "§f" + truncate(seller, 8), x + 40, y + 4, 0xAAAAAA);
            
            ItemStack[] icons = iconCache.get(tradeId);
            if (icons != null) {
                context.drawItem(icons[0], x + 2, y + 2);
                context.drawTextWithShadow(this.textRenderer, "➔", x + 20, y + 6, 0xFFFFFF);
                context.drawItem(icons[1], x + 32, y + 18);
                if (!icons[2].isEmpty()) {
                    context.drawItem(icons[2], x + 52, y + 18);
                }
            }
        }

        // Indicador de página
        int maxPage = (int) Math.ceil((double) visibleTrades.size() / PAGE_SIZE);
        if (maxPage > 1) {
            context.drawCenteredTextWithShadow(this.textRenderer, (currentPage + 1) + " / " + maxPage, centerX, y2 - 18, 0xAAAAAA);
        }

        super.render(context, mouseX, mouseY, delta);
        context.getMatrices().pop();
    }
    
    private ItemStack parseJsonItem(JsonObject json) {
        if (json == null || !json.has("id")) return ItemStack.EMPTY;
        return new ItemStack(Registries.ITEM.get(Identifier.of(json.get("id").getAsString())), json.get("count").getAsInt());
    }

    private String truncate(String text, int max) {
        return text.length() > max ? text.substring(0, max - 1) + "…" : text;
    }

    @Override
    public boolean shouldPause() { return false; }

    @Override
    public void renderBackground(DrawContext context, int mouseX, int mouseY, float delta) {}
}
