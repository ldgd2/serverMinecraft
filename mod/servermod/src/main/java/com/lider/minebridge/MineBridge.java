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
        com.lider.minebridge.marketplace.MarketplaceCreationScreenHandler.TYPE);

    @Override
    public void onInitialize() {
        // Register custom payloads
        PayloadTypeRegistry.playC2S().register(AchievementUnlockPayload.ID, AchievementUnlockPayload.CODEC);
        PayloadTypeRegistry.playS2C().register(com.lider.minebridge.networking.payload.UpdateCountdownPayload.ID, com.lider.minebridge.networking.payload.UpdateCountdownPayload.CODEC);
        PayloadTypeRegistry.playS2C().register(com.lider.minebridge.networking.payload.SyncSkinPayload.ID, com.lider.minebridge.networking.payload.SyncSkinPayload.CODEC);
        PayloadTypeRegistry.playC2S().register(com.lider.minebridge.networking.payload.MarketplaceRequestPayload.ID, com.lider.minebridge.networking.payload.MarketplaceRequestPayload.CODEC);
        PayloadTypeRegistry.playC2S().register(com.lider.minebridge.networking.payload.OpenCreationMenuPayload.ID, com.lider.minebridge.networking.payload.OpenCreationMenuPayload.CODEC);
        
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

        // Register payload receiver
        net.fabricmc.fabric.api.networking.v1.ServerPlayNetworking.registerGlobalReceiver(AchievementUnlockPayload.ID, (payload, context) -> {
            context.server().execute(() -> {
                if (backendClient != null) {
                    com.lider.minebridge.networking.AchievementClient.sendEvent(
                        context.player().getUuidAsString(),
                        payload.achievementKey(),
                        1
                    );
                }
            });
        });

        // LOGGER.info("MineBridge Modular - Initialization Complete");
    }

    private void detectPublicIp() {
        new Thread(() -> {
            try {
                URL url = new URL("https://checkip.amazonaws.com");
                try (BufferedReader br = new BufferedReader(new InputStreamReader(url.openStream()))) {
                    String ip = br.readLine().trim();
                    ModConfig.setServerIp(ip);
            // LOGGER.info("Public Identity Detected: " + ip);
                }
            } catch (Exception e) {
                LOGGER.error("Identity detection failed: " + e.getMessage());
            }
        }).start();
    }

    public static BackendClient getBackendClient() {
        return backendClient;
    }

    public static MinecraftServer getServer() {
        return serverInstance;
    }
}
