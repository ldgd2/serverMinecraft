package com.lider.minebridge.client;

import com.lider.minebridge.networking.payload.AchievementUnlockPayload;
import net.fabricmc.fabric.api.client.event.lifecycle.v1.ClientTickEvents;
import net.fabricmc.fabric.api.client.networking.v1.ClientPlayNetworking;
import net.fabricmc.fabric.api.event.player.UseEntityCallback;
import net.fabricmc.fabric.api.event.player.UseBlockCallback;
import net.fabricmc.fabric.api.event.player.PlayerBlockBreakEvents;
import net.minecraft.block.Block;
import net.minecraft.client.MinecraftClient;
import net.minecraft.entity.passive.SheepEntity;
import net.minecraft.registry.Registries;
import net.minecraft.text.Text;
import net.minecraft.util.ActionResult;
import net.minecraft.util.DyeColor;
import net.minecraft.client.option.KeyBinding;
import net.minecraft.client.util.InputUtil;
import net.fabricmc.fabric.api.client.keybinding.v1.KeyBindingHelper;
import org.lwjgl.glfw.GLFW;
import com.lider.minebridge.networking.payload.MarketplaceRequestPayload;
import net.minecraft.client.gui.screen.Screen;

import net.fabricmc.fabric.api.client.networking.v1.ClientPlayConnectionEvents;
import net.fabricmc.fabric.api.client.networking.v1.ClientPlayConnectionEvents;
import net.fabricmc.fabric.api.client.event.lifecycle.v1.ClientTickEvents;
import net.fabricmc.fabric.api.event.player.PlayerBlockBreakEvents;
import net.fabricmc.fabric.api.event.player.UseEntityCallback;
import net.fabricmc.fabric.api.client.item.v1.ItemTooltipCallback;
import net.minecraft.client.MinecraftClient;
import net.minecraft.block.Block;
import net.minecraft.entity.passive.SheepEntity;
import net.minecraft.entity.effect.StatusEffects;
import net.minecraft.registry.Registries;
import net.minecraft.text.Text;
import net.minecraft.util.ActionResult;
import net.minecraft.util.DyeColor;
import net.minecraft.world.World;

import java.util.HashSet;
import java.util.Set;
import java.util.concurrent.ConcurrentHashMap;

public class ClientEvents {
    private static final Set<String> unlockedAchievementsSession = new HashSet<>();
    private static final ConcurrentHashMap<String, Integer> blockBrokenSession = new ConcurrentHashMap<>();
    private static final ConcurrentHashMap<String, Integer> traderTrades = new ConcurrentHashMap<>();
    
    private static boolean isActive = false;
    private static boolean wasDead = false;
    
    private static int tickCounter = 0;
    
    public static KeyBinding marketplaceKey;
    
