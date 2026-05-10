package com.lider.minebridge.commands.modules;

import com.mojang.brigadier.CommandDispatcher;
import com.mojang.brigadier.arguments.IntegerArgumentType;
import com.mojang.brigadier.arguments.StringArgumentType;
import com.lider.minebridge.MineBridge;
import com.lider.minebridge.config.ModConfig;
import com.lider.minebridge.networking.payload.UpdateCountdownPayload;
import net.fabricmc.fabric.api.networking.v1.ServerPlayNetworking;
import net.minecraft.server.command.CommandManager;
import net.minecraft.server.command.ServerCommandSource;
import net.minecraft.text.Text;

public class AdminCommand {

    public static void register(CommandDispatcher<ServerCommandSource> dispatcher) {
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

                // Option: status
                .then(CommandManager.literal("status")
                    .executes(context -> {
                        String status = (MineBridge.getBackendClient() != null && MineBridge.getBackendClient().isWebSocketConnected()) ? "§aCONECTADO" : "§cDESCONECTADO";
                        String url = (MineBridge.getBackendClient() != null) ? MineBridge.getBackendClient().getActiveUrl() : "N/A";
                        context.getSource().sendFeedback(() -> Text.of("§6[MineBridge] §fEstado: " + status), false);
                        context.getSource().sendFeedback(() -> Text.of("§6[MineBridge] §fBackend: §e" + url), false);
                        return 1;
                    })
                )

                // Option: test
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

        // Backend direct update trigger: /minebridge_update <seconds>
        dispatcher.register(CommandManager.literal("minebridge_update")
            .requires(source -> source.hasPermissionLevel(4))
            .then(CommandManager.argument("seconds", IntegerArgumentType.integer(0))
                .executes(context -> triggerUpdate(context.getSource(), IntegerArgumentType.getInteger(context, "seconds")))
            )
        );
    }

    private static int updateUrl(ServerCommandSource source, String newUrl) {
        ModConfig.setBackendUrl(newUrl);
        if (MineBridge.getBackendClient() != null) {
            MineBridge.getBackendClient().updateBaseUrl(newUrl);
        }
        source.sendFeedback(() -> Text.literal("§a[MineBridge] URL del Backend actualizada a: §f" + newUrl), true);
        return 1;
    }

    private static int updateKey(ServerCommandSource source, String newKey) {
        ModConfig.setApiKey(newKey);
        if (MineBridge.getBackendClient() != null) {
            MineBridge.getBackendClient().updateApiKey(newKey);
        }
        source.sendFeedback(() -> Text.literal("§a[MineBridge] API Key actualizada correctamente."), true);
        return 1;
    }

    private static int triggerUpdate(ServerCommandSource source, int seconds) {
        // Enviar paquete a todos los clientes (para el timer visual)
        source.getServer().getPlayerManager().getPlayerList().forEach(player -> {
            ServerPlayNetworking.send(player, new UpdateCountdownPayload(seconds));
        });
        
        // También enviar mensaje por chat para redundancia
        source.getServer().getPlayerManager().broadcast(
            Text.of("§7[§9INFO§7] §bMantenimiento programado: Reinicio en " + (seconds / 60) + " minutos."),
            false
        );
        
        source.sendFeedback(() -> Text.literal("§a[MineBridge] Update countdown sent to all clients (" + seconds + "s)"), true);
        return 1;
    }

    private static int executeTest(ServerCommandSource source) {
        source.sendFeedback(() -> Text.literal("§e[MineBridge] Probando conexión con el Backend..."), false);
        
        if (MineBridge.getBackendClient() == null) {
            source.sendError(Text.literal("§c[MineBridge] ERROR: El cliente de red no está inicializado."));
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
