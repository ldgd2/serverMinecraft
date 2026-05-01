package com.lider.minebridge.commands;

import com.lider.minebridge.MineBridge;
import com.lider.minebridge.config.ModConfig;
import com.mojang.brigadier.arguments.StringArgumentType;
import net.fabricmc.fabric.api.command.v2.CommandRegistrationCallback;
import net.minecraft.server.command.CommandManager;
import net.minecraft.text.Text;

public class ModCommands {
    
    public static void init() {
        CommandRegistrationCallback.EVENT.register((dispatcher, registryAccess, environment) -> {
            
            // Base command: /minebridge (and alias /bridge)
            for (String cmdLiteral : new String[]{"minebridge", "bridge"}) {
                dispatcher.register(CommandManager.literal(cmdLiteral)
                    .requires(source -> source.hasPermissionLevel(4))
                    
                    // Option 1: url <url> or set-url <url>
                    .then(CommandManager.literal("url")
                        .then(CommandManager.argument("value", StringArgumentType.greedyString())
                            .executes(context -> updateUrl(context.getSource(), StringArgumentType.getString(context, "value")))
                        )
                    )
                    .then(CommandManager.literal("set-url")
                        .then(CommandManager.argument("value", StringArgumentType.greedyString())
                            .executes(context -> updateUrl(context.getSource(), StringArgumentType.getString(context, "value")))
                        )
                    )
                    
                    // Option 2: key <key> or set-key <key>
                    .then(CommandManager.literal("key")
                        .then(CommandManager.argument("value", StringArgumentType.greedyString())
                            .executes(context -> updateKey(context.getSource(), StringArgumentType.getString(context, "value")))
                        )
                    )
                    .then(CommandManager.literal("set-key")
                        .then(CommandManager.argument("value", StringArgumentType.greedyString())
                            .executes(context -> updateKey(context.getSource(), StringArgumentType.getString(context, "value")))
                        )
                    )
                    
                    // Option 3: test
                    .then(CommandManager.literal("test")
                        .executes(context -> executeTest(context.getSource()))
                    )
                );
            }

            // Global direct alias: /testconnect
            dispatcher.register(CommandManager.literal("testconnect")
                .requires(source -> source.hasPermissionLevel(4))
                .executes(context -> executeTest(context.getSource()))
            );
        });
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
