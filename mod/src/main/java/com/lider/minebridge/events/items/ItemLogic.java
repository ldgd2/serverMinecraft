package com.lider.minebridge.events.items;

import com.lider.minebridge.networking.AchievementClient;
import net.fabricmc.fabric.api.event.player.UseItemCallback;
import net.minecraft.enchantment.Enchantment;
import net.minecraft.item.ItemStack;
import net.minecraft.item.Items;
import net.minecraft.registry.Registries;
import net.minecraft.server.network.ServerPlayerEntity;
import net.minecraft.util.TypedActionResult;
import java.util.List;
import java.util.Map;

public class ItemLogic {

    public static void init() {
        UseItemCallback.EVENT.register((player, world, hand) -> {
            ItemStack stack = player.getStackInHand(hand);
            if (!world.isClient) {
                // Lógica de comida "edgy"
                if (stack.getItem() == Items.COOKED_BEEF) {
                    List<ServerPlayerEntity> nearby = world.getEntitiesByClass(ServerPlayerEntity.class, player.getBoundingBox().expand(8.0), p -> p != player);
                    if (!nearby.isEmpty()) AchievementClient.sendEvent(player.getUuidAsString(), "eat_steak_near_player", 1);
                }

                // Lógica de acumuladores (Pollo Campero)
                if (stack.getItem() == Items.COOKED_CHICKEN && stack.getCount() >= 64) {
                    AchievementClient.sendEvent(player.getUuidAsString(), "cooked_chicken_stack", 1);
                }
            }
            return TypedActionResult.pass(stack);
        });
    }

    public static void onPotionBrewed(String playerUuid, String potionId) {
        AchievementClient.sendEvent(playerUuid, "potion_brewed:" + potionId, 1);
        AchievementClient.sendEvent(playerUuid, "total_potions_brewed", 1);
    }

    public static void onItemEnchanted(ServerPlayerEntity player, ItemStack stack, int levelCost, Map<net.minecraft.registry.entry.RegistryEntry<Enchantment>, Integer> enchantments) {
        AchievementClient.sendEvent(player.getUuidAsString(), "item_enchanted", 1);
        AchievementClient.sendEvent(player.getUuidAsString(), "xp_spent_enchanting", levelCost);
        
        if (levelCost >= 30) {
            AchievementClient.sendEvent(player.getUuidAsString(), "level_30_enchant", 1);
        }

        int totalEnchants = 0;
        for (Map.Entry<net.minecraft.registry.entry.RegistryEntry<Enchantment>, Integer> entry : enchantments.entrySet()) {
            String name = entry.getKey().getKey().get().getValue().getPath();
            int level = entry.getValue();
            
            AchievementClient.sendEvent(player.getUuidAsString(), "enchant:" + name + ":" + level, 1);
            AchievementClient.sendEvent(player.getUuidAsString(), "enchant:" + name, 1);
            totalEnchants++;
        }

        if (totalEnchants >= 7) {
            AchievementClient.sendEvent(player.getUuidAsString(), "maxed_item_enchanted", 1);
        }

        if (stack.getItem() instanceof net.minecraft.item.BookItem || stack.getItem() instanceof net.minecraft.item.EnchantedBookItem) {
            AchievementClient.sendEvent(player.getUuidAsString(), "enchant:book", 1);
        }
    }

    public static void onAnvilUse(ServerPlayerEntity player) {
        AchievementClient.sendEvent(player.getUuidAsString(), "anvil_use", 1);
    }

    public static void onGrindstoneUse(ServerPlayerEntity player) {
        AchievementClient.sendEvent(player.getUuidAsString(), "grindstone_use", 1);
    }

    public static void onLegendaryItemAcquired(String playerUuid, String itemId) {
        AchievementClient.sendEvent(playerUuid, "item_acquired:" + itemId, 1);
        if (itemId.contains("beacon") || itemId.contains("enchanted_golden_apple") || itemId.contains("nether_star")) {
            AchievementClient.sendEvent(playerUuid, "luxury_item_bought", 1);
        }
    }
}
