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

    /** Llamado cuando el jugador obtiene el efecto de oscuridad del Warden (desde mixin de efectos). */
    public static void onWardenDarknessApplied(ServerPlayerEntity player) {
        String uuid = player.getUuidAsString();
        if (sessionUnlocked.add(uuid + "_darkness")) {
            AchievementClient.sendEvent(uuid, "warden_darkness_effect", 1);
        }
    }

    /** Llamado cuando el jugador llega a Y >= 319 (desde AchievementDetectors.onPlayerMove). */
    public static void onMaxHeightReached(ServerPlayerEntity player) {
        String uuid = player.getUuidAsString();
        if (sessionUnlocked.add(uuid + "_height")) {
            AchievementClient.sendEvent(uuid, "max_height_reached", 1);
        }
    }

    /** Llamado cuando el jugador tiene 10+ efectos activos simultáneamente (desde mixin de efectos). */
    public static void onManyEffectsActive(ServerPlayerEntity player) {
        String uuid = player.getUuidAsString();
        if (sessionUnlocked.add(uuid + "_pharmacy")) {
            AchievementClient.sendEvent(uuid, "active_effects_count", 10);
        }
    }

    /** Llamado al explotar una cama en el Nether (desde mixin de cama). */
    public static void onNetherBedExplosion(ServerPlayerEntity player) {
        if (player.getWorld().getRegistryKey() == World.NETHER) {
            AchievementClient.sendEvent(player.getUuidAsString(), "nether_bed_explosion", 1);
        }
    }

    /** Llamado cuando el jugador recibe daño sin armadura (desde mixin de daño). */
    public static void onAttackedWithoutArmor(ServerPlayerEntity player) {
        boolean hasArmor = false;
        for (net.minecraft.item.ItemStack armor : player.getInventory().armor) {
            if (!armor.isEmpty()) { hasArmor = true; break; }
        }
        if (!hasArmor) {
            AchievementClient.sendEvent(player.getUuidAsString(), "attacked_without_armor", 1);
        }
    }

    /** Llamado cuando el jugador tira 64+ diamantes al suelo. */
    public static void onItemDropped(ServerPlayerEntity player, net.minecraft.item.ItemStack stack) {
        if (stack.getItem().getTranslationKey().contains("diamond") && stack.getCount() >= 64) {
            AchievementClient.sendEvent(player.getUuidAsString(), "diamonds_gifted", 64);
        }
    }

    /** Llamado cuando el jugador comercia con un Wandering Trader. */
    public static void onWanderingTraderTrade(ServerPlayerEntity player) {
        AchievementClient.sendEvent(player.getUuidAsString(), "wandering_trader_trade", 1);
    }

    /** Llamado cuando el jugador muere en el vacío con el inventario lleno. */
    public static void onVoidDeathCheck(ServerPlayerEntity player) {
        boolean isFull = true;
        for (int i = 0; i < player.getInventory().main.size(); i++) {
            if (player.getInventory().main.get(i).isEmpty()) { isFull = false; break; }
        }
        if (isFull) {
            AchievementClient.sendEvent(player.getUuidAsString(), "full_inventory_void_death", 1);
        }
    }

    /**
     * Llamado cuando el jugador tiene pastel en mano y 5+ jugadores cerca.
     * Debe llamarse desde un UseItemCallback (evento puntual), NO desde tick.
     */
    public static void onCakeHeldNearPlayers(ServerPlayerEntity player, int nearbyCount) {
        if (nearbyCount >= 5 && sessionUnlocked.add(player.getUuidAsString() + "_cake")) {
            AchievementClient.sendEvent(player.getUuidAsString(), "hold_cake_near_players", 1);
        }
    }

    /** Limpiar flags al desconectarse. */
    public static void onPlayerLeave(ServerPlayerEntity player) {
        String uuid = player.getUuidAsString();
        sessionUnlocked.removeIf(f -> f.startsWith(uuid));
    }

    // init() ya no registra ningún ServerTickEvents
    public static void init() {
        // Todos los detectores son event-driven.
        // El pastel se detecta en UseItemCallback — ver AchievementDetectors.register()
    }
}
