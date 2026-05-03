package com.lider.minebridge.events.player;

import com.lider.minebridge.events.special.MemeLogic;
import com.lider.minebridge.networking.AchievementClient;
import net.fabricmc.fabric.api.message.v1.ServerMessageEvents;
import net.fabricmc.fabric.api.networking.v1.ServerPlayConnectionEvents;
import net.minecraft.entity.damage.DamageSource;
import net.minecraft.registry.Registries;
import net.minecraft.server.network.ServerPlayerEntity;
import net.minecraft.text.Text;

import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.concurrent.ConcurrentHashMap;
import java.time.LocalDate;

public class PlayerLogic {

    private static final Set<String> sessionUnlocked = ConcurrentHashMap.newKeySet();
    private static long serverStartTime = System.currentTimeMillis();
    
    private static final ConcurrentHashMap<String, Integer> chatMessagesSession = new ConcurrentHashMap<>();
    private static final ConcurrentHashMap<String, Integer> deathsTotalSession = new ConcurrentHashMap<>();
    private static final ConcurrentHashMap<String, Integer> deathsTotalStart = new ConcurrentHashMap<>();
    private static final ConcurrentHashMap<String, Map<String, Integer>> deathsByCauseSession = new ConcurrentHashMap<>();
    private static final ConcurrentHashMap<String, String> lastKillerOf = new ConcurrentHashMap<>();
    
    private static final ConcurrentHashMap<String, Long> lastBossKillTime = new ConcurrentHashMap<>();
    private static final ConcurrentHashMap<String, Set<String>> recentDamagers = new ConcurrentHashMap<>();
    private static final ConcurrentHashMap<String, DeathHistory> deathHistory = new ConcurrentHashMap<>();

    private static class DeathHistory {
        String cause; long lastTime; int count;
        DeathHistory(String c, long t) { this.cause = c; this.lastTime = t; this.count = 1; }
    }

    public static void init() {
        ServerMessageEvents.CHAT_MESSAGE.register((message, sender, params) -> {
            String uuid = sender.getUuidAsString();
            String content = message.getContent().getString();
            AchievementClient.sendChatMessage(uuid, sender.getName().getString(), content, "chat");
            
            if (content.equalsIgnoreCase("GG")) {
                Long killTime = lastBossKillTime.get(uuid);
                if (killTime != null && (System.currentTimeMillis() - killTime) < 60000) {
                    AchievementClient.sendEvent(uuid, "gg_after_boss", 1);
                }
            }
            int total = chatMessagesSession.merge(uuid, 1, Integer::sum);
            if (total == 1) AchievementClient.sendEvent(uuid, "CHAT_0", 1);
            if (total == 50) AchievementClient.sendEvent(uuid, "CHAT_1", 1);
            if (total == 250) AchievementClient.sendEvent(uuid, "CHAT_2", 1);
            if (total == 1000) AchievementClient.sendEvent(uuid, "CHAT_3", 1);
            if (total == 5000) AchievementClient.sendEvent(uuid, "CHAT_4", 1);
        });

        ServerPlayConnectionEvents.JOIN.register((handler, sender, server) -> {
            ServerPlayerEntity player = handler.getPlayer();
            String uuid = player.getUuidAsString();
            AchievementClient.sendChatMessage(uuid, player.getName().getString(), "se ha unido.", "join");
            AchievementClient.fetchPlayerStats(uuid);

            if ((System.currentTimeMillis() - serverStartTime) < 60000) AchievementClient.sendEvent(uuid, "join_after_restart", 1);
            LocalDate now = LocalDate.now();
            if (now.getMonthValue() == 5 && now.getDayOfMonth() == 3) AchievementClient.sendEvent(uuid, "join_on_anniversary", 1);
        });

        ServerPlayConnectionEvents.DISCONNECT.register((handler, server) -> {
            ServerPlayerEntity player = handler.getPlayer();
            String uuid = player.getUuidAsString();
            AchievementClient.sendChatMessage(uuid, player.getName().getString(), "ha salido.", "leave");
            onPlayerLeaveCleanup(uuid);
        });

        final java.util.concurrent.atomic.AtomicInteger tickCounter = new java.util.concurrent.atomic.AtomicInteger(0);
        net.fabricmc.fabric.api.event.lifecycle.v1.ServerTickEvents.END_SERVER_TICK.register(server -> {
            if (tickCounter.incrementAndGet() % 40 == 0) {
                for (ServerPlayerEntity p : server.getPlayerManager().getPlayerList()) {
                    com.lider.minebridge.events.modules.AchievementDetectors.onPlayerMove(p);
                    if (p.experienceLevel >= 100) AchievementClient.sendEvent(p.getUuidAsString(), "xp_level", 100);
                }
            }
        });
    }

