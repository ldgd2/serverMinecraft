package com.lider.minebridge;

import com.lider.minebridge.commands.ModCommands;
import com.lider.minebridge.config.ModConfig;
import com.lider.minebridge.events.ServerEvents;
import com.lider.minebridge.networking.BackendClient;
import net.fabricmc.api.EnvType;
import net.fabricmc.api.ModInitializer;
import net.fabricmc.loader.api.FabricLoader;
import net.fabricmc.fabric.api.event.lifecycle.v1.ServerLifecycleEvents;
import net.minecraft.server.MinecraftServer;
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

    @Override
    public void onInitialize() {
        if (FabricLoader.getInstance().getEnvironmentType() != EnvType.SERVER) {
            return;
        }
        
        // CAPTURAR INSTANCIA REAL DEL SERVIDOR
        ServerLifecycleEvents.SERVER_STARTING.register(server -> {
            serverInstance = server;
            // LOGGER.info("Server Instance Captured Successfully");
        });

        // LOGGER.info("MineBridge Modular - Starting Initialization");
        
        ModConfig.load();
        detectPublicIp();

        backendClient = new BackendClient(ModConfig.getBackendUrl(), ModConfig.getApiKey());

        ServerEvents.init();
        ModCommands.init();

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
