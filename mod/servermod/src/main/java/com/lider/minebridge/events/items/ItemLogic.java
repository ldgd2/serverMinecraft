package com.lider.minebridge.events.items;

import com.lider.minebridge.networking.AchievementClient;
import net.minecraft.item.ItemStack;
import net.minecraft.item.Items;
import net.minecraft.server.network.ServerPlayerEntity;
import net.minecraft.registry.Registries;
import net.minecraft.registry.entry.RegistryEntry;
import net.minecraft.enchantment.Enchantment;
import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;

public class ItemLogic {

    private static final ConcurrentHashMap<String, Integer> itemsEnchantedSession = new ConcurrentHashMap<>();
    private static final ConcurrentHashMap<String, Integer> xpSpentSession = new ConcurrentHashMap<>();
    private static final ConcurrentHashMap<String, Integer> anvilUseSession = new ConcurrentHashMap<>();
    private static final ConcurrentHashMap<String, Integer> itemsEnchantedStart = new ConcurrentHashMap<>();

    public static void init() {
        // Inicialización requerida por ServerEvents
    }

    public static void setInitialStats(String uuid, int total) {
        itemsEnchantedStart.put(uuid, total);
    }

    public static void onItemAcquired(ServerPlayerEntity player, ItemStack stack) {
        String uuid = player.getUuidAsString();
        if (stack.getItem() == Items.DRAGON_EGG) AchievementClient.sendEvent(uuid, "has_dragon_egg", 1);
        if (stack.getItem() == Items.POISONOUS_POTATO) AchievementClient.sendEvent(uuid, "item_acquired:minecraft:poisonous_potato", 1);
        if (stack.getItem() == Items.COOKED_CHICKEN && stack.getCount() >= 64) {
            AchievementClient.sendEvent(uuid, "cooked_chicken_stack", 1);
        }
    }

    public static void onItemTossed(ServerPlayerEntity player, ItemStack stack) {
        if (stack.getItem() == Items.DIAMOND && stack.getCount() >= 64) {
            AchievementClient.sendEvent(player.getUuidAsString(), "diamonds_gifted", 1);
        }
    }

    public static void onItemEnchanted(ServerPlayerEntity player, ItemStack stack, int cost, Map<RegistryEntry<Enchantment>, Integer> enchants) {
        String uuid = player.getUuidAsString();
        itemsEnchantedSession.merge(uuid, 1, Integer::sum);
        xpSpentSession.merge(uuid, cost, Integer::sum);
        AchievementClient.sendEvent(uuid, "item_enchanted", 1);
    }

    public static void onPotionBrewed(String uuid, String potionId) {
        AchievementClient.sendEvent(uuid, "potion_brewed", 1);
    }

    public static void onAnvilUse(ServerPlayerEntity player) {
        String uuid = player.getUuidAsString();
        anvilUseSession.merge(uuid, 1, Integer::sum);
        AchievementClient.sendEvent(uuid, "anvil_use", 1);
    }

    public static void onToolBroken(String playerUuid, String itemId) {
        if (itemId.contains("netherite")) {
            AchievementClient.sendEvent(playerUuid, "netherite_tool_broken", 1);
        }
    }

    public static void onPlayerLeave(String uuid) {
        java.util.Map<String, Integer> stats = new java.util.HashMap<>();
        Integer enchanted = itemsEnchantedSession.remove(uuid);
        if (enchanted != null) stats.put("item_enchanted", enchanted);
        Integer xp = xpSpentSession.remove(uuid);
        if (xp != null) stats.put("xp_spent_enchanting", xp);
        if (!stats.isEmpty()) AchievementClient.sendSessionSummary(uuid, stats);
        itemsEnchantedStart.remove(uuid);
        anvilUseSession.remove(uuid);
    }
}