    public static void init() {
        com.lider.minebridge.config.ClientConfig.load();
        com.lider.minebridge.events.ClientAchievementLogic.init();
        
        marketplaceKey = KeyBindingHelper.registerKeyBinding(new KeyBinding(
            "key.minebridge.marketplace",
            InputUtil.Type.KEYSYM,
            GLFW.GLFW_KEY_PERIOD,
            "category.minebridge"
        ));
        ClientPlayConnectionEvents.JOIN.register((handler, sender, client) -> {
            isActive = ClientPlayNetworking.canSend(AchievementUnlockPayload.ID);
            if (isActive) {
                unlockedAchievementsSession.clear();
                blockBrokenSession.clear();
                traderTrades.clear();
                wasDead = false;
                tickCounter = 0;
            }
            com.lider.minebridge.client.gui.UpdateTimerHud.startTimer(-1);
        });

        ClientPlayConnectionEvents.DISCONNECT.register((handler, client) -> {
            isActive = false;
        });

        com.lider.minebridge.client.gui.UpdateTimerHud.register();

        net.fabricmc.fabric.api.client.networking.v1.ClientPlayNetworking.registerGlobalReceiver(com.lider.minebridge.networking.payload.UpdateCountdownPayload.ID, (payload, context) -> {
            context.client().execute(() -> {
                com.lider.minebridge.client.gui.UpdateTimerHud.startTimer(payload.seconds());
            });
        });

        net.fabricmc.fabric.api.client.networking.v1.ClientPlayNetworking.registerGlobalReceiver(com.lider.minebridge.networking.payload.SyncSkinPayload.ID, (payload, context) -> {
            context.client().execute(() -> {
                com.lider.minebridge.client.ClientSkinManager.updateSkin(payload.playerId(), payload.value(), payload.signature());
            });
        });

        ClientTickEvents.END_CLIENT_TICK.register(client -> {
            if (!isActive || client.player == null) return;
            
            tickCounter++;
            com.lider.minebridge.client.gui.UpdateTimerHud.tick();
            
            // ==========================================
            // CHEQUEOS LIGEROS (Cada Tick)
            // ==========================================
            
            if (client.player.isDead() && !wasDead) {
                wasDead = true;
                if (client.player.getY() < -64) {
                    boolean isFull = true;
                    for (int i = 0; i < client.player.getInventory().main.size(); i++) {
                        if (client.player.getInventory().main.get(i).isEmpty()) { isFull = false; break; }
                    }
                    if (isFull) triggerAchievement("MEME_VOID_STARK", "Sr Stark, no me quiero ir", "Moriste en el vacío con el inventario lleno.");
                }
                boolean hasTotem = client.player.getInventory().contains(new net.minecraft.item.ItemStack(net.minecraft.item.Items.TOTEM_OF_UNDYING));
                if (hasTotem && client.player.getMainHandStack().getItem() != net.minecraft.item.Items.TOTEM_OF_UNDYING 
                    && client.player.getOffHandStack().getItem() != net.minecraft.item.Items.TOTEM_OF_UNDYING) {
                    triggerAchievement("die_with_totem_in_inv", "Olvidadizo", "Moriste teniendo un tótem guardado.");
                }
            } else if (!client.player.isDead()) {
                wasDead = false;
                if (client.player.fallDistance > 30 && client.player.getHealth() > 0 && client.player.getHealth() <= 2.0f) {
                    triggerAchievement("clutch_survival", "Sobreviviente Nato", "Sobreviviste a una caída enorme a medio corazón.");
                }
            }

            // ==========================================
            // CHEQUEOS PESADOS (1 Vez por Segundo = 20 Ticks)
            // ==========================================
            if (tickCounter % 20 == 0) {
                // 1. XP Level
                if (!unlockedAchievementsSession.contains("die_with_100_lvl") && client.player.experienceLevel >= 100) {
                    triggerAchievement("die_with_100_lvl", "¡Nivel 100!", "Llegaste al nivel 100 de XP.");
                }
                
                // 2. Altura y Abismos
                if (!unlockedAchievementsSession.contains("EVEREST") && client.player.getY() >= 315) {
                    triggerAchievement("EVEREST", "Everest", "Llegaste a la cima del mundo.");
                }
                
                if (client.player.getY() <= -60) {
                    if (!unlockedAchievementsSession.contains("DESCEND_MADNESS") && (client.player.hasStatusEffect(StatusEffects.BLINDNESS) || client.player.hasStatusEffect(StatusEffects.DARKNESS))) {
                        triggerAchievement("DESCEND_MADNESS", "Descendiendo a la Locura", "En lo profundo y ciego, el abismo te devuelve la mirada.");
                    }
                    if (!unlockedAchievementsSession.contains("EDGE_REASON") && client.player.getMainHandStack().getItem() == net.minecraft.item.Items.TOTEM_OF_UNDYING && 
                        client.player.getOffHandStack().getItem() == net.minecraft.item.Items.TOTEM_OF_UNDYING) {
                        triggerAchievement("EDGE_REASON", "El Límite de la Razón", "Aferrado a la vida en el lecho de roca con dos tótems.");
                    }
                }

                if (!unlockedAchievementsSession.contains("FATHOMLESS_ABYSS") && client.player.getY() <= 0 && client.player.getAir() <= 0 && client.player.getHealth() <= 6.0f) {
                    triggerAchievement("FATHOMLESS_ABYSS", "Abismo Insondable", "Ahogándote en las profundidades de la desesperación.");
                }

                // 3. Efectos y Estados
                if (!unlockedAchievementsSession.contains("FEAR_PARALYSIS") && client.player.hasStatusEffect(StatusEffects.DARKNESS)) triggerAchievement("FEAR_PARALYSIS", "Parálisis del Miedo", "La oscuridad te consume.");
                if (!unlockedAchievementsSession.contains("MANY_EFFECTS") && client.player.getActiveStatusEffects().size() >= 10) triggerAchievement("MANY_EFFECTS", "Farmacia Ambulante", "10 efectos simultáneos.");
                
                if (!unlockedAchievementsSession.contains("BLOOD_SWEAT") && client.player.getHealth() <= 2.0f && client.player.getHungerManager().getFoodLevel() == 0 && client.player.isSprinting()) {
                    triggerAchievement("BLOOD_SWEAT", "Sudor y Sangre", "Corriendo por tu vida, hambriento y moribundo.");
                }

                // 4. Inventarios e Ítems
                if (!unlockedAchievementsSession.contains("has_dragon_egg") && client.player.getInventory().contains(new net.minecraft.item.ItemStack(net.minecraft.item.Items.DRAGON_EGG))) {
                    triggerAchievement("has_dragon_egg", "Dueño del Dragón", "Tienes el huevo de dragón.");
                }
                
                if (!unlockedAchievementsSession.contains("IMMINENT_MASSACRE")) {
                    int weaponCount = 0;
                    for (int i = 0; i < 9; i++) {
                        String itemName = client.player.getInventory().getStack(i).getItem().getTranslationKey();
                        if (itemName.contains("sword") || itemName.contains("axe")) weaponCount++;
                    }
                    if (weaponCount == 9) triggerAchievement("IMMINENT_MASSACRE", "Masacre Inminente", "Un arsenal de dolor listo en tus manos.");
                }

                // 5. Jugadores Cercanos (MEME_ANTOJEN)
                if (!unlockedAchievementsSession.contains("MEME_ANTOJEN") && client.player.getMainHandStack().getItem() == net.minecraft.item.Items.CAKE && client.world != null) {
                    long nearby = client.world.getPlayers().stream().filter(p -> p != client.player && p.squaredDistanceTo(client.player) < 64.0).count();
                    if (nearby >= 5) triggerAchievement("MEME_ANTOJEN", "¡Antojen!", "Sosteniendo pastel ante 5 personas.");
                }
            }

            // --- Tecla Marketplace ---
            while (marketplaceKey.wasPressed()) {
                if (Screen.hasShiftDown()) {
                    // Abrir pantalla de CREACIÓN
                    MinecraftClient.getInstance().setScreen(new com.lider.minebridge.client.ui.MarketplaceCreationScreen());
                } else {
                    // Abrir pantalla de MERCADO GLOBAL (Fetch desde backend)
                    com.lider.minebridge.networking.TradeClient.getOpenTrades().thenAccept(trades -> {
                        if (ClientPlayNetworking.canSend(MarketplaceRequestPayload.ID)) {
                            ClientPlayNetworking.send(new MarketplaceRequestPayload(trades.toString()));
                        }
                    });
                }
            }
        });

        PlayerBlockBreakEvents.AFTER.register((world, player, pos, state, blockEntity) -> {
            if (!isActive || !world.isClient) return;

            Block block = state.getBlock();
            String id = Registries.BLOCK.getId(block).getPath();
            
            int total = blockBrokenSession.merge(id, 1, Integer::sum);
            
            if (id.equals("obsidian") && total == 1000) {
                triggerAchievement("MEME_NO_AFECTO", "Falta de Afecto", "Picaste 1000 de obsidiana.");
            }
            if ((id.equals("soul_sand") || id.equals("soul_soil")) && total == 500) {
                triggerAchievement("HARVEST_SOULS", "Cosecha de Almas", "El lamento de 500 almas liberadas por tu pico.");
            }
        });

        UseEntityCallback.EVENT.register((player, world, hand, entity, hitResult) -> {
            if (isActive && world.isClient) {
                if (entity instanceof SheepEntity sheep && sheep.getColor() == DyeColor.PINK) {
                    triggerAchievement("pink_sheep_found", "Oveja Rosa", "Encontraste la mítica oveja rosa.");
                }
                if (Registries.ENTITY_TYPE.getId(entity.getType()).getPath().contains("wandering_trader")) {
                    int trades = traderTrades.merge(player.getUuidAsString(), 1, Integer::sum);
                    if (trades == 1) triggerAchievement("wandering_trader_trade", "Negociante", "Comerciaste con el errante.");
                    if (trades == 10) triggerAchievement("TRADER_10", "Cliente Frecuente", "Has hablado 10 veces con errantes.");
                }
            }
            return ActionResult.PASS;
        });
    }

