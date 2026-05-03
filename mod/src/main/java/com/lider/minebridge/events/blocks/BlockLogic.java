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

            // 1. MINERÍA GENERAL (Basado en Mining.py)
            int sessionCount = blockBrokenSession.merge(uuid, 1, Integer::sum);
            int totalCount = blockBrokenStart.getOrDefault(uuid, 0) + sessionCount;

            if (totalCount == 100) AchievementClient.sendEvent(uuid, "MINER_1", 1);
            if (totalCount == 500) AchievementClient.sendEvent(uuid, "MINER_2", 1);
            if (totalCount == 1000) AchievementClient.sendEvent(uuid, "MINER_3", 1);
            if (totalCount == 5000) AchievementClient.sendEvent(uuid, "MINER_4", 1);
            if (totalCount == 10000) AchievementClient.sendEvent(uuid, "MINER_5", 1);
            if (totalCount == 50000) AchievementClient.sendEvent(uuid, "MINER_ELITE", 1);

            // 2. MINERALES ESPECÍFICOS
            for (String ore : TRACKED_ORES) {
                if (id.contains(ore)) {
                    if (ore.contains("diamond")) {
                        int dm = diamondsMinedSession.merge(uuid, 1, Integer::sum);
                        if (dm == 1) AchievementClient.sendEvent(uuid, "MINE_DIAMOND", 1);
                        if (dm == 64) AchievementClient.sendEvent(uuid, "MINE_DIAMOND_64", 1);
                        AchievementClient.sendEvent(uuid, "mine_diamond", 1);
                    } 
                    else if (ore.contains("ancient_debris")) AchievementClient.sendEvent(uuid, "mine_ancient_debris", 1);
                    else if (ore.contains("emerald")) AchievementClient.sendEvent(uuid, "mine_emerald", 1);
                    else if (ore.contains("amethyst")) AchievementClient.sendEvent(uuid, "mine_amethyst", 1);
                    else if (ore.contains("gold")) AchievementClient.sendEvent(uuid, "mine_gold", 1);
                    else if (id.equals("obsidian")) {
                        int obs = obsidianMinedSession.merge(uuid, 1, Integer::sum);
                        if (obs == 1000) AchievementClient.sendEvent(uuid, "MEME_NO_AFECTO", 1);
                        AchievementClient.sendEvent(uuid, "mine_obsidian", 1);
                    }
                    break;
                }
            }

            // 3. CULTIVOS (Farming.py)
            for (String crop : TRACKED_CROPS) {
                if (id.contains(crop)) {
                    boolean isMature = false;
                    if (block instanceof CropBlock c) isMature = c.isMature(state);
                    else if (block instanceof NetherWartBlock) isMature = state.get(NetherWartBlock.AGE) == 3;
                    else if (block instanceof SweetBerryBushBlock) isMature = state.get(SweetBerryBushBlock.AGE) == 3;
                    else isMature = true;

                    if (isMature) {
                        int totalFarming = cropsHarvestedSession.merge(uuid, 1, Integer::sum);
                        java.util.Map<String, Integer> pCrops = cropsSpecificSession.computeIfAbsent(uuid, k -> new java.util.HashMap<>());
                        int specCount = pCrops.merge(id, 1, Integer::sum);

                        // Thresholds generales
                        if (totalFarming == 1000) AchievementClient.sendEvent(uuid, "FARM_1", 1);
                        if (totalFarming == 50000) AchievementClient.sendEvent(uuid, "FARM_3", 1);

                        // Thresholds específicos
                        AchievementClient.sendEvent(uuid, "crop:minecraft:" + id, 1);
                        if (id.equals("potatoes") && specCount == 500) AchievementClient.sendEvent(uuid, "FARM_POTATO", 1);
                        if (id.equals("carrots") && specCount == 500) AchievementClient.sendEvent(uuid, "FARM_CARROT", 1);
                        if (id.equals("wheat") && specCount == 1000) AchievementClient.sendEvent(uuid, "FARM_WHEAT", 1);
                    }
                    break;
                }
            }
        });

        // JUKEBOX Y COFRES DE ALDEA
        UseBlockCallback.EVENT.register((player, world, hand, hitResult) -> {
            if (!world.isClient && player instanceof ServerPlayerEntity serverPlayer) {
                Block block = world.getBlockState(hitResult.getBlockPos()).getBlock();
                String uuid = serverPlayer.getUuidAsString();

                // 1. Tocadiscos
                if (block instanceof net.minecraft.block.JukeboxBlock) {
                    net.minecraft.item.ItemStack stack = player.getStackInHand(hand);
                    if (stack.get(net.minecraft.component.DataComponentTypes.JUKEBOX_PLAYABLE) != null) {
                        AchievementClient.sendEvent(uuid, "music_disc_played", 1);
                        AchievementClient.sendEvent(uuid, "MISC_MUSIC", 1);
                    }
                }

                // 2. Cofres (Aldea y Tesoro)
                if (block == net.minecraft.block.Blocks.CHEST) {
                    net.minecraft.server.world.ServerWorld sw = (net.minecraft.server.world.ServerWorld) world;
                    // Aldea
                    if (sw.getStructureAccessor().getStructureAt(hitResult.getBlockPos(), net.minecraft.registry.tag.StructureTags.VILLAGE).isValid()) {
                        AchievementClient.sendEvent(uuid, "loot_village_chest", 1);
                        AchievementClient.sendEvent(uuid, "PHILO_NECESSARY", 1);
                    }
                    // Tesoro Enterrado
                    if (sw.getStructureAccessor().getStructureAt(hitResult.getBlockPos(), net.minecraft.registry.tag.StructureTags.BURIED_TREASURE).isValid()) {
                        AchievementClient.sendEvent(uuid, "buried_treasure_found", 1);
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
