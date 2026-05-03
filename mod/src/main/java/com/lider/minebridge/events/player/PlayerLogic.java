package com.lider.minebridge.events.player;

import com.lider.minebridge.MineBridge;
import com.lider.minebridge.events.special.MemeLogic;
import com.lider.minebridge.networking.AchievementClient;
import net.fabricmc.fabric.api.message.v1.ServerMessageEvents;
import net.fabricmc.fabric.api.networking.v1.ServerPlayConnectionEvents;
import net.minecraft.entity.damage.DamageSource;
import net.minecraft.registry.Registries;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.network.ServerPlayerEntity;
import net.minecraft.text.Text;

public class PlayerLogic {

    private static final java.util.Set<String> sessionUnlocked = java.util.concurrent.ConcurrentHashMap.newKeySet();

    public static void init() {
        // CHAT
        ServerMessageEvents.CHAT_MESSAGE.register((message, sender, params) -> {
            AchievementClient.sendChatMessage(sender.getUuidAsString(), sender.getName().getString(), message.getContent().getString(), "chat");
        });

        // CONEXIÓN
        ServerPlayConnectionEvents.JOIN.register((handler, sender, server) -> {
            ServerPlayerEntity player = handler.getPlayer();
            com.lider.minebridge.networking.AchievementClient.sendChatMessage(player.getUuidAsString(), player.getName().getString(), "se ha unido.", "join");
            
            // Sincronizar Skin automáticamente al entrar
            com.lider.minebridge.networking.SkinClient.syncSkin(player);
        });

        // DESCONEXIÓN
        ServerPlayConnectionEvents.DISCONNECT.register((handler, server) -> {
            ServerPlayerEntity player = handler.getPlayer();
            String uuid = player.getUuidAsString();
            AchievementClient.sendChatMessage(uuid, player.getName().getString(), "ha salido.", "leave");
            
            // Limpiar y enviar acumulados pendientes
            com.lider.minebridge.events.modules.AchievementDetectors.onPlayerLeave(player);
            com.lider.minebridge.events.blocks.BlockLogic.onPlayerLeave(uuid);
            com.lider.minebridge.events.combat.CombatLogic.onPlayerLeave(uuid);
        });

        // DETECCIÓN DE ESTADOS PARA LOGROS (Altura, XP, etc.)
        // Corre 1 vez cada 40 ticks (2 segundos) POR JUGADOR
        final java.util.concurrent.atomic.AtomicInteger tickCounter = new java.util.concurrent.atomic.AtomicInteger(0);
        net.fabricmc.fabric.api.event.lifecycle.v1.ServerTickEvents.END_SERVER_TICK.register(server -> {
            if (tickCounter.incrementAndGet() % 40 == 0) {
                for (ServerPlayerEntity p : server.getPlayerManager().getPlayerList()) {
                    // Verificaciones de movimiento/altura
                    com.lider.minebridge.events.modules.AchievementDetectors.onPlayerMove(p);
                    
                    // Verificación de XP (Logro de nivel 100)
                    String uuid = p.getUuidAsString();
                    if (p.experienceLevel >= 100 && sessionUnlocked.add(uuid + "_xp100")) {
                        AchievementClient.sendEvent(uuid, "xp_level", 100);
                    }
                }
            }
        });
    }

    public static void broadcastFromApp(String user, String msg) {
        MinecraftServer server = MineBridge.getServer();
        if (server != null) {
            server.getPlayerManager().broadcast(Text.literal("§8[§bAPP§8] §3" + user + "§7: " + msg), false);
        }
    }

    public static void onPlayerDeath(ServerPlayerEntity player, DamageSource source, Text deathMsg) {
        AchievementClient.sendChatMessage(player.getUuidAsString(), player.getName().getString(), deathMsg.getString(), "death");
        
        // 1. EVENTO ESTRUCTURADO DE MUERTE
        String cause = "unknown";
        if (source.getAttacker() instanceof ServerPlayerEntity) {
            cause = "player";
        } else if (source.getAttacker() != null) {
            cause = "entity." + Registries.ENTITY_TYPE.getId(source.getAttacker().getType()).toString().replace(":", ".");
        } else {
            cause = "cause." + source.getName();
        }
        AchievementClient.sendEvent(player.getUuidAsString(), "death:" + cause, 1);
        AchievementClient.sendEvent(player.getUuidAsString(), "death_total", 1);

        String deathMsgStr = deathMsg.getString().toLowerCase();

        // 4. CACTUS NETHERITE DEATH (Darwin Award)
        if (deathMsgStr.contains("cactus")) {
            boolean fullNetherite = true;
            for (net.minecraft.item.ItemStack armor : player.getInventory().armor) {
                if (armor.isEmpty() || !armor.getItem().getTranslationKey().contains("netherite")) {
                    fullNetherite = false;
                    break;
                }
            }
            if (fullNetherite) {
                AchievementClient.sendEvent(player.getUuidAsString(), "netherite_cactus_death", 1);
            }
        }

        // 5. SELF TNT DEATH & BED EXPLOSIONS (Darwin Awards)
        if (deathMsgStr.contains("explosion") || deathMsgStr.contains("blew up")) {
            AchievementClient.sendEvent(player.getUuidAsString(), "self_tnt_death", 1);
        }
        if (deathMsgStr.contains("intentional game design")) {
            AchievementClient.sendEvent(player.getUuidAsString(), "nether_bed_explosion", 1);
        }

        // 6. VOID DEATH WITH FULL INVENTORY (No me quiero ir Sr. Stark)
        if (deathMsgStr.contains("fell out of the world") || deathMsgStr.contains("void")) {
            MemeLogic.onVoidDeathCheck(player);
        }
    }

    public static void onDimensionChange(ServerPlayerEntity player, String dimensionId) {
        String uuid = player.getUuidAsString();
        if (sessionUnlocked.add(uuid + "_dim_" + dimensionId)) {
            AchievementClient.sendEvent(uuid, "dimension_enter:" + dimensionId, 1);
        }
    }

    public static void checkPhysicalAchievements(ServerPlayerEntity player) {
        // Desactivado — ahora se maneja en el tick de 2 segundos (ServerTickEvents)
    }

    public static void onPlayerDamage(ServerPlayerEntity player, float amount, boolean isFallDamage) {
        if (isFallDamage && player.fallDistance > 30 && player.getHealth() <= 1.0f) {
            AchievementClient.sendEvent(player.getUuidAsString(), "clutch_survival", 1);
        }
    }
}
