package com.lider.minebridge.events.special;

import com.lider.minebridge.networking.AchievementClient;
import net.fabricmc.fabric.api.event.lifecycle.v1.ServerTickEvents;
import net.minecraft.entity.effect.StatusEffects;
import net.minecraft.server.network.ServerPlayerEntity;
import net.minecraft.world.World;

public class MemeLogic {

    private static int tickCounter = 0;
    private static final java.util.Set<String> sessionUnlocked = java.util.concurrent.ConcurrentHashMap.newKeySet();

    public static void init() {
        ServerTickEvents.END_SERVER_TICK.register(server -> {
            tickCounter++;
            if (tickCounter < 100) return; // Solo revisar cada 5 segundos
            tickCounter = 0;

            for (ServerPlayerEntity player : server.getPlayerManager().getPlayerList()) {
                String uuid = player.getUuidAsString();
                
                // 1. EL MONTE EVEREST (Altura 320)
                if (player.getY() >= 319 && sessionUnlocked.add(uuid + "_height")) {
                    AchievementClient.sendEvent(player.getUuidAsString(), "max_height_reached", 1);
                }

                // 2. PARALISIS DEL MIEDO (Warden)
                if (player.hasStatusEffect(StatusEffects.DARKNESS) && sessionUnlocked.add(uuid + "_darkness")) {
                    AchievementClient.sendEvent(uuid, "warden_darkness_effect", 1);
                }

                // 3. FARMACIA ANDANTE (10 efectos activos)
                if (player.getStatusEffects().size() >= 10 && sessionUnlocked.add(uuid + "_pharmacy")) {
                    AchievementClient.sendEvent(uuid, "active_effects_count", 10);
                }

                // 4. DISTANCIA MONTADO (General y Strider)
                if (player.getVehicle() != null) {
                    AchievementClient.sendEvent(uuid, "distance_mounted", 100); // 100 ticks
                    if (player.getVehicle().getType().getTranslationKey().contains("strider") && player.getVehicle().isInLava()) {
                        AchievementClient.sendEvent(uuid, "strider_lava_distance", 100);
                    }
                }

                // 5. NO ANTOJEN (Pastel + 5 jugadores cerca)
                if (player.getStackInHand(net.minecraft.util.Hand.MAIN_HAND).getItem().getTranslationKey().contains("cake")) {
                    int count = server.getPlayerManager().getPlayerList().stream()
                        .filter(p -> p != player && p.getPos().distanceTo(player.getPos()) < 8.0)
                        .collect(java.util.stream.Collectors.toList()).size();
                    if (count >= 5 && sessionUnlocked.add(uuid + "_cake")) {
                        AchievementClient.sendEvent(uuid, "hold_cake_near_players", 1);
                    }
                }
            }
        });
    }

    public static void onNetherBedExplosion(ServerPlayerEntity player) {
        AchievementClient.sendEvent(player.getUuidAsString(), "nether_bed_explosion", 1);
    }

    public static void onAttackedWithoutArmor(ServerPlayerEntity player) {
        boolean hasArmor = false;
        for (net.minecraft.item.ItemStack armor : player.getInventory().armor) {
            if (!armor.isEmpty()) {
                hasArmor = true;
                break;
            }
        }
        if (!hasArmor) {
            AchievementClient.sendEvent(player.getUuidAsString(), "attacked_without_armor", 1);
        }
    }

    public static void onItemDropped(ServerPlayerEntity player, net.minecraft.item.ItemStack stack) {
        // HUMILDAD (Regalar 64 diamantes)
        if (stack.getItem().getTranslationKey().contains("diamond") && stack.getCount() >= 64) {
            AchievementClient.sendEvent(player.getUuidAsString(), "diamonds_gifted", 64);
        }
    }

    public static void onWanderingTraderTrade(ServerPlayerEntity player) {
        AchievementClient.sendEvent(player.getUuidAsString(), "wandering_trader_trade", 1);
    }

    public static void onVoidDeathCheck(ServerPlayerEntity player) {
        // MEME_VOID_STARK (Muerte al vacío con inventario lleno)
        boolean isFull = true;
        for (int i = 0; i < player.getInventory().main.size(); i++) {
            if (player.getInventory().main.get(i).isEmpty()) {
                isFull = false;
                break;
            }
        }
        if (isFull) {
            AchievementClient.sendEvent(player.getUuidAsString(), "full_inventory_void_death", 1);
        }
    }
}
