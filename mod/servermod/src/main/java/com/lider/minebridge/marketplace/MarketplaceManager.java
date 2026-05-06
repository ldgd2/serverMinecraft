package com.lider.minebridge.marketplace;

import com.google.gson.JsonArray;
import com.google.gson.JsonObject;
import com.lider.minebridge.MineBridge;
import com.lider.minebridge.networking.TradeClient;
import net.minecraft.entity.player.PlayerEntity;
import net.minecraft.entity.player.PlayerInventory;
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
            java.util.List<String> sellerUuids = new java.util.ArrayList<>();
            
            for (int i = 0; i < trades.size(); i++) {
                JsonObject tradeJson = trades.get(i).getAsJsonObject();
                int tradeId = tradeJson.get("id").getAsInt();
                String sellerUuid = tradeJson.get("seller_uuid").getAsString();
                ItemStack selling = parseItemStack(tradeJson.getAsJsonObject("selling"));
                ItemStack asking = parseItemStack(tradeJson.getAsJsonObject("asking"));
                
                if (!selling.isEmpty() && !asking.isEmpty()) {
                    TradeOffer offer = new TradeOffer(new TradedItem(asking.getItem(), asking.getCount()), selling, 1, 0, 0f);
                    
                    String seller = tradeJson.get("seller").getAsString();
                    boolean isSelf = sellerUuid.equals(player.getUuidAsString());
                    String prefix = isSelf ? "§a[TUYA] " : "§e";
                    
                    selling.set(net.minecraft.component.DataComponentTypes.CUSTOM_NAME, Text.of(prefix + selling.getName().getString() + " §7(de " + seller + ")"));
                    if (isSelf) {
                        java.util.List<Text> lore = new java.util.ArrayList<>();
                        lore.add(Text.of("§cClick para ELIMINAR publicación"));
                        selling.set(net.minecraft.component.DataComponentTypes.LORE, new net.minecraft.component.type.LoreComponent(lore));
                    }

                    offers.add(offer);
                    tradeIds.add(tradeId);
                    sellerUuids.add(sellerUuid);
                }
            }

            if (offers.isEmpty()) {
                player.sendMessage(Text.of("§cMarketplace vacío por ahora."), false);
                // Aún así abrimos para que puedan ver el "perfil" o algo? No, mejor no.
            }

            SimpleMerchant merchant = new SimpleMerchant(player, tradeIds, sellerUuids);
            merchant.setOffers(offers);
            player.openHandledScreen(new SimpleNamedScreenHandlerFactory((syncId, inv, p) -> 
                new net.minecraft.screen.MerchantScreenHandler(syncId, inv, merchant), 
                Text.of("§6Marketplace Global")));
        });
    }

    public static void openCreationMenu(ServerPlayerEntity player) {
        player.openHandledScreen(new SimpleNamedScreenHandlerFactory((syncId, inv, p) -> 
            new MarketplaceCreationScreenHandler(syncId, inv), 
            Text.of("§2Configurar Nueva Oferta")));
    }

    public static void openTransactionMenu(ServerPlayerEntity player, int tradeId) {
        player.openHandledScreen(new net.fabricmc.fabric.api.screenhandler.v1.ExtendedScreenHandlerFactory<com.lider.minebridge.networking.payload.TransactionScreenDataPayload>() {
            @Override
            public com.lider.minebridge.networking.payload.TransactionScreenDataPayload getScreenOpeningData(ServerPlayerEntity player) {
                return new com.lider.minebridge.networking.payload.TransactionScreenDataPayload(tradeId);
            }

            @Override
            public Text getDisplayName() {
                return Text.of("§6Trueque en Progreso");
            }

            @Override
            public net.minecraft.screen.ScreenHandler createMenu(int syncId, PlayerInventory inv, PlayerEntity player) {
                return new MarketplaceTransactionScreenHandler(syncId, inv, tradeId);
            }
        });
    }

    public static void completeTradeOnServer(ServerPlayerEntity player, int tradeId) {
        if (!(player.currentScreenHandler instanceof MarketplaceTransactionScreenHandler handler)) return;
        if (handler.getTradeId() != tradeId) return;

        Inventory paymentInv = handler.getInventory();
        ItemStack payment = paymentInv.getStack(0);

        if (payment.isEmpty()) {
            player.sendMessage(Text.of("§cNo hay pago en el slot."), false);
            return;
        }

        // Obtener detalles del trade desde el backend para verificar
        com.lider.minebridge.networking.TradeClient.getOpenTrades().thenAccept(trades -> {
            MineBridge.getServer().execute(() -> {
                JsonObject targetTrade = null;
                for (int i = 0; i < trades.size(); i++) {
                    if (trades.get(i).getAsJsonObject().get("id").getAsInt() == tradeId) {
                        targetTrade = trades.get(i).getAsJsonObject();
                        break;
                    }
                }

                if (targetTrade == null) {
                    player.sendMessage(Text.of("§cEste trade ya no está disponible."), false);
                    player.playSound(net.minecraft.sound.SoundEvents.ENTITY_VILLAGER_NO, 1.0f, 1.0f);
                    player.closeHandledScreen();
                    return;
                }

                final JsonObject finalTargetTrade = targetTrade;

                // Obtener requerimientos (puede ser un objeto único o un array)
                com.google.gson.JsonElement askingElement = finalTargetTrade.get("asking");
                java.util.List<ItemStack> requirements = new java.util.ArrayList<>();
                
                if (askingElement.isJsonArray()) {
                    JsonArray array = askingElement.getAsJsonArray();
                    for (int i = 0; i < array.size(); i++) {
                        requirements.add(parseItemStack(array.get(i).getAsJsonObject()));
                    }
                } else {
                    requirements.add(parseItemStack(askingElement.getAsJsonObject()));
                }

                // Verificar que el pago en los slots coincida con los requerimientos
                // Usamos una copia del inventario de pago para validar sin afectar hasta estar seguros
                boolean[] requirementMet = new boolean[requirements.size()];
                int[] slotUsedForRequirement = new int[requirements.size()];
                java.util.Arrays.fill(slotUsedForRequirement, -1);

                for (int r = 0; r < requirements.size(); r++) {
                    ItemStack req = requirements.get(r);
                    for (int s = 0; s < paymentInv.size(); s++) {
                        ItemStack slotStack = paymentInv.getStack(s);
                        if (!slotStack.isEmpty() && slotStack.getItem() == req.getItem() && slotStack.getCount() >= req.getCount()) {
                            requirementMet[r] = true;
                            slotUsedForRequirement[r] = s;
                            break;
                        }
                    }
                }

                for (boolean met : requirementMet) {
                    if (!met) {
                        player.sendMessage(Text.of("§cNo has puesto los objetos requeridos o la cantidad exacta en los slots."), false);
                        player.playSound(net.minecraft.sound.SoundEvents.ENTITY_VILLAGER_NO, 1.0f, 1.0f);
                        return;
                    }
                }

                // SI TODO ESTÁ BIEN: Cobrar cantidades exactas
                for (int r = 0; r < requirements.size(); r++) {
                    int slotIdx = slotUsedForRequirement[r];
                    paymentInv.getStack(slotIdx).decrement(requirements.get(r).getCount());
                }
                paymentInv.markDirty();

                // Notificar al backend
                com.lider.minebridge.networking.TradeClient.completeTradeSecurely(tradeId, player.getUuidAsString(), player.getName().getString())
                    .thenAccept(success -> {
                        MineBridge.getServer().execute(() -> {
                            if (success) {
                                // Dar recompensa al comprador
                                JsonObject sellingJson = finalTargetTrade.getAsJsonObject("selling");
                                ItemStack reward = parseItemStack(sellingJson);
                                player.getInventory().offerOrDrop(reward);
                                
                                player.sendMessage(Text.of("§6[Market] §a¡Trato completado con éxito!"), false);
                                player.playSound(net.minecraft.sound.SoundEvents.ENTITY_VILLAGER_YES, 1.0f, 1.0f);
                                player.networkHandler.sendPacket(new net.minecraft.network.packet.s2c.play.TitleS2CPacket(Text.of("§a§lTRATO CERRADO")));
                                player.closeHandledScreen();
                            } else {
                                player.sendMessage(Text.of("§cError al sincronizar con el servidor central."), false);
                                player.playSound(net.minecraft.sound.SoundEvents.ENTITY_VILLAGER_NO, 1.0f, 1.0f);
                            }
                        });
                    });
            });
        });
    }

    public static void deleteTrade(ServerPlayerEntity player, int tradeId) {
        TradeClient.cancelTrade(tradeId);
        player.sendMessage(Text.of("§6[Market] §cPublicación eliminada."), false);
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
        private final java.util.List<String> sellerUuids;
        private TradeOfferList offers = new TradeOfferList();

        public SimpleMerchant(PlayerEntity customer, java.util.List<Integer> tradeIds, java.util.List<String> sellerUuids) {
            this.customer = customer;
            this.tradeIds = tradeIds;
            this.sellerUuids = sellerUuids;
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
                    String sellerUuid = sellerUuids.get(i);
                    
                    if (sellerUuid.equals(customer.getUuidAsString())) {
                        deleteTrade((ServerPlayerEntity) customer, tradeId);
                        ((ServerPlayerEntity) customer).closeHandledScreen();
                    } else {
                        TradeClient.completeTrade(tradeId, customer.getUuidAsString(), customer.getName().getString());
                    }
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
