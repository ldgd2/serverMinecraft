package com.lider.minebridge.events.special;

import com.lider.minebridge.networking.AchievementClient;
import net.minecraft.server.network.ServerPlayerEntity;
import net.minecraft.world.World;

import java.util.concurrent.ConcurrentHashMap;

/**
 * MemeLogic — Detectores de logros especiales/memes.
 * TODOS son event-driven ahora. Se eliminó el ServerTickEvents que corría cada 5 segundos.
 * Cada método se llama desde el evento apropiado (mixin, callback, etc.)
 */
public class MemeLogic {

    // Flags de sesión — se limpia al desconectarse el jugador
    private static final java.util.Set<String> sessionUnlocked = ConcurrentHashMap.newKeySet();

    /** Llamado cuando el jugador obtiene el efecto de oscuridad del Warden. */
    public static void onWardenDarknessApplied(ServerPlayerEntity player) {
        String uuid = player.getUuidAsString();
        if (sessionUnlocked.add(uuid + "_darkness")) {
            AchievementClient.sendEvent(uuid, "FEAR_PARALYSIS", 1);
        }
    }

    /** Llamado cuando el jugador llega a Y >= 319. */
    public static void onMaxHeightReached(ServerPlayerEntity player) {
        String uuid = player.getUuidAsString();
        if (sessionUnlocked.add(uuid + "_height")) {
            AchievementClient.sendEvent(uuid, "EVEREST", 1);
        }
    }

    /** Llamado cuando el jugador tiene 10+ efectos activos simultáneamente. */
    public static void onManyEffectsActive(ServerPlayerEntity player) {
        String uuid = player.getUuidAsString();
        if (sessionUnlocked.add(uuid + "_pharmacy")) {
            AchievementClient.sendEvent(uuid, "MANY_EFFECTS", 1);
        }
    }

    /** Llamado al explotar una cama en el Nether. */
    public static void onNetherBedExplosion(ServerPlayerEntity player) {
        if (player.getWorld().getRegistryKey() == World.NETHER) {
            AchievementClient.sendEvent(player.getUuidAsString(), "NETHER_SLEEP", 1);
        }
    }

    /** Llamado cuando el jugador recibe daño sin armadura. */
    public static void onAttackedWithoutArmor(ServerPlayerEntity player) {
        boolean hasArmor = false;
        for (net.minecraft.item.ItemStack armor : player.getInventory().armor) {
            if (!armor.isEmpty()) { hasArmor = true; break; }
        }
        if (!hasArmor) {
            AchievementClient.sendEvent(player.getUuidAsString(), "MEME_POV_VILLAGER", 1);
        }
    }

    /** Llamado cuando el jugador tira 64+ diamantes al suelo. */
    public static void onItemDropped(ServerPlayerEntity player, net.minecraft.item.ItemStack stack) {
        if (stack.getItem().getTranslationKey().contains("diamond") && stack.getCount() >= 64) {
            AchievementClient.sendEvent(player.getUuidAsString(), "MEME_HUMILDAD", 1);
        }
    }

    /** Llamado cuando el jugador comercia con un Wandering Trader. */
    private static final java.util.concurrent.ConcurrentHashMap<String, Integer> traderTrades = new java.util.concurrent.ConcurrentHashMap<>();
    public static void onWanderingTraderTrade(ServerPlayerEntity player) {
        String uuid = player.getUuidAsString();
        int total = traderTrades.merge(uuid, 1, Integer::sum);
        if (total == 10) AchievementClient.sendEvent(uuid, "TRADER_10", 1);
    }

    /** Llamado cuando el jugador muere en el vacío con el inventario lleno. */
    public static void onVoidDeathCheck(ServerPlayerEntity player) {
        boolean isFull = true;
        for (int i = 0; i < player.getInventory().main.size(); i++) {
            if (player.getInventory().main.get(i).isEmpty()) { isFull = false; break; }
        }
        if (isFull) {
            AchievementClient.sendEvent(player.getUuidAsString(), "MEME_VOID_STARK", 1);
        }
    }

    /** Llamado cuando el jugador tiene pastel en mano y 5+ jugadores cerca. */
    public static void onCakeHeldNearPlayers(ServerPlayerEntity player, int nearbyCount) {
        if (nearbyCount >= 5 && sessionUnlocked.add(player.getUuidAsString() + "_cake")) {
            AchievementClient.sendEvent(player.getUuidAsString(), "MEME_ANTOJEN", 1);
        }
    }

    public static void init() {
        // Todos los detectores son event-driven.
    }
}
