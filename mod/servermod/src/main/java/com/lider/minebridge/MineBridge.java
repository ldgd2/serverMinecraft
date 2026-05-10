package com.lider.minebridge;

import com.lider.minebridge.commands.ModCommands;
import com.lider.minebridge.config.ModConfig;
import com.lider.minebridge.events.ServerEvents;
import com.lider.minebridge.networking.BackendClient;
import com.lider.minebridge.marketplace.MarketplaceModule;
import com.lider.minebridge.achievements.AchievementModule;
import com.lider.minebridge.networking.payload.UpdateCountdownPayload;
import com.lider.minebridge.networking.payload.SyncSkinPayload;
import net.fabricmc.api.ModInitializer;
import net.fabricmc.fabric.api.event.lifecycle.v1.ServerLifecycleEvents;
import net.fabricmc.fabric.api.networking.v1.PayloadTypeRegistry;
import net.minecraft.server.MinecraftServer;
import com.lider.minebridge.networking.payload.SyncBackendUrlPayload;
import net.fabricmc.fabric.api.networking.v1.ServerPlayConnectionEvents;
import net.fabricmc.fabric.api.networking.v1.ServerPlayNetworking;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class MineBridge implements ModInitializer {
    public static final String MOD_ID = "minebridge";
    public static final Logger LOGGER = LoggerFactory.getLogger(MOD_ID);
    
    private static MinecraftServer serverInstance;
    private static BackendClient backendClient;

    @Override
    public void onInitialize() {
        // --- Carga de Módulos (Modularización Premium) ---
        MarketplaceModule.initCommon();
        AchievementModule.initCommon();
        
        // Registros Globales Genéricos
        PayloadTypeRegistry.playS2C().register(UpdateCountdownPayload.ID, UpdateCountdownPayload.CODEC);
        PayloadTypeRegistry.playS2C().register(SyncSkinPayload.ID, SyncSkinPayload.CODEC);
        PayloadTypeRegistry.playS2C().register(SyncBackendUrlPayload.ID, SyncBackendUrlPayload.CODEC);

        ServerPlayConnectionEvents.JOIN.register((handler, sender, server) -> {
            // Enviamos siempre la URL PÚBLICA a los jugadores.
            // El localUrl es solo para que el mod del servidor hable con su backend local.
            String url = ModConfig.getBackendUrl();
            if (url != null && !url.contains("PENDING")) {
                ServerPlayNetworking.send(handler.player, new SyncBackendUrlPayload(url));
            }
        });

        ServerLifecycleEvents.SERVER_STARTING.register(server -> {
            serverInstance = server;
        });

        ModConfig.load();
        detectPublicIp();

        backendClient = new BackendClient(ModConfig.getBackendUrl(), ModConfig.getLocalUrl(), ModConfig.getApiKey());

        ServerEvents.init();
        ModCommands.init();

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
