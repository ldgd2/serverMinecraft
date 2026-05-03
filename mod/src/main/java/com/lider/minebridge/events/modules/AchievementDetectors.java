package com.lider.minebridge.events.modules;

import com.lider.minebridge.networking.AchievementClient;
import net.fabricmc.fabric.api.event.player.UseEntityCallback;
import net.minecraft.entity.effect.StatusEffects;
import net.minecraft.entity.passive.SheepEntity;
import net.minecraft.server.network.ServerPlayerEntity;
import net.minecraft.util.ActionResult;
import net.minecraft.util.DyeColor;
import net.minecraft.world.World;

import java.util.concurrent.ConcurrentHashMap;

public class AchievementDetectors {

    // Tracking por sesión para no repetir eventos "de estado"
    private static final java.util.Set<String> sessionFlags = ConcurrentHashMap.newKeySet();

    // Última posición registrada por jugador para calcular distancia y detectar alturas
    private static final ConcurrentHashMap<String, double[]> lastPos = new ConcurrentHashMap<>();

    /**
     * Llamado desde PlayerLogic cada vez que el jugador se mueve (evento de movimiento real).
     * Solo procesa si el jugador cambió de posición de forma significativa.
     * De esta forma NUNCA se corre en un tick sin que el jugador haya hecho algo.
     */
    public static void onPlayerMove(ServerPlayerEntity player) {
        String uuid = player.getUuidAsString();
        double x = player.getX();
        double y = player.getY();
        double z = player.getZ();

        double[] prev = lastPos.get(uuid);
        if (prev != null) {
            double dist = Math.sqrt(Math.pow(x - prev[0], 2) + Math.pow(y - prev[1], 2) + Math.pow(z - prev[2], 2));
            // Solo procesar si se movió al menos 5 bloques (filtrar micro-movimientos y teleports grandes)
            if (dist < 5 || dist > 200) return;
        }
        lastPos.put(uuid, new double[]{x, y, z});

        // LOGRO DE ALTURA MÁXIMA (Everest) - solo una vez por sesión
        if (y >= 319 && sessionFlags.add(uuid + "_height")) {
            AchievementClient.sendEvent(uuid, "max_height_reached", 1);
        }

        // EFECTO WARDEN (Oscuridad) - solo si el jugador lo tiene en este momento
        if (player.hasStatusEffect(StatusEffects.DARKNESS) && sessionFlags.add(uuid + "_warden")) {
            AchievementClient.sendEvent(uuid, "warden_darkness_effect", 1);
        }
    }

    /**
     * Limpia los flags y posición al desconectarse el jugador.
     */
    public static void onPlayerLeave(ServerPlayerEntity player) {
        String uuid = player.getUuidAsString();
        lastPos.remove(uuid);
        sessionFlags.removeIf(f -> f.startsWith(uuid));
    }

    public static void register() {
        // DETECTOR DE INTERACCIONES (OVEJA ROSA) - event-driven, sin tick
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
