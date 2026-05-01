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
            dispatcher.register(CommandManager.literal("bridge")
                .requires(source -> source.hasPermissionLevel(4))
                // /bridge url <url>
                .then(CommandManager.literal("url")
                    .then(CommandManager.argument("value", StringArgumentType.string())
                        .executes(context -> {
                            String newUrl = StringArgumentType.getString(context, "value");
                            ModConfig.setBackendUrl(newUrl);
                            if (MineBridge.getBackendClient() != null) {
                                MineBridge.getBackendClient().updateBaseUrl(newUrl);
                            }
                            context.getSource().sendFeedback(() -> Text.literal("§a[MineBridge] URL del Backend actualizada."), true);
                            return 1;
                        })
                    )
                )
                // /bridge key <key>
                .then(CommandManager.literal("key")
                    .then(CommandManager.argument("value", StringArgumentType.string())
                        .executes(context -> {
                            String newKey = StringArgumentType.getString(context, "value");
                            ModConfig.setApiKey(newKey);
                            if (MineBridge.getBackendClient() != null) {
                                MineBridge.getBackendClient().updateApiKey(newKey);
                            }
                            context.getSource().sendFeedback(() -> Text.literal("§a[MineBridge] API Key actualizada."), true);
                            return 1;
                        })
                    )
                )
                // /bridge test (alias de /testconnect)
                .then(CommandManager.literal("test")
                    .executes(context -> executeTest(context.getSource()))
                )
            );

            // Alias directo: /testconnect
            dispatcher.register(CommandManager.literal("testconnect")
                .requires(source -> source.hasPermissionLevel(4))
                .executes(context -> executeTest(context.getSource()))
            );
        });
    }

    private static int executeTest(net.minecraft.server.command.ServerCommandSource source) {
        source.sendFeedback(() -> Text.literal("§e[MineBridge] Probando conexión..."), false);
        
        if (MineBridge.getBackendClient() == null) {
            source.sendError(Text.literal("§c[MineBridge] El cliente de red no está inicializado."));
            return 0;
        }

        MineBridge.getBackendClient().testConnection().thenAccept(result -> {
            switch (result) {
                case "SUCCESS":
                    source.sendFeedback(() -> Text.literal("§a[MineBridge] ¡Conexión Exitosa! El backend respondió correctamente."), true);
                    break;
                case "CONFIG_ERROR":
                    source.sendError(Text.literal("§c[MineBridge] Error: Configuración incompleta. Usa /bridge url y /bridge key."));
                    break;
                case "UNAUTHORIZED":
                    source.sendError(Text.literal("§c[MineBridge] Error 401: API Key inválida o rechazada por el backend."));
                    break;
                default:
                    source.sendError(Text.literal("§c[MineBridge] Fallo en la conexión: " + result));
                    break;
            }
        });
        return 1;
    }
}
