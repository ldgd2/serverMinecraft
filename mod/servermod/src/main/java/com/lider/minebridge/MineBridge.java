package com.lider.minebridge;

import com.lider.minebridge.commands.ModCommands;
import com.lider.minebridge.config.ModConfig;
import com.lider.minebridge.events.ServerEvents;
import com.lider.minebridge.networking.BackendClient;
import com.lider.minebridge.marketplace.MarketplaceModule;
import com.lider.minebridge.achievements.AchievementModule;
import com.lider.minebridge.networking.payload.UpdateCountdownPayload;
import com.lider.minebridge.networking.payload.SyncSkinPayload;
import com.lider.minebridge.networking.payload.SyncBackendUrlPayload;
import com.lider.minebridge.networking.NetworkManager;
import net.fabricmc.api.ModInitializer;
import net.fabricmc.fabric.api.event.lifecycle.v1.ServerLifecycleEvents;
import net.fabricmc.fabric.api.networking.v1.PayloadTypeRegistry;
import net.minecraft.server.MinecraftServer;
import net.fabricmc.fabric.api.networking.v1.ServerPlayConnectionEvents;
import net.fabricmc.fabric.api.networking.v1.ServerPlayNetworking;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class MineBridge implements ModInitializer {
    public static final Logger LOGGER = LoggerFactory.getLogger("MineBridge");
    
    private static MinecraftServer serverInstance;
    private static BackendClient backendClient;

    @Override
    public void onInitialize() {
        ServerLifecycleEvents.SERVER_STARTING.register(srv -> {
            serverInstance = srv;
        });

        // --- Carga de Módulos (Modularización Premium) ---
        MarketplaceModule.initCommon();
        AchievementModule.initCommon();
        
        // Registros Globales Genéricos
        PayloadTypeRegistry.playS2C().register(UpdateCountdownPayload.ID, UpdateCountdownPayload.CODEC);
        PayloadTypeRegistry.playS2C().register(SyncSkinPayload.ID, SyncSkinPayload.CODEC);
        PayloadTypeRegistry.playS2C().register(SyncBackendUrlPayload.ID, SyncBackendUrlPayload.CODEC);
        PayloadTypeRegistry.playS2C().register(com.lider.minebridge.networking.payload.ShowAlertPayload.ID, com.lider.minebridge.networking.payload.ShowAlertPayload.CODEC);
        PayloadTypeRegistry.playS2C().register(com.lider.minebridge.networking.payload.ShowNotificationPayload.ID, com.lider.minebridge.networking.payload.ShowNotificationPayload.CODEC);
        
        // Security Handshake
        PayloadTypeRegistry.playS2C().register(com.lider.minebridge.networking.payload.ModHandshakePayload.ID, com.lider.minebridge.networking.payload.ModHandshakePayload.CODEC);
        PayloadTypeRegistry.playC2S().register(com.lider.minebridge.networking.payload.ModHandshakePayload.ID, com.lider.minebridge.networking.payload.ModHandshakePayload.CODEC);

        ServerPlayConnectionEvents.JOIN.register((handler, sender, srv) -> {
            String url = ModConfig.getBackendUrl();
            if (url != null && !url.contains("PENDING")) {
                ServerPlayNetworking.send(handler.player, new SyncBackendUrlPayload(url));
            }
        });

        ModConfig.load();
        detectPublicIp();

        backendClient = new BackendClient(ModConfig.getBackendUrl(), ModConfig.getLocalUrl(), ModConfig.getApiKey());

        ServerEvents.init();
        ModCommands.init();
        com.lider.minebridge.networking.HeartbeatTask.start();

        LOGGER.info("MineBridge Modular - Server Initialization Complete");
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
