package com.lider.minebridge.events.modules;

import com.lider.minebridge.events.special.MemeLogic;
import com.lider.minebridge.networking.AchievementClient;
import net.fabricmc.fabric.api.event.player.UseEntityCallback;
import net.fabricmc.fabric.api.event.player.UseItemCallback;
import net.minecraft.entity.passive.SheepEntity;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.network.ServerPlayerEntity;
import net.minecraft.util.ActionResult;
import net.minecraft.util.DyeColor;
import net.minecraft.util.TypedActionResult;
import net.minecraft.world.World;

import java.util.concurrent.ConcurrentHashMap;

public class AchievementDetectors {

    // Última posición Y registrada por jugador (solo necesitamos Y para altura)
    private static final ConcurrentHashMap<String, Double> lastY = new ConcurrentHashMap<>();

    /**
     * Llamado desde PlayerLogic cada 40 ticks (2 segundos).
     * Verifica altura SOLO si el jugador cambió de Y de forma significativa.
     * No hace nada si el jugador está quieto.
     */
    public static void onPlayerMove(ServerPlayerEntity player) {
        String uuid = player.getUuidAsString();
        double y = player.getY();

        Double prevY = lastY.get(uuid);
        if (prevY != null && Math.abs(y - prevY) < 10.0) {
            return; // No cambió suficiente altura — ignorar completamente
        }
        lastY.put(uuid, y);

        // Solo si llegó a la altura máxima
        if (y >= 319) {
            MemeLogic.onMaxHeightReached(player);
        }
    }

    /** Limpia el tracking de posición al desconectarse. */
    public static void onPlayerLeave(ServerPlayerEntity player) {
        lastY.remove(player.getUuidAsString());
        MemeLogic.onPlayerLeave(player);
    }

    public static void register() {
        // OVEJA ROSA — event-driven, dispara una sola vez por interacción
        UseEntityCallback.EVENT.register((player, world, hand, entity, hitResult) -> {
            if (!world.isClient && entity instanceof SheepEntity sheep && sheep.getColor() == DyeColor.PINK) {
                AchievementClient.sendEvent(player.getUuidAsString(), "pink_sheep_found", 1);
            }
            return ActionResult.PASS;
        });

        // PASTEL CERCA DE JUGADORES — event-driven via UseItem (cuando el jugador usa el pastel)
        UseItemCallback.EVENT.register((player, world, hand) -> {
            if (!world.isClient && player instanceof ServerPlayerEntity serverPlayer) {
                net.minecraft.item.ItemStack stack = player.getStackInHand(hand);
                if (stack.getItem().getTranslationKey().contains("cake")) {
                    MinecraftServer server = serverPlayer.getServer();
                    if (server != null) {
                        int nearbyCount = (int) server.getPlayerManager().getPlayerList().stream()
                            .filter(p -> p != serverPlayer && p.getPos().distanceTo(serverPlayer.getPos()) < 8.0)
                            .count();
                        MemeLogic.onCakeHeldNearPlayers(serverPlayer, nearbyCount);
                    }
                }
            }
            return TypedActionResult.pass(player.getStackInHand(hand));
        });
    }
}
