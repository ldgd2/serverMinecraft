package com.lider.minebridge.events.blocks;

import com.lider.minebridge.networking.AchievementClient;
import net.fabricmc.fabric.api.event.player.UseBlockCallback;
import net.minecraft.block.Block;
import net.minecraft.block.CropBlock;
import net.minecraft.block.NetherWartBlock;
import net.minecraft.block.SweetBerryBushBlock;
import net.minecraft.registry.Registries;
import net.minecraft.server.network.ServerPlayerEntity;
import net.minecraft.util.ActionResult;

import java.util.Set;
import java.util.concurrent.ConcurrentHashMap;

public class BlockLogic {

    // Bloques que SÍ importan para logros — no enviamos nada más
    private static final Set<String> TRACKED_ORES = Set.of(
        "diamond_ore", "deepslate_diamond_ore",
        "ancient_debris",
        "emerald_ore", "deepslate_emerald_ore",
        "nether_gold_ore",
        "amethyst_cluster"
    );

    private static final Set<String> TRACKED_CROPS = Set.of(
        "wheat", "carrots", "potatoes",
        "nether_wart", "sugar_cane", "sweet_berry_bush",
        "melon", "pumpkin"
    );

    // Acumulador local por jugador: bloques rotos en esta sesión
    // Solo se envía en lotes de 50 o al desconectarse
    private static final ConcurrentHashMap<String, Integer> blockBrokenAccum = new ConcurrentHashMap<>();

    public static void init() {
        // RUPTURA DE BLOQUES — solo eventos relevantes para logros
        net.fabricmc.fabric.api.event.player.PlayerBlockBreakEvents.AFTER.register((world, player, pos, state, blockEntity) -> {
            if (world.isClient || !(player instanceof ServerPlayerEntity serverPlayer)) return;

            String uuid = serverPlayer.getUuidAsString();
            Block block = state.getBlock();
            String id = Registries.BLOCK.getId(block).getPath();

            // 1. MINER ACHIEVEMENTS — acumulamos localmente y solo enviamos cada 100 bloques
            //    Así evitamos un evento por cada bloque de piedra/tierra
            int count = blockBrokenAccum.merge(uuid, 1, Integer::sum);
            if (count % 100 == 0) {
                // Enviamos el acumulado cuando llega a múltiplos de 100
                AchievementClient.sendEvent(uuid, "block_broken", 100);
            }

            // 2. MINERALES ESPECÍFICOS — solo los importantes (diamond, debris, etc.)
            for (String ore : TRACKED_ORES) {
                if (id.contains(ore)) {
                    if (ore.contains("diamond")) AchievementClient.sendEvent(uuid, "mine_diamond", 1);
                    else if (ore.contains("ancient_debris")) AchievementClient.sendEvent(uuid, "mine_ancient_debris", 1);
                    else if (ore.contains("emerald")) AchievementClient.sendEvent(uuid, "mine_emerald", 1);
                    else if (ore.contains("amethyst")) AchievementClient.sendEvent(uuid, "mine_amethyst", 1);
                    break;
                }
            }

            // 3. CULTIVOS — solo si están maduros (evita contar replantado)
            for (String crop : TRACKED_CROPS) {
                if (id.contains(crop)) {
                    boolean isMature = false;
                    if (block instanceof CropBlock c) isMature = c.isMature(state);
                    else if (block instanceof NetherWartBlock) isMature = state.get(NetherWartBlock.AGE) == 3;
                    else if (block instanceof SweetBerryBushBlock) isMature = state.get(SweetBerryBushBlock.AGE) == 3;
                    else isMature = true; // sugar_cane, melon, pumpkin

                    if (isMature) {
                        AchievementClient.sendEvent(uuid, "crop_harvested", 1);
                        AchievementClient.sendEvent(uuid, "crop:minecraft:" + id, 1);
                    }
                    break;
                }
            }
        });

        // JUKEBOX — event-driven, sin tick
        UseBlockCallback.EVENT.register((player, world, hand, hitResult) -> {
            if (!world.isClient && player instanceof ServerPlayerEntity serverPlayer) {
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

    /** Flush del acumulador al desconectarse (para no perder el residuo) */
    public static void onPlayerLeave(String uuid) {
        Integer remaining = blockBrokenAccum.remove(uuid);
        if (remaining != null && remaining % 50 != 0) {
            int residual = remaining % 50;
            if (residual > 0) {
                AchievementClient.sendEvent(uuid, "block_broken", residual);
            }
        }
    }

    /** Llamado desde BlockItemMixin para registrar colocación de redstone */
    public static void onBlockPlaced(String blockId, String playerUuid) {
        // Solo nos interesa redstone para el logro de arquitecto
        if (blockId.contains("redstone") || blockId.contains("repeater") || blockId.contains("comparator")) {
            AchievementClient.sendEvent(playerUuid, "redstone_placed", 1);
        }
        // block_placed genérico eliminado — muy alto volumen, sin logros directos de 1:1
    }
}
