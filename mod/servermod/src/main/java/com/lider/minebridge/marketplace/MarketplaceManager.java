package com.lider.minebridge.marketplace;

import com.google.gson.JsonArray;
import com.google.gson.JsonObject;
import com.lider.minebridge.MineBridge;
import com.lider.minebridge.core.MineCore;
import com.lider.minebridge.marketplace.handler.MarketplaceCreationScreenHandler;
import com.lider.minebridge.marketplace.handler.MarketplaceTransactionScreenHandler;
import com.lider.minebridge.marketplace.networking.TradeClient;
import com.lider.minebridge.marketplace.networking.TransactionScreenDataPayload;
import com.lider.minebridge.marketplace.networking.MarketplaceDataPayload;
import net.minecraft.entity.player.PlayerEntity;
import net.minecraft.entity.player.PlayerInventory;
import net.minecraft.inventory.Inventory;
import net.minecraft.item.ItemStack;
import net.minecraft.registry.Registries;
import net.minecraft.server.network.ServerPlayerEntity;
import net.minecraft.text.Text;
import net.minecraft.util.Identifier;
import net.fabricmc.fabric.api.networking.v1.ServerPlayNetworking;

/**
 * Cerebro del Marketplace (Servidor).
 * Optimizado con MineCore para evitar cualquier bloqueo del hilo principal.
 */
public class MarketplaceManager {

    /**
     * Envía los datos de los trades al cliente de forma asíncrona.
     */
    public static void openMarketplace(ServerPlayerEntity player, JsonArray trades) {
        if (ServerPlayNetworking.canSend(player, MarketplaceDataPayload.ID)) {
            ServerPlayNetworking.send(player, new MarketplaceDataPayload(trades.toString()));
        }
    }

    public static void openCreationMenu(ServerPlayerEntity player) {
        player.openHandledScreen(new net.minecraft.screen.SimpleNamedScreenHandlerFactory((syncId, inv, p) -> 
            new MarketplaceCreationScreenHandler(syncId, inv), 
            Text.of("§2Configurar Nueva Oferta")));
    }

    public static void handlePublishTrade(ServerPlayerEntity player, String title) {
        if (!(player.currentScreenHandler instanceof MarketplaceCreationScreenHandler handler)) return;
        
        Inventory inv = handler.getTradeInventory();
        com.google.gson.JsonArray sellingArray = new com.google.gson.JsonArray();
        com.google.gson.JsonArray askingArray = new com.google.gson.JsonArray();

        for (int i = 0; i < 9; i++) {
            ItemStack stack = inv.getStack(i);
            if (!stack.isEmpty()) sellingArray.add(serializeItemStack(stack));
        }
        for (int i = 9; i < 18; i++) {
            ItemStack stack = inv.getStack(i);
            if (!stack.isEmpty()) askingArray.add(serializeItemStack(stack));
        }

        if (sellingArray.size() == 0 || askingArray.size() == 0) {
            player.sendMessage(Text.of("§c[!] Debes poner qué ofreces y qué pides."), false);
            return;
        }
        
        TradeClient.publishTrade(
            player.getUuidAsString(),
            player.getName().getString(),
            title,
            sellingArray,
            askingArray
        ).thenAccept(success -> {
            MineCore.sync(() -> {
                if (success) {
                    for (int i = 0; i < 9; i++) inv.setStack(i, ItemStack.EMPTY);
                    player.closeHandledScreen();
                    player.sendMessage(Text.of("§6[Market] §a¡Oferta publicada exitosamente!"), false);
                } else {
                    player.sendMessage(Text.of("§c[Market] Error al publicar."), false);
                }
            });
        });
    }

