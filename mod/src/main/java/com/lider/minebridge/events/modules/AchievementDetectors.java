package com.lider.minebridge.events.modules;

import com.lider.minebridge.networking.AchievementClient;
import net.fabricmc.fabric.api.event.player.UseEntityCallback;
import net.fabricmc.fabric.api.event.player.UseItemCallback;
import net.fabricmc.fabric.api.event.lifecycle.v1.ServerTickEvents;
import net.minecraft.entity.effect.StatusEffects;
import net.minecraft.entity.passive.SheepEntity;
import net.minecraft.item.ItemStack;
import net.minecraft.server.network.ServerPlayerEntity;
import net.minecraft.util.ActionResult;
import net.minecraft.util.DyeColor;
import net.minecraft.util.TypedActionResult;
import net.minecraft.world.World;

public class AchievementDetectors {

    public static void register() {
        // DETECTOR DE ALTURA Y ESTADO (EVEREST, WARDEN)
        ServerTickEvents.END_SERVER_TICK.register(server -> {
            for (ServerPlayerEntity player : server.getPlayerManager().getPlayerList()) {
                if (player.getY() >= 319) {
                    AchievementClient.sendEvent(player.getUuidAsString(), "max_height_reached", 1);
                }
                if (player.hasStatusEffect(StatusEffects.DARKNESS)) {
                    AchievementClient.sendEvent(player.getUuidAsString(), "warden_darkness_effect", 1);
                }
            }
        });

        // DETECTOR DE INTERACCIONES (OVEJA ROSA)
        UseEntityCallback.EVENT.register((player, world, hand, entity, hitResult) -> {
            if (!world.isClient && entity instanceof SheepEntity sheep && sheep.getColor() == DyeColor.PINK) {
                AchievementClient.sendEvent(player.getUuidAsString(), "pink_sheep_found", 1);
            }
            return ActionResult.PASS;
        });
    }

    public static void onNetherBedExplosion(ServerPlayerEntity player) {
        if (player.getWorld().getRegistryKey() == World.NETHER) {
            AchievementClient.sendEvent(player.getUuidAsString(), "nether_bed_explosion", 1);
        }
    }
}
