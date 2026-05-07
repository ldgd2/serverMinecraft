package com.lider.minebridge;

import com.lider.minebridge.commands.ModCommands;
import com.lider.minebridge.config.ModConfig;
import com.lider.minebridge.events.ServerEvents;
import com.lider.minebridge.networking.BackendClient;
import net.fabricmc.api.EnvType;
import net.fabricmc.api.ModInitializer;
import net.fabricmc.loader.api.FabricLoader;
import net.fabricmc.fabric.api.event.lifecycle.v1.ServerLifecycleEvents;
import com.lider.minebridge.networking.payload.AchievementUnlockPayload;
import net.fabricmc.fabric.api.networking.v1.PayloadTypeRegistry;
import net.minecraft.server.MinecraftServer;
import net.minecraft.util.Identifier;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import java.io.BufferedReader;
import java.io.InputStreamReader;
import java.net.URL;

public class MineBridge implements ModInitializer {
    public static final String MOD_ID = "minebridge";
    public static final Logger LOGGER = LoggerFactory.getLogger(MOD_ID);
    
    private static MinecraftServer serverInstance;
    private static BackendClient backendClient;

    public static final net.minecraft.screen.ScreenHandlerType<com.lider.minebridge.marketplace.MarketplaceCreationScreenHandler> MARKETPLACE_CREATION_HANDLER = 
        net.minecraft.registry.Registry.register(net.minecraft.registry.Registries.SCREEN_HANDLER, Identifier.of(MOD_ID, "creation"), 
        new net.minecraft.screen.ScreenHandlerType<>(com.lider.minebridge.marketplace.MarketplaceCreationScreenHandler::new, net.minecraft.resource.featuretoggle.FeatureSet.empty()));

    public static final net.minecraft.screen.ScreenHandlerType<com.lider.minebridge.marketplace.MarketplaceTransactionScreenHandler> MARKETPLACE_TRANSACTION_HANDLER = 
        net.minecraft.registry.Registry.register(net.minecraft.registry.Registries.SCREEN_HANDLER, Identifier.of(MOD_ID, "transaction"), 
        new net.fabricmc.fabric.api.screenhandler.v1.ExtendedScreenHandlerType<>(
            (syncId, inv, data) -> new com.lider.minebridge.marketplace.MarketplaceTransactionScreenHandler(syncId, inv, data.tradeId(), data.req1(), data.req2()),
            com.lider.minebridge.networking.payload.TransactionScreenDataPayload.CODEC
        ));

