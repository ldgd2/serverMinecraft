package com.lider.minebridge.events;

import com.lider.minebridge.events.player.PlayerLogic;
import net.minecraft.server.network.ServerPlayerEntity;

/**
 * ServerEvents — El servidor ahora es ligero.
 * Solo maneja eventos de red y presencia.
 */
public class ServerEvents {

    public static void init() {
        PlayerLogic.init();
    }

    public static void onPlayerDeath(ServerPlayerEntity player, net.minecraft.entity.damage.DamageSource source, net.minecraft.text.Text deathMessage) {
        PlayerLogic.onPlayerDeath(player, source, deathMessage);
    }
}
