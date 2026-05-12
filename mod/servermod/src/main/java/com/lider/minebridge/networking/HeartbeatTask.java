package com.lider.minebridge.networking;

import com.google.gson.JsonArray;
import com.google.gson.JsonObject;
import com.lider.minebridge.MineBridge;
import com.lider.minebridge.config.ModConfig;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.network.ServerPlayerEntity;

import java.util.concurrent.TimeUnit;

/**
 * HeartbeatTask — Reporta el estado del servidor y la lista de jugadores online.
 * Asegura que el backend tenga información sincronizada incluso tras reinicios.
 */
public class HeartbeatTask {

    public static void start() {
        NetworkManager.getScheduler().scheduleAtFixedRate(HeartbeatTask::run, 15, 60, TimeUnit.SECONDS);
    }

    private static void run() {
        MinecraftServer server = MineBridge.getServer();
        if (server == null) return;

        server.execute(() -> {
            JsonObject payload = new JsonObject();
            payload.addProperty("server_name", ModConfig.getServerName());
            payload.addProperty("online_count", server.getCurrentPlayerCount());
            payload.addProperty("max_players", server.getMaxPlayerCount());
            
            JsonArray players = new JsonArray();
            for (ServerPlayerEntity player : server.getPlayerManager().getPlayerList()) {
                JsonObject p = new JsonObject();
                p.addProperty("name", player.getName().getString());
                p.addProperty("uuid", player.getUuidAsString());
                p.addProperty("ip", player.getIp());
                players.add(p);
            }
            payload.add("players", players);

            // El envío es asíncrono dentro de AchievementClient.sendRequest
            AchievementClient.sendRequest("api/v1/bridge/heartbeat", payload);
        });
    }
}
