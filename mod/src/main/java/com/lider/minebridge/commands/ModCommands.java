package com.lider.minebridge.commands;

import com.lider.minebridge.MineBridge;
import com.lider.minebridge.config.ModConfig;
import com.lider.minebridge.networking.SkinClient;
import com.mojang.brigadier.arguments.StringArgumentType;
import net.fabricmc.fabric.api.command.v2.CommandRegistrationCallback;
import net.minecraft.command.argument.EntityArgumentType;
import net.minecraft.server.command.CommandManager;
import net.minecraft.server.network.ServerPlayerEntity;
import net.minecraft.text.Text;

import java.util.Collection;

public class ModCommands {
    
    public static void init() {
        CommandRegistrationCallback.EVENT.register((dispatcher, registryAccess, environment) -> {
            
            // Base command: /minebridge (and alias /bridge)
            for (String cmdLiteral : new String[]{"minebridge", "bridge"}) {
                dispatcher.register(CommandManager.literal(cmdLiteral)
                    .requires(source -> source.hasPermissionLevel(4))
                    
                    // Config: url
                    .then(CommandManager.literal("url")
                        .then(CommandManager.argument("value", StringArgumentType.greedyString())
                            .executes(context -> updateUrl(context.getSource(), StringArgumentType.getString(context, "value")))
                        )
                    )
                    
                    // Config: key
                    .then(CommandManager.literal("key")
                        .then(CommandManager.argument("value", StringArgumentType.greedyString())
                            .executes(context -> updateKey(context.getSource(), StringArgumentType.getString(context, "value")))
                        )
                    )
                    
                    // Action: skin refresh [players]
                    .then(CommandManager.literal("skin")
                        .then(CommandManager.literal("refresh")
                            .executes(context -> refreshSelfSkin(context.getSource()))
                            .then(CommandManager.argument("targets", EntityArgumentType.players())
                                .executes(context -> refreshOtherSkins(context.getSource(), EntityArgumentType.getPlayers(context, "targets")))
                            )
                        )
                    )
                    
                    // Option 3: test
                    .then(CommandManager.literal("test")
                        .executes(context -> executeTest(context.getSource()))
                    )
                );
            }

            // Global direct alias: /skin refresh (for all players)
            dispatcher.register(CommandManager.literal("skin")
                .then(CommandManager.literal("refresh")
                    .executes(context -> refreshSelfSkin(context.getSource()))
                )
            );

            // Global direct alias: /testconnect
            dispatcher.register(CommandManager.literal("testconnect")
                .requires(source -> source.hasPermissionLevel(4))
                .executes(context -> executeTest(context.getSource()))
            );
        });
    }

    private static int refreshSelfSkin(net.minecraft.server.command.ServerCommandSource source) {
        try {
            ServerPlayerEntity player = source.getPlayerOrThrow();
            source.sendFeedback(() -> Text.literal("§e[MineBridge] Solicitando actualización de skin..."), false);
            SkinClient.syncSkin(player, () -> {
                source.sendFeedback(() -> Text.literal("§a[MineBridge] ✅ Tu skin ha sido actualizada."), false);
            });
            return 1;
        } catch (Exception e) {
            source.sendError(Text.literal("§c[MineBridge] Solo los jugadores pueden usar este comando."));
            return 0;
        }
    }

    private static int refreshOtherSkins(net.minecraft.server.command.ServerCommandSource source, Collection<ServerPlayerEntity> targets) {
        source.sendFeedback(() -> Text.literal("§e[MineBridge] Actualizando skins para " + targets.size() + " jugadores..."), true);
        for (ServerPlayerEntity player : targets) {
            SkinClient.syncSkin(player);
        }
        return targets.size();
    }

    private static int updateUrl(net.minecraft.server.command.ServerCommandSource source, String newUrl) {
        ModConfig.setBackendUrl(newUrl);
        if (MineBridge.getBackendClient() != null) {
            MineBridge.getBackendClient().updateBaseUrl(newUrl);
        }
        source.sendFeedback(() -> Text.literal("§a[MineBridge] URL del Backend actualizada a: §f" + newUrl), true);
        return 1;
    }

    private static int updateKey(net.minecraft.server.command.ServerCommandSource source, String newKey) {
        ModConfig.setApiKey(newKey);
        if (MineBridge.getBackendClient() != null) {
            MineBridge.getBackendClient().updateApiKey(newKey);
        }
        source.sendFeedback(() -> Text.literal("§a[MineBridge] API Key actualizada correctamente."), true);
        return 1;
    }

    private static int executeTest(net.minecraft.server.command.ServerCommandSource source) {
        source.sendFeedback(() -> Text.literal("§e[MineBridge] Probando conexión con el Backend..."), false);
        
        if (MineBridge.getBackendClient() == null) {
            source.sendError(Text.literal("§c[MineBridge] ERROR: El cliente de red no está inicializado. Usa /minebridge set-url primero."));
            return 0;
        }

        try {
            MineBridge.getBackendClient().testConnection().thenAccept(result -> {
                if (result == null) return;
                switch (result) {
                    case "SUCCESS":
                        source.sendFeedback(() -> Text.literal("§a[MineBridge] ✅ ¡Conexión Exitosa!"), true);
                        break;
                    case "CONFIG_ERROR":
                        source.sendError(Text.literal("§c[MineBridge] ❌ Error: Configuración incompleta."));
                        break;
                    case "UNAUTHORIZED":
                        source.sendError(Text.literal("§c[MineBridge] ❌ Error 401: API Key inválida."));
                        break;
                    default:
                        source.sendError(Text.literal("§c[MineBridge] ❌ Fallo en la conexión: " + result));
                        break;
                }
            }).exceptionally(ex -> {
                source.sendError(Text.literal("§c[MineBridge] ❌ Error de red: " + ex.getMessage()));
                return null;
            });
        } catch (Exception e) {
            source.sendError(Text.literal("§c[MineBridge] ❌ Error al iniciar la prueba: " + e.getMessage()));
        }
        return 1;
    }
}