    public static final int COLOR_COMMON = 0xAAAAAA;
    public static final int COLOR_UNCOMMON = 0x55FF55;
    public static final int COLOR_RARE = 0x5555FF;
    public static final int COLOR_EPIC = 0xAA00AA;
    public static final int COLOR_LEGENDARY = 0xFFAA00;
    public static final int COLOR_MYTHIC = 0xAA0000;

    private static int getColorForKey(String key) {
        return switch (key) {
            case "EDGE_REASON" -> COLOR_MYTHIC;
            case "DESCEND_MADNESS", "TIME_LEGEND", "TIME_ANCIENT", "DOMINATOR" -> COLOR_LEGENDARY;
            case "HARVEST_SOULS", "FATHOMLESS_ABYSS" -> COLOR_EPIC;
            case "BLOOD_SWEAT", "IMMINENT_MASSACRE" -> COLOR_RARE;
            case "MEME_VOID_STARK", "MEME_NO_AFECTO", "EVEREST" -> COLOR_UNCOMMON;
            default -> COLOR_COMMON;
        };
    }

    public static void triggerAchievement(String key, String title, String description) {
        if (unlockedAchievementsSession.contains(key)) {
            return;
        }
        unlockedAchievementsSession.add(key);

        MinecraftClient client = MinecraftClient.getInstance();
        if (client != null && client.getToastManager() != null) {
            int color = getColorForKey(key);
            client.getToastManager().add(new AchievementToast(Text.of(title), Text.of(description), color));
        }

        // Send payload to server
        if (ClientPlayNetworking.canSend(AchievementUnlockPayload.ID)) {
            ClientPlayNetworking.send(new AchievementUnlockPayload(key));
        }
    }
}