    @Override
    public void onInitialize() {
        // Register custom payloads
        PayloadTypeRegistry.playC2S().register(AchievementUnlockPayload.ID, AchievementUnlockPayload.CODEC);
        PayloadTypeRegistry.playS2C().register(com.lider.minebridge.networking.payload.UpdateCountdownPayload.ID, com.lider.minebridge.networking.payload.UpdateCountdownPayload.CODEC);
        PayloadTypeRegistry.playS2C().register(com.lider.minebridge.networking.payload.SyncSkinPayload.ID, com.lider.minebridge.networking.payload.SyncSkinPayload.CODEC);
        PayloadTypeRegistry.playC2S().register(com.lider.minebridge.networking.payload.MarketplaceRequestPayload.ID, com.lider.minebridge.networking.payload.MarketplaceRequestPayload.CODEC);
        PayloadTypeRegistry.playC2S().register(com.lider.minebridge.networking.payload.OpenCreationMenuPayload.ID, com.lider.minebridge.networking.payload.OpenCreationMenuPayload.CODEC);
        PayloadTypeRegistry.playC2S().register(com.lider.minebridge.networking.payload.OpenTransactionMenuPayload.ID, com.lider.minebridge.networking.payload.OpenTransactionMenuPayload.CODEC);
        PayloadTypeRegistry.playC2S().register(com.lider.minebridge.networking.payload.CompleteTradePayload.ID, com.lider.minebridge.networking.payload.CompleteTradePayload.CODEC);
        
        ServerLifecycleEvents.SERVER_STARTING.register(server -> {
            serverInstance = server;
        });

        ModConfig.load();
        detectPublicIp();

        backendClient = new BackendClient(ModConfig.getBackendUrl(), ModConfig.getLocalUrl(), ModConfig.getApiKey());

        ServerEvents.init();
        ModCommands.init();

        net.fabricmc.fabric.api.networking.v1.ServerPlayNetworking.registerGlobalReceiver(com.lider.minebridge.networking.payload.MarketplaceRequestPayload.ID, (payload, context) -> {
            context.server().execute(() -> {
                com.google.gson.JsonArray trades = com.google.gson.JsonParser.parseString(payload.tradeData()).getAsJsonArray();
                com.lider.minebridge.marketplace.MarketplaceManager.openMarketplace(context.player(), trades);
            });
        });

        net.fabricmc.fabric.api.networking.v1.ServerPlayNetworking.registerGlobalReceiver(com.lider.minebridge.networking.payload.OpenCreationMenuPayload.ID, (payload, context) -> {
            context.server().execute(() -> {
                com.lider.minebridge.marketplace.MarketplaceManager.openCreationMenu(context.player());
            });
        });

        net.fabricmc.fabric.api.networking.v1.ServerPlayNetworking.registerGlobalReceiver(com.lider.minebridge.networking.payload.OpenTransactionMenuPayload.ID, (payload, context) -> {
            context.server().execute(() -> {
                com.lider.minebridge.marketplace.MarketplaceManager.openTransactionMenu(context.player(), payload.tradeId());
            });
        });

        net.fabricmc.fabric.api.networking.v1.ServerPlayNetworking.registerGlobalReceiver(com.lider.minebridge.networking.payload.CompleteTradePayload.ID, (payload, context) -> {
            context.server().execute(() -> {
                com.lider.minebridge.marketplace.MarketplaceManager.completeTradeOnServer(context.player(), payload.tradeId());
            });
        });

        // Register payload receiver
        net.fabricmc.fabric.api.networking.v1.ServerPlayNetworking.registerGlobalReceiver(AchievementUnlockPayload.ID, (payload, context) -> {
            context.server().execute(() -> {
                String key = payload.achievementKey();
                String playerName = context.player().getName().getString();
                
                // Anunciar al chat global (El servidor solo anuncia)
                context.server().getPlayerManager().broadcast(
                    net.minecraft.text.Text.of("§6[Logro] §f" + playerName + " ha desbloqueado: §e" + key.replace("_", " ").toUpperCase()),
                    false
                );

                if (backendClient != null) {
                    com.lider.minebridge.networking.AchievementClient.sendEvent(
                        context.player().getUuidAsString(),
                        key,
                        1
                    );
                }
            });
        });

        // Registro de comandos
        net.fabricmc.fabric.api.command.v2.CommandRegistrationCallback.EVENT.register((dispatcher, registryAccess, environment) -> {
            dispatcher.register(net.minecraft.server.command.CommandManager.literal("minebridge")
                .requires(source -> source.hasPermissionLevel(2))
                .then(net.minecraft.server.command.CommandManager.literal("status")
                    .executes(context -> {
                        String status = (backendClient != null && backendClient.isWebSocketConnected()) ? "§aCONECTADO" : "§cDESCONECTADO";
                        String url = (backendClient != null) ? backendClient.getActiveUrl() : "N/A";
                        context.getSource().sendFeedback(() -> net.minecraft.text.Text.of("§6[MineBridge] §fEstado: " + status), false);
                        context.getSource().sendFeedback(() -> net.minecraft.text.Text.of("§6[MineBridge] §fBackend: §e" + url), false);
                        return 1;
                    })
                )
            );
        });

        LOGGER.info("MineBridge Modular - Initialization Complete");
    }

    private void detectPublicIp() {
        com.lider.minebridge.networking.NetworkManager.getExecutor().execute(() -> {
            try {
                java.net.URL url = new java.net.URL("https://checkip.amazonaws.com");
                try (java.io.BufferedReader br = new java.io.BufferedReader(new java.io.InputStreamReader(url.openStream()))) {
                    String ip = br.readLine().trim();
                    com.lider.minebridge.config.ModConfig.setServerIp(ip);
                }
            } catch (Exception e) {
                LOGGER.error("Identity detection failed: " + e.getMessage());
            }
        });
    }

    public static BackendClient getBackendClient() {
        return backendClient;
    }

    public static MinecraftServer getServer() {
        return serverInstance;
    }
}
