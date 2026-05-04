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
        "amethyst_cluster",
        "obsidian"
    );

    private static final Set<String> TRACKED_CROPS = Set.of(
        "wheat", "carrots", "potatoes",
        "nether_wart", "sugar_cane", "sweet_berry_bush",
        "melon", "pumpkin"
    );

    // Contadores de sesión detallados
    private static final ConcurrentHashMap<String, Integer> blockBrokenSession = new ConcurrentHashMap<>();
    private static final ConcurrentHashMap<String, Integer> blockBrokenStart = new ConcurrentHashMap<>();
    private static final ConcurrentHashMap<String, Integer> blockPlacedSession = new ConcurrentHashMap<>();
    private static final ConcurrentHashMap<String, Integer> cropsHarvestedSession = new ConcurrentHashMap<>();
    private static final ConcurrentHashMap<String, java.util.Map<String, Integer>> cropsSpecificSession = new ConcurrentHashMap<>();
    private static final ConcurrentHashMap<String, Integer> diamondsMinedSession = new ConcurrentHashMap<>();
    private static final ConcurrentHashMap<String, Integer> obsidianMinedSession = new ConcurrentHashMap<>();
    private static final ConcurrentHashMap<String, Integer> redstonePlacedSession = new ConcurrentHashMap<>();

    public static void setInitialStats(String uuid, int total) {
        blockBrokenStart.put(uuid, total);
    }

    public static void init() {
        // RUPTURA DE BLOQUES
        net.fabricmc.fabric.api.event.player.PlayerBlockBreakEvents.AFTER.register((world, player, pos, state, blockEntity) -> {
            if (world.isClient || !(player instanceof ServerPlayerEntity serverPlayer)) return;

            String uuid = serverPlayer.getUuidAsString();
            Block block = state.getBlock();
            String id = Registries.BLOCK.getId(block).getPath();

            // 2. MINERALES ESPECÍFICOS (Solo dejamos lo especial/meme)
            for (String ore : TRACKED_ORES) {
                if (id.contains(ore) && id.equals("obsidian")) {
                    int obs = obsidianMinedSession.merge(uuid, 1, Integer::sum);
                    if (obs == 1000) AchievementClient.sendEvent(uuid, "MEME_NO_AFECTO", 1);
                    break;
                }
            }

            // 3. CULTIVOS (Eliminado por ser intrusivo - Solo se guardan estadisticas al final)
        });

        // JUKEBOX Y COFRES DE ALDEA
        UseBlockCallback.EVENT.register((player, world, hand, hitResult) -> {
            if (!world.isClient && player instanceof ServerPlayerEntity serverPlayer) {
                Block block = world.getBlockState(hitResult.getBlockPos()).getBlock();
                String uuid = serverPlayer.getUuidAsString();

                // 2. Cofres (Aldea y Tesoro - Mantenemos por ser Especiales)
                if (block == net.minecraft.block.Blocks.CHEST) {
                    net.minecraft.server.world.ServerWorld sw = (net.minecraft.server.world.ServerWorld) world;
                    net.minecraft.util.math.BlockPos pos = hitResult.getBlockPos();
                    
                    if (sw.getStructureAccessor().getStructureContaining(pos, net.minecraft.registry.tag.StructureTags.VILLAGE).hasChildren()) {
                        AchievementClient.sendEvent(uuid, "PHILO_NECESSARY", 1);
                    }
                    
                    if (sw.getStructureAccessor().getStructureContaining(pos, net.minecraft.registry.tag.StructureTags.ON_TREASURE_MAPS).hasChildren()) {
                        AchievementClient.sendEvent(uuid, "MEME_VIBORA", 1);
                    }
                }
            }
            return ActionResult.PASS;
        });
    }

    public static void onBlockPlaced(String blockId, String playerUuid) {
        int total = blockPlacedSession.merge(playerUuid, 1, Integer::sum);
        
        // Thresholds Arquitectura (Architecture.py)
        if (total == 1000) AchievementClient.sendEvent(playerUuid, "ARCH_1", 1);
        if (total == 10000) AchievementClient.sendEvent(playerUuid, "ARCH_2", 1);
        if (total == 100000) AchievementClient.sendEvent(playerUuid, "ARCH_4", 1);

        // Thresholds Redstone (Redstone.py)
        if (blockId.contains("redstone") || blockId.contains("repeater") || blockId.contains("comparator") || blockId.contains("observer")) {
            int redstoneTotal = redstonePlacedSession.merge(playerUuid, 1, Integer::sum);
            if (redstoneTotal == 500) AchievementClient.sendEvent(playerUuid, "TECH_1", 1);
            if (redstoneTotal == 2500) AchievementClient.sendEvent(playerUuid, "TECH_2", 1);
            AchievementClient.sendEvent(playerUuid, "redstone_placed", 1);
        }
    }

    public static void onPlayerLeave(String uuid) {
        blockBrokenStart.remove(uuid);
        java.util.Map<String, Integer> stats = new java.util.HashMap<>();
        
        Integer obs = obsidianMinedSession.remove(uuid);
        if (obs != null) stats.put("obsidian_mined", obs);

        Integer redstone = redstonePlacedSession.remove(uuid);
        if (redstone != null) stats.put("redstone_placed", redstone);
        
        Integer broken = blockBrokenSession.remove(uuid);
        if (broken != null) stats.put("block_broken", broken);
        
        Integer placed = blockPlacedSession.remove(uuid);
        if (placed != null) stats.put("block_placed", placed);
        
        Integer crops = cropsHarvestedSession.remove(uuid);
        if (crops != null) stats.put("crop_harvested", crops);
        
        java.util.Map<String, Integer> specCrops = cropsSpecificSession.remove(uuid);
        if (specCrops != null) {
            for (java.util.Map.Entry<String, Integer> entry : specCrops.entrySet()) {
                stats.put("crop:minecraft:" + entry.getKey(), entry.getValue());
            }
        }

        if (!stats.isEmpty()) {
            AchievementClient.sendSessionSummary(uuid, stats);
        }
    }
}
