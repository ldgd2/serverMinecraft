package com.lider.minebridge.events.blocks;

import com.lider.minebridge.networking.AchievementClient;
import net.fabricmc.fabric.api.event.player.AttackBlockCallback;
import net.minecraft.block.Block;
import net.minecraft.registry.Registries;
import net.minecraft.util.ActionResult;

public class BlockLogic {

    public static void init() {
        // DETECTOR DE RUPTURA (Minería)
        AttackBlockCallback.EVENT.register((player, world, hand, pos, direction) -> {
            if (!world.isClient) {
                Block block = world.getBlockState(pos).getBlock();
                String id = Registries.BLOCK.getId(block).getPath();
                
                AchievementClient.sendEvent(player.getUuidAsString(), "block_broken:" + id, 1);
                AchievementClient.sendEvent(player.getUuidAsString(), "block_broken", 1);

                // LOGROS DE ELITE (Materiales)
                if (id.contains("diamond_ore")) {
                    AchievementClient.sendEvent(player.getUuidAsString(), "mine_diamond", 1);
                }
                if (id.contains("ancient_debris")) {
                    AchievementClient.sendEvent(player.getUuidAsString(), "mine_ancient_debris", 1);
                }
            }
            return ActionResult.PASS;
        });
    }

    /**
     * Llamado desde BlockItemMixin para registrar colocación
     */
    public static void onBlockPlaced(String blockId, String playerUuid) {
        AchievementClient.sendEvent(playerUuid, "block_placed:" + blockId, 1);
        AchievementClient.sendEvent(playerUuid, "block_placed", 1);
        
        // LOGROS DE ARQUITECTO (Redstone)
        if (blockId.contains("redstone") || blockId.contains("repeater") || blockId.contains("comparator")) {
            AchievementClient.sendEvent(playerUuid, "redstone_placed", 1);
        }
    }
}
