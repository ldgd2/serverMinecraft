package com.lider.minebridge.events.items;

import com.lider.minebridge.networking.AchievementClient;
import net.minecraft.item.ItemStack;
import net.minecraft.item.Items;
import net.minecraft.server.network.ServerPlayerEntity;
import net.minecraft.registry.Registries;

import java.util.concurrent.ConcurrentHashMap;

public class ItemLogic {

    private static final ConcurrentHashMap<String, Integer> itemsEnchantedSession = new ConcurrentHashMap<>();
    private static final ConcurrentHashMap<String, Integer> xpSpentSession = new ConcurrentHashMap<>();
    private static final ConcurrentHashMap<String, Integer> anvilUseSession = new ConcurrentHashMap<>();
    private static final ConcurrentHashMap<String, Integer> grindstoneUseSession = new ConcurrentHashMap<>();
    
    // Rastreo de regalos (Humildad)
    private static final ConcurrentHashMap<Integer, String> tossedItems = new ConcurrentHashMap<>();

    public static void onItemAcquired(ServerPlayerEntity player, ItemStack stack) {
        String uuid = player.getUuidAsString();
        String itemId = Registries.ITEM.getId(stack.getItem()).toString();

        // 1. LOGROS DE COLECCIÓN
        if (stack.getItem() == Items.DRAGON_EGG) AchievementClient.sendEvent(uuid, "has_dragon_egg", 1);
        if (stack.getItem() == Items.POISONOUS_POTATO) AchievementClient.sendEvent(uuid, "item_acquired:minecraft:poisonous_potato", 1);
        
        // 2. SUPER POLLO (Stack de 64)
        if (stack.getItem() == Items.COOKED_CHICKEN && stack.getCount() >= 64) {
            AchievementClient.sendEvent(uuid, "cooked_chicken_stack", 1);
        }

        // 3. HUMILDAD (Recoger 64 diamantes tirados por otro)
        if (stack.getItem() == Items.DIAMOND && stack.getCount() >= 64) {
            // Nota: Esta lógica requiere seguimiento del objeto tirado, se puede pulir con eventos de entidad item.
        }
    }

    public static void onItemTossed(ServerPlayerEntity player, ItemStack stack) {
        if (stack.getItem() == Items.DIAMOND && stack.getCount() >= 64) {
            AchievementClient.sendEvent(player.getUuidAsString(), "diamonds_gifted", 1);
        }
    }

    public static void onItemEnchanted(String uuid, int xpLevel) {
        itemsEnchantedSession.merge(uuid, 1, Integer::sum);
        xpSpentSession.merge(uuid, xpLevel, Integer::sum);
        AchievementClient.sendEvent(uuid, "item_enchanted", 1);
    }

    public static void onAnvilUse(String uuid) {
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
        anvilUseSession.remove(uuid);
        grindstoneUseSession.remove(uuid);
    }
}
