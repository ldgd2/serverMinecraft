package com.lider.minebridge.networking;

import com.google.gson.JsonArray;
import com.google.gson.JsonObject;
import com.lider.minebridge.MineBridge;
import com.lider.minebridge.config.ModConfig;
import net.minecraft.server.MinecraftServer;
import com.lider.minebridge.core.MineCore;
import net.minecraft.server.network.ServerPlayerEntity;

import java.util.concurrent.TimeUnit;

/**
 * HeartbeatTask — Reporta el estado del servidor y la lista de jugadores online.
 * Asegura que el backend tenga información sincronizada incluso tras reinicios.
 */
public class HeartbeatTask {

    public static void start() {
        // Ya no enviamos datos por reloj (polling). 
        // Solo enviamos cuando realmente pasa algo (Event-Driven).
        trigger();
    }

    private static long lastTrigger = 0;
    private static final long COOLDOWN_MS = 2000;

    /**
     * Disparador manual para momentos CRÍTICOS (Join/Leave).
     * Evita pedir datos como desquiciado; solo cuando realmente cambia algo.
     */
    public static void trigger() {
        long now = System.currentTimeMillis();
        if (now - lastTrigger < COOLDOWN_MS) return;
        lastTrigger = now;
        run();
    }

    private static void run() {
        MinecraftServer server = MineBridge.getServer();
        if (server == null) return;

        // CAPTURA MÍNIMA: Solo lo que vive en el servidor
        MineCore.Data.snapshot(() -> {
            int online = server.getCurrentPlayerCount();
            int max = server.getMaxPlayerCount();
            String name = com.lider.minebridge.config.ModConfig.getServerName();
            
            // Capturamos solo los datos necesarios como strings para no tocar objetos del juego en el hilo async
            java.util.List<PlayerData> players = server.getPlayerManager().getPlayerList().stream()
                .map(p -> new PlayerData(p.getName().getString(), p.getUuidAsString(), p.getIp()))
                .toList();
                
            return new RawData(online, max, name, players);
        }, raw -> {
            // PROCESAMIENTO PESADO: Construcción de JSON fuera del hilo principal
            JsonObject payload = new JsonObject();
            payload.addProperty("online_count", raw.online);
            payload.addProperty("max_players", raw.max);
            
            JsonArray playersArray = new JsonArray();
            for (PlayerData pData : raw.players) {
                JsonObject p = new JsonObject();
                p.addProperty("player", pData.name);
                p.addProperty("name", pData.name);
                p.addProperty("player_uuid", pData.uuid);
                p.addProperty("uuid", pData.uuid);
                p.addProperty("ip", pData.ip);
                p.addProperty("player_ip", pData.ip);
                playersArray.add(p);
            }
            
            payload.add("players", playersArray);
            payload.addProperty("server_name", raw.name);
            payload.addProperty("server", raw.name);
            payload.addProperty("status", "RUNNING");

            // Enviar heartbeat a la ruta estandarizada
            AchievementClient.sendRequest("api/v1/bridge/heartbeat", payload);
        });
    }

    private record PlayerData(String name, String uuid, String ip) {}
    private record RawData(int online, int max, String name, java.util.List<PlayerData> players) {}
}
