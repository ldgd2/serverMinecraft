package com.lider.minebridge.events.combat;

import com.lider.minebridge.networking.AchievementClient;
import java.util.concurrent.ConcurrentHashMap;

public class CombatLogic {

    // Acumuladores para reducir tráfico de red
    private static final ConcurrentHashMap<String, Integer> totalKillsAccum = new ConcurrentHashMap<>();
    private static final ConcurrentHashMap<String, Integer> hostileKillsAccum = new ConcurrentHashMap<>();

    public static void init() {
        // La mayoría del combate se maneja vía Mixin (LivingEntityMixin)
    }

    /**
     * Llamado cuando un jugador mata a una entidad.
     * Los kills específicos (Bosses, Warden, etc.) se envían al momento.
     * Los kills genéricos se acumulan y se envían cada 10.
     */
    public static void onEntityKill(String playerUuid, String victimId) {
        // 1. KILLS ESPECÍFICOS (Siempre enviar al instante para logros de "Primer X")
        // Solo enviamos si es una entidad relevante para logros específicos
        if (victimId.contains("ender_dragon") || victimId.contains("wither") || 
            victimId.contains("warden") || victimId.contains("elder_guardian")) {
            AchievementClient.sendEvent(playerUuid, "kill:" + victimId, 1);
        }

        // 2. TOTAL KILLS (Acumular cada 10)
        int total = totalKillsAccum.merge(playerUuid, 1, Integer::sum);
        if (total % 10 == 0) {
            AchievementClient.sendEvent(playerUuid, "total_kills", 10);
        }
        
        // 3. HOSTILE KILLS (Acumular cada 10)
        if (victimId.contains("zombie") || victimId.contains("skeleton") || 
            victimId.contains("creeper") || victimId.contains("blaze") || 
            victimId.contains("spider") || victimId.contains("enderman") ||
            victimId.contains("piglin") || victimId.contains("ghast")) {
            
            int hostile = hostileKillsAccum.merge(playerUuid, 1, Integer::sum);
            if (hostile % 10 == 0) {
                AchievementClient.sendEvent(playerUuid, "hostile_kills", 10);
            }
        }
    }

    public static void onTotemUsed(String playerUuid) {
        AchievementClient.sendEvent(playerUuid, "totem_used", 1);
    }

    public static void onSkeletonSnipe(String playerUuid, double distance) {
        if (distance >= 50.0) {
            AchievementClient.sendEvent(playerUuid, "skeleton_snipe_distance", 50);
        }
    }

    /** Limpiar acumulados al salir */
    public static void onPlayerLeave(String uuid) {
        Integer t = totalKillsAccum.remove(uuid);
        if (t != null && t % 10 != 0) AchievementClient.sendEvent(uuid, "total_kills", t % 10);
        
        Integer h = hostileKillsAccum.remove(uuid);
        if (h != null && h % 10 != 0) AchievementClient.sendEvent(uuid, "hostile_kills", h % 10);
    }
}
