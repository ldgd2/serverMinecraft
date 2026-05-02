package com.lider.minebridge.events;

import com.lider.minebridge.events.blocks.BlockLogic;
import com.lider.minebridge.events.combat.CombatLogic;
import com.lider.minebridge.events.economy.EconomyLogic;
import com.lider.minebridge.events.items.ItemLogic;
import com.lider.minebridge.events.player.PlayerLogic;
import com.lider.minebridge.events.special.MemeLogic;
import com.lider.minebridge.events.world.WorldLogic;
import net.minecraft.server.network.ServerPlayerEntity;

/**
 * El Gran Orquestador. 
 * Su única misión es despertar a los módulos especializados al inicio.
 */
public class ServerEvents {

    public static void init() {
        // Inicializar cada dominio por separado
        PlayerLogic.init();
        BlockLogic.init();
        CombatLogic.init();
        ItemLogic.init();
        WorldLogic.init();
        MemeLogic.init();
        EconomyLogic.init();
    }

    /**
     * Puentes para Mixins (Delegando a sus respectivos dominios)
     */
    public static void onNetherBedExplosion(ServerPlayerEntity player) {
        MemeLogic.onNetherBedExplosion(player);
    }

    public static void onPlayerDeath(ServerPlayerEntity player, net.minecraft.entity.damage.DamageSource source, net.minecraft.text.Text deathMessage) {
        PlayerLogic.onPlayerDeath(player, source, deathMessage);
    }
}
