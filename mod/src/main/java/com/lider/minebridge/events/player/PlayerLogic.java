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

    public static void init() {
        // CHAT
        ServerMessageEvents.CHAT_MESSAGE.register((message, sender, params) -> {
            AchievementClient.sendChatMessage(sender.getUuidAsString(), sender.getName().getString(), message.getContent().getString(), "chat");
        });

        // CONEXIÓN
        ServerPlayConnectionEvents.JOIN.register((handler, sender, server) -> {
            ServerPlayerEntity player = handler.getPlayer();
            AchievementClient.sendChatMessage(player.getUuidAsString(), player.getName().getString(), "se ha unido.", "join");
        });

        // DESCONEXIÓN
        ServerPlayConnectionEvents.DISCONNECT.register((handler, server) -> {
            ServerPlayerEntity player = handler.getPlayer();
            AchievementClient.sendChatMessage(player.getUuidAsString(), player.getName().getString(), "ha salido.", "leave");
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

        // 5. SELF TNT DEATH (Mi momento ha llegado)
        if (deathMsgStr.contains("explosion") || deathMsgStr.contains("blew up")) {
            AchievementClient.sendEvent(player.getUuidAsString(), "self_tnt_death", 1);
        }

        // 6. VOID DEATH WITH FULL INVENTORY (No me quiero ir Sr. Stark)
        if (deathMsgStr.contains("fell out of the world") || deathMsgStr.contains("void")) {
            MemeLogic.onVoidDeathCheck(player);
        }
    }

    public static void onDimensionChange(ServerPlayerEntity player, String dimensionId) {
        AchievementClient.sendEvent(player.getUuidAsString(), "dimension_enter:" + dimensionId, 1);
    }

    public static void checkPhysicalAchievements(ServerPlayerEntity player) {
        if (player.getY() >= 319) {
            AchievementClient.sendEvent(player.getUuidAsString(), "max_height_reached", 1);
        }
        if (player.experienceLevel >= 100) {
            AchievementClient.sendEvent(player.getUuidAsString(), "xp_level", 100);
        }
    }

    public static void onPlayerDamage(ServerPlayerEntity player, float amount, boolean isFallDamage) {
        if (isFallDamage && player.fallDistance > 30 && player.getHealth() <= 1.0f) {
            AchievementClient.sendEvent(player.getUuidAsString(), "clutch_survival", 1);
        }
    }
}
