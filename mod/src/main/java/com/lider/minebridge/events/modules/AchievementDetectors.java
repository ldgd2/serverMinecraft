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
        net.minecraft.util.math.Vec3d currentPos = player.getPos();
        long now = System.currentTimeMillis();

        // 1. TIEMPO Y HORARIOS
        int seconds = playtimeSession.merge(uuid, 2, Integer::sum);
        AchievementClient.sendEvent(uuid, "playtime_seconds", 2);

        LocalTime time = LocalTime.now();
        if (time.getHour() >= 3 && time.getHour() <= 5) AchievementClient.sendEvent(uuid, "play_at_night", 1);
        if (time.getHour() >= 6 && time.getHour() <= 8) AchievementClient.sendEvent(uuid, "play_at_dawn", 1);

        // 2. AFK (1 hora)
        net.minecraft.util.math.Vec3d prevPos = lastPos.get(uuid);
        if (prevPos != null && currentPos.distanceTo(prevPos) < 0.1) {
            long afkTime = now - lastMoveTime.getOrDefault(uuid, now);
            if (afkTime >= 3600000 && sessionUnlocked.add(uuid + "_afk1h")) {
                AchievementClient.sendEvent(uuid, "afk_seconds", 3600);
            }
        } else {
            lastMoveTime.put(uuid, now);
        }

        // 3. DISTANCIA Y MONTURAS
        if (prevPos != null) {
            double dist = currentPos.distanceTo(prevPos);
            if (dist > 0.1) {
                int totalDist = distanceSession.merge(uuid, (int)dist, Integer::sum);
                AchievementClient.sendEvent(uuid, "distance_travelled", (int)dist);
                
                if (totalDist >= 10000 && totalDist < 10100 && sessionUnlocked.add(uuid + "_dist10k")) AchievementClient.sendEvent(uuid, "DIST_1", 1);
                if (totalDist >= 100000 && totalDist < 100500 && sessionUnlocked.add(uuid + "_dist100k")) AchievementClient.sendEvent(uuid, "DIST_2", 1);

                if (player.getVehicle() != null) {
                    AchievementClient.sendEvent(uuid, "distance_mounted", (int)dist);
                    if (Registries.ENTITY_TYPE.getId(player.getVehicle().getType()).getPath().contains("strider") && player.isInLava()) {
                        AchievementClient.sendEvent(uuid, "strider_lava_distance", (int)dist);
                    }
                }
            }
        }
        lastPos.put(uuid, currentPos);

        // 4. ALTURA (EVEREST RESTAURADO)
        double y = player.getY();
        if (y >= 319) AchievementClient.sendEvent(uuid, "max_height_reached", 1);

        // 5. EFECTOS
        if (player.hasStatusEffect(net.minecraft.entity.effect.StatusEffects.DARKNESS)) {
            AchievementClient.sendEvent(uuid, "warden_darkness_effect", 1);
        }
        if (player.getStatusEffects().size() >= 10) {
            AchievementClient.sendEvent(uuid, "active_effects_count", 1);
        }

        // OTROS
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
    }

    public static void onPlayerSleep(ServerPlayerEntity player) {
        String uuid = player.getUuidAsString();
        AchievementClient.sendEvent(uuid, "sleep_with_bad_omen", 1);
    }

    public static void register() {
        UseEntityCallback.EVENT.register((player, world, hand, entity, hitResult) -> {
            if (!world.isClient && player instanceof ServerPlayerEntity serverPlayer) {
                String uuid = serverPlayer.getUuidAsString();
                if (entity instanceof SheepEntity sheep && sheep.getColor() == DyeColor.PINK) {
                    AchievementClient.sendEvent(uuid, "pink_sheep_found", 1);
                }
                // TRADER
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
                // STEAK NEAR PLAYER
                if (stack.getItem().getTranslationKey().contains("cooked_beef")) {
                    boolean near = player.getWorld().getPlayers().stream().anyMatch(p -> p != player && p.getPos().distanceTo(player.getPos()) < 5);
                    if (near) AchievementClient.sendEvent(serverPlayer.getUuidAsString(), "eat_steak_near_player", 1);
                }
            }
            return TypedActionResult.pass(player.getStackInHand(hand));
        });
    }
}
