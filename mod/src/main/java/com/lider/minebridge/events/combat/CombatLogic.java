package com.lider.minebridge.events.combat;

import com.lider.minebridge.networking.AchievementClient;
import net.minecraft.server.network.ServerPlayerEntity;
import net.minecraft.registry.Registries;
import java.util.concurrent.ConcurrentHashMap;

public class CombatLogic {

    private static final ConcurrentHashMap<String, Integer> totalKillsSession = new ConcurrentHashMap<>();
    private static final ConcurrentHashMap<String, Integer> totalKillsStart = new ConcurrentHashMap<>();
    private static final ConcurrentHashMap<String, Integer> totemsUsedSession = new ConcurrentHashMap<>();

    public static void init() {
        // Inicialización requerida por ServerEvents
    }

    public static void setInitialStats(String uuid, int total) {
        totalKillsStart.put(uuid, total);
    }

    public static void onEntityKill(String playerUuid, String victimId) {
        // Log para depuración
        com.lider.minebridge.MineBridge.LOGGER.info("[MineBridge] Eliminación detectada: " + victimId + " por " + playerUuid);

        if (victimId.contains("ender_dragon")) {
            AchievementClient.sendEvent(playerUuid, "dragon_killed_by_bed", 1);
            com.lider.minebridge.events.player.PlayerLogic.onBossKilled(playerUuid);
        }
        if (victimId.contains("wither") && !victimId.contains("skeleton")) {
            com.lider.minebridge.events.player.PlayerLogic.onBossKilled(playerUuid);
        }
        if (victimId.contains("ghast")) AchievementClient.sendEvent(playerUuid, "ghast_fireball_kill", 1);
        if (victimId.contains("axolotl")) AchievementClient.sendEvent(playerUuid, "kill_axolotl", 1);
        if (victimId.contains("villager")) AchievementClient.sendEvent(playerUuid, "kill_villager", 1);
        if (victimId.contains("warden")) AchievementClient.sendEvent(playerUuid, "kill_warden", 1);

        int sessionKills = totalKillsSession.merge(playerUuid, 1, Integer::sum);
        int totalKills = totalKillsStart.getOrDefault(playerUuid, 0) + sessionKills;
        
        AchievementClient.sendEvent(playerUuid, "total_kills", 1);
        AchievementClient.sendEvent(playerUuid, "session_kills", 1);

        if (totalKills == 10) AchievementClient.sendEvent(playerUuid, "KILL_1", 1);
        if (totalKills == 50) AchievementClient.sendEvent(playerUuid, "KILL_2", 1);
        if (totalKills == 100) AchievementClient.sendEvent(playerUuid, "KILL_3", 1);
        if (totalKills == 500) AchievementClient.sendEvent(playerUuid, "KILL_4", 1);
        if (totalKills == 1000) {
            AchievementClient.sendEvent(playerUuid, "KILL_5", 1);
            AchievementClient.sendEvent(playerUuid, "GOD_OF_WAR", 1);
        }
        if (totalKills == 5000) AchievementClient.sendEvent(playerUuid, "KILL_ELITE", 1);
        if (totalKills == 10000) AchievementClient.sendEvent(playerUuid, "PHILO_KILL_ENT", 1);
        if (totalKills == 50000) AchievementClient.sendEvent(playerUuid, "PHILO_GOD", 1);

        if (victimId.contains("zombie") || victimId.contains("skeleton") || victimId.contains("creeper") ||
            victimId.contains("blaze") || victimId.contains("spider") || victimId.contains("ghast")) {
            AchievementClient.sendEvent(playerUuid, "hostile_kills", 1);
        }
    }

    public static void onSkeletonSnipe(String playerUuid, double distance) {
        if (distance >= 50.0) AchievementClient.sendEvent(playerUuid, "skeleton_snipe_distance", 1);
    }

    public static void onPlayerAttack(ServerPlayerEntity player, net.minecraft.entity.Entity victim) {
        String uuid = player.getUuidAsString();
        String vId = Registries.ENTITY_TYPE.getId(victim.getType()).getPath();
        if (vId.contains("warden") && player.getMainHandStack().isEmpty()) AchievementClient.sendEvent(uuid, "punch_warden", 1);
    }

    public static void onTotemUsed(String playerUuid) {
        totemsUsedSession.merge(playerUuid, 1, Integer::sum);
        AchievementClient.sendEvent(playerUuid, "totem_used", 1);
    }

    public static void onPlayerLeave(String uuid) {
        java.util.Map<String, Integer> stats = new java.util.HashMap<>();
        Integer total = totalKillsSession.remove(uuid);
        if (total != null) stats.put("total_kills", total);
        Integer totems = totemsUsedSession.remove(uuid);
        if (totems != null) stats.put("totem_used", totems);
        if (!stats.isEmpty()) AchievementClient.sendSessionSummary(uuid, stats);
        totalKillsStart.remove(uuid);
    }

    public static void onCreeperKill(net.minecraft.entity.Entity victim) {
        victim.getWorld().getEntitiesByClass(net.minecraft.server.network.ServerPlayerEntity.class, victim.getBoundingBox().expand(15.0), p -> true)
            .forEach(player -> AchievementClient.sendEvent(player.getUuidAsString(), "creeper_kill_witness", 1));
    }
}
