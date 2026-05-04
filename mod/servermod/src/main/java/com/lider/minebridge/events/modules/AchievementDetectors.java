package com.lider.minebridge.events.modules;

import com.lider.minebridge.events.special.MemeLogic;
import com.lider.minebridge.networking.AchievementClient;
import net.fabricmc.fabric.api.event.player.UseEntityCallback;
import net.fabricmc.fabric.api.event.player.UseItemCallback;
import net.minecraft.entity.passive.SheepEntity;
import net.minecraft.entity.passive.TameableEntity;
import net.minecraft.entity.passive.WolfEntity;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.network.ServerPlayerEntity;
import net.minecraft.util.ActionResult;
import net.minecraft.util.DyeColor;
import net.minecraft.util.TypedActionResult;
import net.minecraft.registry.Registries;
import net.minecraft.entity.effect.StatusEffectInstance;

import java.time.LocalTime;
import java.util.List;
import java.util.Set;
import java.util.concurrent.ConcurrentHashMap;

public class AchievementDetectors {

    private static final ConcurrentHashMap<String, Long> lastMoveTime = new ConcurrentHashMap<>();

    public static void onPlayerMove(ServerPlayerEntity player) {
        // Altura (Logro Everest) - Solo si supera el límite de construcción
        if (player.getY() >= 315) {
            com.lider.minebridge.events.special.MemeLogic.onMaxHeightReached(player);
        }
    }

    public static void onPlayerLeave(ServerPlayerEntity player) {
        String uuid = player.getUuidAsString();
        lastMoveTime.remove(uuid);
        // Se eliminó el resumen de sesión para ahorrar recursos, 
        // ya que los logros importantes se envían en tiempo real.
    }

    public static void onAnimalTamed(ServerPlayerEntity player, TameableEntity animal) {
        String uuid = player.getUuidAsString();
        String type = Registries.ENTITY_TYPE.getId(animal.getType()).getPath();
        if (type.contains("wolf")) {
            AchievementClient.sendEvent(uuid, "tame_wolf", 1);
        }
    }

    public static void onPlayerSleep(ServerPlayerEntity player) {
        String uuid = player.getUuidAsString();
        if (player.hasStatusEffect(net.minecraft.entity.effect.StatusEffects.BAD_OMEN)) {
            AchievementClient.sendEvent(uuid, "sleep_with_bad_omen", 1);
        }
    }

    public static void register() {
        UseEntityCallback.EVENT.register((player, world, hand, entity, hitResult) -> {
            if (!world.isClient && player instanceof ServerPlayerEntity serverPlayer) {
                String uuid = serverPlayer.getUuidAsString();
                if (entity instanceof SheepEntity sheep && sheep.getColor() == DyeColor.PINK) {
                    AchievementClient.sendEvent(uuid, "pink_sheep_found", 1);
                }
                if (Registries.ENTITY_TYPE.getId(entity.getType()).getPath().contains("wandering_trader")) {
                    AchievementClient.sendEvent(uuid, "wandering_trader_trade", 1);
                }
            }
            return ActionResult.PASS;
        });

        UseItemCallback.EVENT.register((player, world, hand) -> {
            if (!world.isClient && player instanceof ServerPlayerEntity serverPlayer) {
                net.minecraft.item.ItemStack stack = player.getStackInHand(hand);
                if (stack.getItem().getTranslationKey().contains("cake")) {
                    MinecraftServer server = serverPlayer.getServer();
                    if (server != null) {
                        int nearbyCount = (int) server.getPlayerManager().getPlayerList().stream()
                            .filter(p -> p != serverPlayer && p.getPos().distanceTo(serverPlayer.getPos()) < 8.0).count();
                        if (nearbyCount >= 5) AchievementClient.sendEvent(serverPlayer.getUuidAsString(), "hold_cake_near_players", 1);
                    }
                }
            }
            return TypedActionResult.pass(player.getStackInHand(hand));
        });
    }
}