    public static void setInitialStats(String uuid, int totalDeaths, long lastSeen) {
        deathsTotalStart.put(uuid, totalDeaths);
        if (lastSeen > 0 && (System.currentTimeMillis() - lastSeen) > 604800000L) AchievementClient.sendEvent(uuid, "return_after_7d", 1);
    }

    public static void onBossKilled(String uuid) {
        lastBossKillTime.put(uuid, System.currentTimeMillis());
    }

    public static void onPlayerDamage(ServerPlayerEntity victim, DamageSource source) {
        String uuid = victim.getUuidAsString();
        if (source.getAttacker() instanceof ServerPlayerEntity attacker) {
            recentDamagers.computeIfAbsent(uuid, k -> ConcurrentHashMap.newKeySet()).add(attacker.getUuidAsString());
            boolean noArmor = true;
            for (net.minecraft.item.ItemStack stack : victim.getArmorItems()) if (!stack.isEmpty()) { noArmor = false; break; }
            if (noArmor) AchievementClient.sendEvent(uuid, "attacked_without_armor", 1);
        }
    }

    public static void onPlayerDeath(ServerPlayerEntity player, DamageSource source, Text deathMsg) {
        String uuid = player.getUuidAsString();
        String causeKey = source.getName();
        if (source.getAttacker() instanceof ServerPlayerEntity) causeKey = "player";
        
        long now = System.currentTimeMillis();
        AchievementClient.sendChatMessage(uuid, player.getName().getString(), deathMsg.getString(), "death");

        // 1. CONTADORES
        int sDeaths = deathsTotalSession.merge(uuid, 1, Integer::sum);
        int tDeaths = deathsTotalStart.getOrDefault(uuid, 0) + sDeaths;
        Map<String, Integer> pDeaths = deathsByCauseSession.computeIfAbsent(uuid, k -> new java.util.HashMap<>());
        int count = pDeaths.merge(causeKey, 1, Integer::sum);

        // 2. LOGROS DE MUERTE BÁSICOS
        if (tDeaths == 1) AchievementClient.sendEvent(uuid, "first_death", 1);
        if (player.experienceLevel >= 100) AchievementClient.sendEvent(uuid, "die_with_100_lvl", 1);

        // 3. SR. STARK (Vacío)
        if (causeKey.contains("out_of_world") || deathMsg.getString().toLowerCase().contains("void")) {
            int invCount = 0;
            for (int i = 0; i < player.getInventory().size(); i++) if (!player.getInventory().getStack(i).isEmpty()) invCount++;
            if (invCount > 30) AchievementClient.sendEvent(uuid, "full_inventory_void_death", 1);
        }

        // 4. CLUTCH
        if (causeKey.contains("fall") && player.fallDistance > 30 && player.getHealth() <= 1.0f) {
            AchievementClient.sendEvent(uuid, "clutch_survival", 1);
        }

        // 5. MUERTE REPETIDA
        DeathHistory hist = deathHistory.get(uuid);
        if (hist != null && hist.cause.equals(causeKey) && (now - hist.lastTime) < 300000) {
            hist.count++; hist.lastTime = now;
            if (hist.count == 3) AchievementClient.sendEvent(uuid, "repeat_death_streak", 1);
        } else deathHistory.put(uuid, new DeathHistory(causeKey, now));

        // 6. TODOS CONTRA YO SOLO
        Set<String> attackers = recentDamagers.get(uuid);
        if (attackers != null && attackers.size() >= 3) AchievementClient.sendEvent(uuid, "died_to_team", 1);
        recentDamagers.remove(uuid);

        // 7. HITOS POR CAUSA
        if (causeKey.equals("player") && count == 10) {
            AchievementClient.sendEvent(uuid, "killed_by_player_10", 1);
            AchievementClient.sendEvent(uuid, "DEATH_PVP_10", 1);
        }
        if (causeKey.contains("zombie") && count == 10) AchievementClient.sendEvent(uuid, "DEATH_ZOMB_10", 1);
        if (causeKey.contains("creeper") && count == 10) AchievementClient.sendEvent(uuid, "DEATH_CREEP_10", 1);
        if (causeKey.contains("fall") && count == 100) AchievementClient.sendEvent(uuid, "DEATH_FALL_100", 1);
        if (causeKey.contains("out_of_world") && count == 10) AchievementClient.sendEvent(uuid, "DEATH_VOID_10", 1);
        
        if (causeKey.contains("fall") || causeKey.contains("lava") || causeKey.contains("fire")) AchievementClient.sendEvent(uuid, "self_death", 1);

        // 8. TRIPLE AMENAZA
        List<net.minecraft.entity.mob.MobEntity> nearby = player.getWorld().getEntitiesByClass(net.minecraft.entity.mob.MobEntity.class, player.getBoundingBox().expand(10.0), m -> true);
        boolean c = false, z = false, s = false;
        for (net.minecraft.entity.mob.MobEntity m : nearby) {
            String mid = Registries.ENTITY_TYPE.getId(m.getType()).getPath();
            if (mid.contains("creeper")) c = true;
            if (mid.contains("zombie")) z = true;
            if (mid.contains("skeleton")) s = true;
        }
        if (c && z && s) AchievementClient.sendEvent(uuid, "triple_threat_death", 1);

        // 9. TÓTEM EN INVENTARIO
        boolean hasTotem = false;
        for (int i = 0; i < player.getInventory().size(); i++) {
            if (player.getInventory().getStack(i).getItem() == net.minecraft.item.Items.TOTEM_OF_UNDYING) { hasTotem = true; break; }
        }
        if (hasTotem && player.getMainHandStack().getItem() != net.minecraft.item.Items.TOTEM_OF_UNDYING && player.getOffHandStack().getItem() != net.minecraft.item.Items.TOTEM_OF_UNDYING) {
            AchievementClient.sendEvent(uuid, "die_with_totem_in_inv", 1);
        }

        // 10. VENGANZA
        if (source.getAttacker() instanceof ServerPlayerEntity killer) {
            String kUuid = killer.getUuidAsString();
            AchievementClient.sendEvent(uuid, "killed_by_player", 1);
            String pk = lastKillerOf.get(kUuid);
            if (pk != null && pk.equals(uuid)) AchievementClient.sendEvent(kUuid, "revenge_kill", 1);
            lastKillerOf.put(uuid, kUuid);
        }

        // 11. SKILL ISSUE / MEMES
        String dMsg = deathMsg.getString().toLowerCase();
        if (dMsg.contains("zombie")) {
            boolean fullN = true;
            for (net.minecraft.item.ItemStack armor : player.getArmorItems()) if (!armor.getItem().getTranslationKey().contains("netherite")) { fullN = false; break; }
            if (fullN) AchievementClient.sendEvent(uuid, "skill_issue_death", 1);
        }
        if (dMsg.contains("explosion") || dMsg.contains("blew up")) AchievementClient.sendEvent(uuid, "self_tnt_death", 1);
        if (dMsg.contains("intentional game design")) AchievementClient.sendEvent(uuid, "nether_bed_explosion", 1);
        if (dMsg.contains("cactus")) MemeLogic.onCactusDeath(player);
    }

    public static void onDimensionChange(ServerPlayerEntity player, String dimensionId) {
        String uuid = player.getUuidAsString();
        if (sessionUnlocked.add(uuid + "_dim_" + dimensionId)) {
            if (dimensionId.contains("the_end")) AchievementClient.sendEvent(uuid, "enter_dimension:minecraft:the_end", 1);
        }
    }

    private static void onPlayerLeaveCleanup(String uuid) {
        Map<String, Integer> stats = new java.util.HashMap<>();
        Integer chat = chatMessagesSession.remove(uuid);
        if (chat != null) stats.put("chat_message", chat);
        Integer deaths = deathsTotalSession.remove(uuid);
        if (deaths != null) stats.put("death_total", deaths);
        if (!stats.isEmpty()) AchievementClient.sendSessionSummary(uuid, stats);
        sessionUnlocked.removeIf(s -> s.startsWith(uuid));
        lastKillerOf.remove(uuid); deathsTotalStart.remove(uuid);
        lastBossKillTime.remove(uuid); recentDamagers.remove(uuid); deathHistory.remove(uuid);
    }
}
