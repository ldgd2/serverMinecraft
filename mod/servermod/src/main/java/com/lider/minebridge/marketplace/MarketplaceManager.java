package com.lider.minebridge.marketplace;

import com.google.gson.JsonArray;
import com.google.gson.JsonObject;
import com.lider.minebridge.MineBridge;
import com.lider.minebridge.networking.TradeClient;
import net.minecraft.entity.player.PlayerEntity;
import net.minecraft.inventory.Inventory;
import net.minecraft.item.Item;
import net.minecraft.item.ItemStack;
import net.minecraft.registry.Registries;
import net.minecraft.screen.SimpleNamedScreenHandlerFactory;
import net.minecraft.server.network.ServerPlayerEntity;
import net.minecraft.text.Text;
import net.minecraft.util.Identifier;
import net.minecraft.village.Merchant;
import net.minecraft.village.MerchantInventory;
import net.minecraft.village.TradeOffer;
import net.minecraft.village.TradeOfferList;
import net.minecraft.village.TradedItem;
import org.jetbrains.annotations.Nullable;

import java.util.Optional;

public class MarketplaceManager {
    public static void openMarketplace(ServerPlayerEntity player, JsonArray trades) {
        MineBridge.getServer().execute(() -> {
            TradeOfferList offers = new TradeOfferList();
            java.util.List<Integer> tradeIds = new java.util.ArrayList<>();
            
            for (int i = 0; i < trades.size(); i++) {
                JsonObject tradeJson = trades.get(i).getAsJsonObject();
                int tradeId = tradeJson.get("id").getAsInt();
                ItemStack selling = parseItemStack(tradeJson.getAsJsonObject("selling"));
                ItemStack asking = parseItemStack(tradeJson.getAsJsonObject("asking"));
                
                if (!selling.isEmpty() && !asking.isEmpty()) {
                    offers.add(new TradeOffer(new TradedItem(asking.getItem(), asking.getCount()), selling, 1, 0, 0f));
                    tradeIds.add(tradeId);
                }
            }

            if (offers.isEmpty()) {
                player.sendMessage(Text.of("§cMarketplace vacío por ahora."), false);
                return;
            }

            SimpleMerchant merchant = new SimpleMerchant(player, tradeIds);
            merchant.setOffers(offers);
            player.openHandledScreen(new SimpleNamedScreenHandlerFactory((syncId, inv, p) -> 
                new net.minecraft.screen.MerchantScreenHandler(syncId, inv, merchant), 
                Text.of("§6Marketplace Global")));
        });
    }

    private static ItemStack parseItemStack(JsonObject json) {
        try {
            String id = json.get("id").getAsString();
            int count = json.get("count").getAsInt();
            Item item = Registries.ITEM.get(Identifier.of(id));
            return new ItemStack(item, count);
        } catch (Exception e) {
            return ItemStack.EMPTY;
        }
    }

    private static class SimpleMerchant implements Merchant {
        private final PlayerEntity customer;
        private final java.util.List<Integer> tradeIds;
        private TradeOfferList offers = new TradeOfferList();

        public SimpleMerchant(PlayerEntity customer, java.util.List<Integer> tradeIds) {
            this.customer = customer;
            this.tradeIds = tradeIds;
        }

        @Override public void setCustomer(@Nullable PlayerEntity customer) {}
        @Override public @Nullable PlayerEntity getCustomer() { return customer; }
        @Override public TradeOfferList getOffers() { return offers; }
        public void setOffers(TradeOfferList offers) { this.offers = offers; }
        
        @Override public void trade(TradeOffer offer) {
            // Buscar qué tradeID corresponde a esta oferta
            for (int i = 0; i < offers.size(); i++) {
                if (offers.get(i) == offer && i < tradeIds.size()) {
                    int tradeId = tradeIds.get(i);
                    TradeClient.completeTrade(tradeId, customer.getUuidAsString(), customer.getName().getString());
                    break;
                }
            }
        }

        @Override public void setOffersFromServer(TradeOfferList offers) {}
        @Override public boolean isClient() { return false; }
        @Override public int getExperience() { return 0; }
        @Override public void setExperienceFromServer(int experience) {}
        @Override public boolean isLeveledMerchant() { return false; }
        @Override public void onSellingItem(ItemStack stack) {}
        @Override public net.minecraft.sound.SoundEvent getYesSound() { return net.minecraft.sound.SoundEvents.ENTITY_VILLAGER_YES; }
    }
}
