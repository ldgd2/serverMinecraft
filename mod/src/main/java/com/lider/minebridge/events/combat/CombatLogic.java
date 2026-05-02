package com.lider.minebridge.events.combat;

import com.lider.minebridge.networking.AchievementClient;

public class CombatLogic {

    public static void init() {
        // La mayoría del combate se maneja vía Mixin (LivingEntityMixin)
        // Pero aquí registramos listeners globales si fuera necesario.
    }

    public static void onEntityKill(String playerUuid, String victimId) {
        AchievementClient.sendEvent(playerUuid, "kill:" + victimId, 1);
        AchievementClient.sendEvent(playerUuid, "total_kills", 1);
        
        // Acumulador de entidades hostiles (God of War)
        if (victimId.contains("zombie") || victimId.contains("skeleton") || victimId.contains("creeper") || victimId.contains("blaze")) {
            AchievementClient.sendEvent(playerUuid, "hostile_kills", 1);
        }
    }

    public static void onTotemUsed(String playerUuid) {
        AchievementClient.sendEvent(playerUuid, "totem_used", 1);
    }

    public static void onWardenDarkness(String playerUuid) {
        AchievementClient.sendEvent(playerUuid, "warden_darkness_effect", 1);
    }

    public static void onSkeletonSnipe(String playerUuid, double distance) {
        if (distance >= 50.0) {
            AchievementClient.sendEvent(playerUuid, "skeleton_snipe_distance", 50);
        }
    }
}