    public static void openTransactionMenu(ServerPlayerEntity player, int tradeId) {
        MineCore.Data.borrow(TradeClient.getOpenTrades(), trades -> {
            JsonObject targetTrade = null;
            for (int i = 0; i < trades.size(); i++) {
                if (trades.get(i).getAsJsonObject().get("id").getAsInt() == tradeId) {
                    targetTrade = trades.get(i).getAsJsonObject();
                    break;
                }
            }

            if (targetTrade == null) {
                player.sendMessage(Text.of("§cEste trade ya no está disponible."), false);
                return;
            }

            java.util.List<ItemStack> requirements = new java.util.ArrayList<>();
            com.google.gson.JsonArray reqArray = new com.google.gson.JsonArray();
            com.google.gson.JsonElement asking = targetTrade.get("asking");
            
            if (asking.isJsonArray()) {
                for (com.google.gson.JsonElement e : asking.getAsJsonArray()) {
                    requirements.add(parseItemStack(e.getAsJsonObject()));
                    reqArray.add(e);
                }
            } else {
                requirements.add(parseItemStack(asking.getAsJsonObject()));
                reqArray.add(asking);
            }

            final java.util.List<ItemStack> finalReqs = requirements;
            final String jsonReqs = reqArray.toString();

            player.openHandledScreen(new net.fabricmc.fabric.api.screenhandler.v1.ExtendedScreenHandlerFactory<TransactionScreenDataPayload>() {
                @Override public TransactionScreenDataPayload getScreenOpeningData(ServerPlayerEntity p) { return new TransactionScreenDataPayload(tradeId, jsonReqs); }
                @Override public Text getDisplayName() { return Text.of("§6§lTRUEQUE EN PROGRESO"); }
                @Override public net.minecraft.screen.ScreenHandler createMenu(int syncId, PlayerInventory inv, PlayerEntity p) {
                    return new MarketplaceTransactionScreenHandler(syncId, inv, tradeId, finalReqs);
                }
            });
        });
    }

    public static void completeTradeOnServer(ServerPlayerEntity player, int tradeId) {
        if (!(player.currentScreenHandler instanceof MarketplaceTransactionScreenHandler handler)) return;
        if (handler.getTradeId() != tradeId) return;

        MineCore.Data.borrow(TradeClient.getOpenTrades(), trades -> {
            JsonObject targetTrade = null;
            for (int i = 0; i < trades.size(); i++) {
                if (trades.get(i).getAsJsonObject().get("id").getAsInt() == tradeId) {
                    targetTrade = trades.get(i).getAsJsonObject();
                    break;
                }
            }

            if (targetTrade == null) {
                player.sendMessage(Text.of("§cTrade no disponible."), false);
                player.closeHandledScreen();
                return;
            }

            final JsonObject finalTrade = targetTrade;
            MineCore.Data.borrow(TradeClient.completeTrade(tradeId, player.getUuidAsString(), player.getName().getString()), success -> {
                if (success) {
                    // Entrega asíncrona de recompensa
                    ItemStack reward = parseItemStack(finalTrade.getAsJsonObject("selling"));
                    player.getInventory().offerOrDrop(reward);
                    player.sendMessage(Text.of("§a¡Trato completado!"), false);
                    player.closeHandledScreen();
                }
            });
        });
    }

    public static void deleteTrade(ServerPlayerEntity player, int tradeId) {
        MineCore.Data.borrow(TradeClient.getOpenTrades(), trades -> {
            JsonObject targetTrade = null;
            for (int i = 0; i < trades.size(); i++) {
                if (trades.get(i).getAsJsonObject().get("id").getAsInt() == tradeId) {
                    targetTrade = trades.get(i).getAsJsonObject();
                    break;
                }
            }

            if (targetTrade != null && targetTrade.get("seller_uuid").getAsString().equals(player.getUuidAsString())) {
                final JsonObject finalTrade = targetTrade;
                MineCore.Data.borrow(TradeClient.cancelTrade(tradeId), success -> {
                    if (success) {
                        player.getInventory().offerOrDrop(parseItemStack(finalTrade.getAsJsonObject("selling")));
                        player.sendMessage(Text.of("§cPublicación eliminada y objetos devueltos."), false);
                    }
                });
            }
        });
    }

    private static JsonObject serializeItemStack(ItemStack stack) {
        JsonObject json = new JsonObject();
        json.addProperty("id", Registries.ITEM.getId(stack.getItem()).toString());
        json.addProperty("count", stack.getCount());
        return json;
    }

    private static ItemStack parseItemStack(JsonObject json) {
        try {
            return new ItemStack(Registries.ITEM.get(Identifier.of(json.get("id").getAsString())), json.get("count").getAsInt());
        } catch (Exception e) { return ItemStack.EMPTY; }
    }
}
