package com.lider.minebridge.events;

import com.lider.minebridge.networking.AchievementClient;
import net.fabricmc.fabric.api.event.player.PlayerBlockBreakEvents;
import net.fabricmc.fabric.api.event.player.UseBlockCallback;
import net.fabricmc.fabric.api.event.player.UseEntityCallback;
import net.minecraft.block.Block;
import net.minecraft.block.Blocks;
import net.minecraft.entity.passive.SheepEntity;
import net.minecraft.item.ItemStack;
import net.minecraft.item.Items;
import net.minecraft.registry.Registries;
import net.minecraft.text.Text;
import net.minecraft.util.ActionResult;
import net.minecraft.util.DyeColor;
import net.minecraft.world.World;

import java.util.HashSet;
import java.util.Set;
import java.util.concurrent.ConcurrentHashMap;

public class ClientAchievementLogic {

    private static final ConcurrentHashMap<String, Integer> stats = new ConcurrentHashMap<>();

    public static void init() {
        // RUPTURA DE BLOQUES
        PlayerBlockBreakEvents.AFTER.register((world, player, pos, state, blockEntity) -> {
            if (!world.isClient) return;
            
            Block block = state.getBlock();
            String id = Registries.BLOCK.getId(block).getPath();
            
            incrementStat("blocks_broken");
            
            if (id.equals("obsidian")) {
                if (incrementStat("obsidian_mined") == 1000) {
                    AchievementClient.triggerAchievement("MEME_NO_AFECTO", "Falta de Afecto", "Picaste 1000 de obsidiana.");
                }
            }
            
            if (id.contains("diamond")) {
                if (incrementStat("diamonds_mined") == 10) {
                    AchievementClient.triggerAchievement("DIAMOND_HUNTER", "Cazador de Diamantes", "Has picado 10 diamantes.");
                }
            }

            if (id.equals("soul_sand") || id.equals("soul_soil")) {
                if (incrementStat("soul_mined") == 500) {
                    AchievementClient.triggerAchievement("HARVEST_SOULS", "Cosecha de Almas", "El lamento de 500 almas liberadas.");
                }
            }
        });

        // INTERACCIÓN CON ENTIDADES
        UseEntityCallback.EVENT.register((player, world, hand, entity, hitResult) -> {
            if (world.isClient) {
                if (entity instanceof SheepEntity sheep && sheep.getColor() == DyeColor.PINK) {
                    AchievementClient.triggerAchievement("pink_sheep_found", "Oveja Rosa", "Encontraste la mítica oveja rosa.");
                }
                
                if (Registries.ENTITY_TYPE.getId(entity.getType()).getPath().contains("wandering_trader")) {
                    int trades = incrementStat("trader_trades");
                    if (trades == 1) AchievementClient.triggerAchievement("wandering_trader_trade", "Negociante", "Comerciaste con el errante.");
                    if (trades == 10) AchievementClient.triggerAchievement("TRADER_10", "Cliente Frecuente", "Has hablado 10 veces con errantes.");
                }
            }
            return ActionResult.PASS;
        });

        // USO DE BLOQUES
        UseBlockCallback.EVENT.register((player, world, hand, hitResult) -> {
            if (world.isClient) {
                Block block = world.getBlockState(hitResult.getBlockPos()).getBlock();
                if (block.getTranslationKey().contains("bed") && world.getRegistryKey() == World.NETHER) {
                    AchievementClient.triggerAchievement("NETHER_SLEEP", "Sueño Explosivo", "Intentaste dormir en el Nether.");
                }
            }
            return ActionResult.PASS;
        });
    }

    public static void onBlockPlaced(Block block) {
        String id = Registries.BLOCK.getId(block).getPath();
        int total = incrementStat("blocks_placed");
        
        if (total == 1000) AchievementClient.triggerAchievement("ARCH_1", "Arquitecto Novel", "Has colocado 1000 bloques.");
        if (total == 10000) AchievementClient.triggerAchievement("ARCH_2", "Maestro Constructor", "Has colocado 10000 bloques.");

        if (id.contains("redstone") || id.contains("repeater") || id.contains("comparator") || id.contains("observer")) {
            int redstone = incrementStat("redstone_placed");
            if (redstone == 500) AchievementClient.triggerAchievement("TECH_1", "Iniciación Técnica", "Has colocado 500 componentes de Redstone.");
            if (redstone == 2500) AchievementClient.triggerAchievement("TECH_2", "Ingeniero Industrial", "Has colocado 2500 componentes de Redstone.");
        }
    }

    public static void onItemTossed(ItemStack stack) {
        if (stack.getItem() == Items.DIAMOND && stack.getCount() >= 64) {
            AchievementClient.triggerAchievement("MEME_HUMILDAD", "Humildad de Diamante", "Tiraste un stack de diamantes al suelo.");
        }
    }

    public static void onItemEnchanted() {
        AchievementClient.triggerAchievement("item_enchanted", "Poder Arcano", "Has encantado un ítem.");
    }

    public static void onAnvilUse() {
        AchievementClient.triggerAchievement("anvil_use", "Forjador", "Has usado el yunque.");
    }

    public static void onInventoryCheck(ItemStack stack) {
        if (stack.isEmpty()) return;
        if (stack.getItem() == Items.DRAGON_EGG) {
            AchievementClient.triggerAchievement("has_dragon_egg", "Dueño del Dragón", "Tienes el huevo de dragón.");
        }
        if (stack.getItem() == Items.POISONOUS_POTATO) {
            AchievementClient.triggerAchievement("item_acquired:minecraft:poisonous_potato", "Mala Suerte", "Conseguiste una patata venenosa.");
        }
        if (stack.getItem() == Items.COOKED_CHICKEN && stack.getCount() >= 64) {
            AchievementClient.triggerAchievement("cooked_chicken_stack", "KFC King", "Tienes un stack de pollo cocinado.");
        }
    }

    private static int incrementStat(String key) {
        return stats.merge(key, 1, Integer::sum);
    }
}
