package com.lider.minebridge.events.economy;

import com.lider.minebridge.networking.AchievementClient;
import net.minecraft.item.ItemStack;
import net.minecraft.item.Items;

public class EconomyLogic {

    public static void init() {
        // Inicialización de listeners de economía
    }

    /**
     * Llamado cuando se completa un trade con un aldeano
     */
    public static void onTradeCompleted(String playerUuid, ItemStack soldItem, ItemStack boughtItem) {
        // Evento genérico de trade
        AchievementClient.sendEvent(playerUuid, "villager_trade", 1);

        // Detectar si se usaron o ganaron esmeraldas
        if (soldItem.getItem() == Items.EMERALD) {
            AchievementClient.sendEvent(playerUuid, "emerald_spent", soldItem.getCount());
        }
        if (boughtItem.getItem() == Items.EMERALD) {
            AchievementClient.sendEvent(playerUuid, "item_acquired:minecraft:emerald", boughtItem.getCount());
        }

        // Objetos de lujo (Faro o Manzana Notch)
        if (boughtItem.getItem() == Items.BEACON || boughtItem.getItem() == Items.ENCHANTED_GOLDEN_APPLE) {
            AchievementClient.sendEvent(playerUuid, "luxury_item_bought", 1);
        }
    }

    public static void onPiglinBarter(String playerUuid) {
        AchievementClient.sendEvent(playerUuid, "piglin_barter", 1);
    }

    /**
     * Llamado cuando el inventario cambia y se detectan esmeraldas (opcional)
     */
    public static void onEmeraldsFound(String playerUuid, int count) {
        AchievementClient.sendEvent(playerUuid, "emerald_balance", count);
        AchievementClient.sendEvent(playerUuid, "item_acquired:minecraft:emerald", count);
    }
}
