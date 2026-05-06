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
            GLFW.GLFW_KEY_M,
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
            if (client.player == null) return;

            // --- Tecla Marketplace (Independiente de isActive) ---
            while (marketplaceKey.wasPressed()) {
                if (Screen.hasShiftDown()) {
                    // Abrir PERFIL DE VENDEDOR (Shift + M)
                    MinecraftClient.getInstance().setScreen(new com.lider.minebridge.client.ui.MarketplaceProfileScreen());
                } else {
                    // Abrir pantalla de MERCADO GLOBAL (M)
                    com.lider.minebridge.networking.TradeClient.getOpenTrades().thenAccept(trades -> {
                        MinecraftClient.getInstance().execute(() -> {
                            MinecraftClient.getInstance().setScreen(new com.lider.minebridge.client.ui.MarketplaceGlobalScreen(trades));
                        });
                    });
                }
            }

            if (!isActive) return;
            
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

            // --- Chequeo de Dimensión ---
            String currentDim = client.world.getRegistryKey().getValue().toString();
            if (currentDim.contains("the_end")) {
                triggerAchievement("enter_dimension:minecraft:the_end", "El Fin de los Tiempos", "Has llegado al End.");
            } else if (currentDim.contains("the_nether")) {
                triggerAchievement("enter_dimension:minecraft:the_nether", "Inframundo", "Has llegado al Nether.");
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
                    if (!unlockedAchievementsSession.contains("DESCEND_MADNESS") && (client.player.hasStatusEffect(net.minecraft.entity.effect.StatusEffects.BLINDNESS) || client.player.hasStatusEffect(net.minecraft.entity.effect.StatusEffects.DARKNESS))) {
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
                if (!unlockedAchievementsSession.contains("FEAR_PARALYSIS") && client.player.hasStatusEffect(net.minecraft.entity.effect.StatusEffects.DARKNESS)) triggerAchievement("FEAR_PARALYSIS", "Parálisis del Miedo", "La oscuridad te consume.");
                if (!unlockedAchievementsSession.contains("MANY_EFFECTS") && client.player.getActiveStatusEffects().size() >= 10) triggerAchievement("MANY_EFFECTS", "Farmacia Ambulante", "10 efectos simultáneos.");
                
                if (!unlockedAchievementsSession.contains("BLOOD_SWEAT") && client.player.getHealth() <= 2.0f && client.player.getHungerManager().getFoodLevel() == 0 && client.player.isSprinting()) {
                    triggerAchievement("BLOOD_SWEAT", "Sudor y Sangre", "Corriendo por tu vida, hambriento y moribundo.");
                }
                
                // 4. Inventarios e Ítems (Delegado a ClientAchievementLogic)
                for (int i = 0; i < client.player.getInventory().size(); i++) {
                    com.lider.minebridge.events.ClientAchievementLogic.onInventoryCheck(client.player.getInventory().getStack(i));
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
        });
        
        // NOTA: El resto de eventos (Bloques, Entidades) se han movido a ClientAchievementLogic.init()
    }

    public static void triggerAchievement(String key, String title, String description) {
        com.lider.minebridge.networking.AchievementClient.triggerAchievement(key, title, description);
    }
}
