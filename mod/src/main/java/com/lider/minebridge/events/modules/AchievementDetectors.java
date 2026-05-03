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

    private static final ConcurrentHashMap<String, Double> lastY = new ConcurrentHashMap<>();
    private static final ConcurrentHashMap<String, net.minecraft.util.math.Vec3d> lastPos = new ConcurrentHashMap<>();
    private static final ConcurrentHashMap<String, Integer> distanceSession = new ConcurrentHashMap<>();
    private static final ConcurrentHashMap<String, Integer> playtimeSession = new ConcurrentHashMap<>();
    private static final ConcurrentHashMap<String, Long> lastMoveTime = new ConcurrentHashMap<>();
    private static final Set<String> xpGainedSession = ConcurrentHashMap.newKeySet();
    private static final Set<String> nightSurvivors = ConcurrentHashMap.newKeySet();
    private static final Set<String> sessionUnlocked = ConcurrentHashMap.newKeySet();

    public static void onPlayerMove(ServerPlayerEntity player) {
        String uuid = player.getUuidAsString();
        // 4. ALTURA (Logro Everest)
        if (player.getY() >= 310) {
            MemeLogic.onMaxHeightReached(player);
        }

        // 5. EFECTOS
        if (player.hasStatusEffect(net.minecraft.entity.effect.StatusEffects.DARKNESS)) {
            AchievementClient.sendEvent(uuid, "warden_darkness_effect", 1);
        }
        if (player.getStatusEffects().size() >= 10) {
            AchievementClient.sendEvent(uuid, "active_effects_count", 1);
        }

        if ((player.experienceLevel > 0 || player.experienceProgress > 0) && xpGainedSession.add(uuid)) {
            AchievementClient.sendEvent(uuid, "gain_first_xp", 1);
        }
    }

    private static final ConcurrentHashMap<String, Integer> animalTamedSession = new ConcurrentHashMap<>();
    private static final ConcurrentHashMap<String, Integer> bedSleptSession = new ConcurrentHashMap<>();

    public static void onPlayerLeave(ServerPlayerEntity player) {
        String uuid = player.getUuidAsString();
        java.util.Map<String, Integer> stats = new java.util.HashMap<>();
        Integer dist = distanceSession.remove(uuid);
        if (dist != null) stats.put("distance_travelled", dist);
        Integer time = playtimeSession.remove(uuid);
        if (time != null) stats.put("playtime_seconds", time);
        Integer tamed = animalTamedSession.remove(uuid);
        if (tamed != null) stats.put("animal_tamed", tamed);
        if (!stats.isEmpty()) AchievementClient.sendSessionSummary(uuid, stats);
        lastY.remove(uuid); lastPos.remove(uuid); lastMoveTime.remove(uuid);
        xpGainedSession.remove(uuid); nightSurvivors.remove(uuid);
        playtimeSession.remove(uuid); bedSleptSession.remove(uuid); 
        sessionUnlocked.removeIf(s -> s.startsWith(uuid));
    }

    public static void onAnimalTamed(ServerPlayerEntity player, TameableEntity animal) {
        String uuid = player.getUuidAsString();
        String type = Registries.ENTITY_TYPE.getId(animal.getType()).getPath();
        if (type.contains("wolf")) {
            AchievementClient.sendEvent(uuid, "tame_wolf", 1);
            List<WolfEntity> wolves = player.getWorld().getEntitiesByClass(WolfEntity.class, player.getBoundingBox().expand(15.0), w -> w.isOwner(player));
            if (wolves.size() >= 5) AchievementClient.sendEvent(uuid, "tame_5_dogs", 1);
        }
        animalTamedSession.merge(uuid, 1, Integer::sum);
    }

    public static void onPlayerSleep(ServerPlayerEntity player) {
        String uuid = player.getUuidAsString();
        bedSleptSession.merge(uuid, 1, Integer::sum);
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
                if (stack.getItem().getTranslationKey().contains("cooked_beef")) {
                    boolean near = player.getWorld().getPlayers().stream().anyMatch(p -> p != player && p.getPos().distanceTo(player.getPos()) < 5);
                    if (near) AchievementClient.sendEvent(serverPlayer.getUuidAsString(), "eat_steak_near_player", 1);
                }
            }
            return TypedActionResult.pass(player.getStackInHand(hand));
        });
    }
}
