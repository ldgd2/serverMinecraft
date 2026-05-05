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
import org.jetbrains.annotations.Nullable;

import java.util.Optional;

public class MarketplaceManager {

    public static void openMarketplace(ServerPlayerEntity player, JsonArray trades) {
        MineBridge.getServer().execute(() -> {
            TradeOfferList offers = new TradeOfferList();
            for (int i = 0; i < trades.size(); i++) {
                JsonObject tradeJson = trades.get(i).getAsJsonObject();
                ItemStack selling = parseItemStack(tradeJson.getAsJsonObject("selling"));
                ItemStack asking = parseItemStack(tradeJson.getAsJsonObject("asking"));
                
                if (!selling.isEmpty() && !asking.isEmpty()) {
                    offers.add(new TradeOffer(asking, selling, 1, 0, 0));
                }
            }

            if (offers.isEmpty()) {
                player.sendMessage(Text.of("§cMarketplace vacío por ahora."), false);
                return;
            }

            SimpleMerchant merchant = new SimpleMerchant(player);
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

    /** Un mercante virtual simple para la UI */
    private static class SimpleMerchant implements Merchant {
        private final PlayerEntity customer;
        private TradeOfferList offers = new TradeOfferList();

        public SimpleMerchant(PlayerEntity customer) {
            this.customer = customer;
        }

        @Override public void setCustomer(@Nullable PlayerEntity customer) {}
        @Override public @Nullable PlayerEntity getCustomer() { return customer; }
        @Override public TradeOfferList getOffers() { return offers; }
        public void setOffers(TradeOfferList offers) { this.offers = offers; }
        @Override public void trade(TradeOffer offer) {
            // Aquí es donde se completa el trato
            // Debemos notificar al backend que este tradeID se ha completado
            // Pero TradeOffer no guarda el ID de nuestra DB. 
            // Podríamos usar el NBT del item o un mapa.
        }
        @Override public void setOffersFromServer(TradeOfferList offers) {}
        @Override public void onBridgeOffers(TradeOfferList offers) {}
        @Override public boolean isClient() { return false; }
        @Override public int getExperience() { return 0; }
        @Override public void setExperienceFromServer(int experience) {}
        @Override public boolean isLevelingMerchant() { return false; }
        @Override public net.minecraft.sound.SoundEvent getYesSound() { return net.minecraft.sound.SoundEvents.ENTITY_VILLAGER_YES; }
    }
}
