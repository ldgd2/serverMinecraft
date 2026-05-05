package com.lider.minebridge.events;

import com.lider.minebridge.networking.AchievementClient;
import net.fabricmc.fabric.api.event.player.PlayerBlockBreakEvents;
import net.minecraft.block.Block;
import net.minecraft.registry.Registries;
import net.minecraft.util.Identifier;

import java.util.Set;

public class ClientAchievementLogic {
    private static final Set<String> VALUABLE_ORES = Set.of(
        "diamond_ore", "deepslate_diamond_ore",
        "ancient_debris", "emerald_ore", "deepslate_emerald_ore"
    );

    private static int blocksBroken = 0;
    private static int diamondsMined = 0;

    public static void init() {
        // El CLIENTE detecta cuando ÉL MISMO rompe un bloque
        PlayerBlockBreakEvents.AFTER.register((world, player, pos, state, blockEntity) -> {
            if (!world.isClient) return; // Solo lógica de cliente
            
            blocksBroken++;
            Block block = state.getBlock();
            String id = Registries.BLOCK.getId(block).getPath();

            // Lógica de hitos de construcción/minería
            if (blocksBroken == 1000) AchievementClient.triggerAchievement("ARCH_1");
            
            if (VALUABLE_ORES.contains(id)) {
                if (id.contains("diamond")) {
                    diamondsMined++;
                    if (diamondsMined == 10) AchievementClient.triggerAchievement("DIAMOND_HUNTER");
                }
            }
        });
    }
}
