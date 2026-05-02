package com.lider.minebridge.events.blocks;

import com.lider.minebridge.networking.AchievementClient;
import net.fabricmc.fabric.api.event.player.AttackBlockCallback;
import net.minecraft.block.Block;
import net.minecraft.registry.Registries;
import net.minecraft.util.ActionResult;

public class BlockLogic {

    public static void init() {
        // DETECTOR DE RUPTURA REAL (Minería y Agricultura)
        net.fabricmc.fabric.api.event.player.PlayerBlockBreakEvents.AFTER.register((world, player, pos, state, blockEntity) -> {
            if (!world.isClient && player instanceof net.minecraft.server.network.ServerPlayerEntity serverPlayer) {
                Block block = state.getBlock();
                String id = Registries.BLOCK.getId(block).getPath();
                
                AchievementClient.sendEvent(serverPlayer.getUuidAsString(), "block_broken:" + id, 1);
                AchievementClient.sendEvent(serverPlayer.getUuidAsString(), "block_broken", 1);

                // LOGROS DE ELITE (Materiales)
                if (id.contains("diamond_ore")) {
                    AchievementClient.sendEvent(serverPlayer.getUuidAsString(), "mine_diamond", 1);
                }
                if (id.contains("ancient_debris")) {
                    AchievementClient.sendEvent(serverPlayer.getUuidAsString(), "mine_ancient_debris", 1);
                }

                // CULTIVOS AGRÍCOLAS
                if (id.contains("wheat") || id.contains("carrots") || id.contains("potatoes") || id.contains("nether_wart") || id.contains("sugar_cane") || id.contains("sweet_berry_bush")) {
                    boolean isMature = false;
                    if (block instanceof net.minecraft.block.CropBlock crop) {
                        isMature = crop.isMature(state);
                    } else if (block instanceof net.minecraft.block.NetherWartBlock) {
                        isMature = state.get(net.minecraft.block.NetherWartBlock.AGE) == 3;
                    } else if (block instanceof net.minecraft.block.SweetBerryBushBlock) {
                        isMature = state.get(net.minecraft.block.SweetBerryBushBlock.AGE) == 3;
                    } else if (block instanceof net.minecraft.block.SugarCaneBlock || id.contains("sugar_cane")) {
                        isMature = true; // La caña de azúcar cuenta por defecto al romperse
                    }

                    if (isMature) {
                        String cropId = id;
                        if (id.equals("sweet_berry_bush")) cropId = "sweet_berries";
                        
                        AchievementClient.sendEvent(serverPlayer.getUuidAsString(), "crop_harvested", 1);
                        AchievementClient.sendEvent(serverPlayer.getUuidAsString(), "crop:minecraft:" + cropId, 1);
                    }
                }
            }
        });

        // DETECTOR DE USO DE BLOQUES (Tocadiscos)
        net.fabricmc.fabric.api.event.player.UseBlockCallback.EVENT.register((player, world, hand, hitResult) -> {
            if (!world.isClient && player instanceof net.minecraft.server.network.ServerPlayerEntity serverPlayer) {
                Block block = world.getBlockState(hitResult.getBlockPos()).getBlock();
                if (block instanceof net.minecraft.block.JukeboxBlock) {
                    net.minecraft.item.ItemStack stack = player.getStackInHand(hand);
                    if (stack.get(net.minecraft.component.DataComponentTypes.JUKEBOX_PLAYABLE) != null) {
                        AchievementClient.sendEvent(serverPlayer.getUuidAsString(), "music_disc_played", 1);
                    }
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
