package com.lider.minebridge.events.modules;

import com.lider.minebridge.networking.AchievementClient;
import net.minecraft.block.Block;
import net.minecraft.registry.Registries;
import net.minecraft.server.network.ServerPlayerEntity;

public class BlockEvents {
    public static void onBlockBroken(ServerPlayerEntity player, Block block) {
        String blockId = Registries.BLOCK.getId(block).toString();
        AchievementClient.sendEvent(player.getUuidAsString(), "block_broken:" + blockId, 1);
    }
}
