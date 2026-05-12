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

    /**
     * Disparador manual para momentos CRÍTICOS (Join/Leave).
     * Evita pedir datos como desquiciado; solo cuando realmente cambia algo.
     */
    public static void trigger() {
        run();
    }

    private static void run() {
        MinecraftServer server = MineBridge.getServer();
        if (server == null) return;

        // CAPTURA: Copiamos lo que necesitamos del hilo principal muy rápido
        MineCore.Data.snapshot(() -> {
            JsonObject data = new JsonObject();
            data.addProperty("online_count", server.getCurrentPlayerCount());
            data.addProperty("max_players", server.getMaxPlayerCount());
            data.addProperty("server_name", com.lider.minebridge.config.ModConfig.getServerName());
            
            java.util.List<ServerPlayerEntity> playersList = new java.util.ArrayList<>(server.getPlayerManager().getPlayerList());
            return new SnapshotData(data, playersList);
        }, snapshot -> {
            // PROCESAMIENTO: Armamos el JSON pesado en un núcleo aislado
            JsonObject payload = snapshot.baseData;
            JsonArray players = new JsonArray();
            
            for (ServerPlayerEntity player : snapshot.players) {
                JsonObject p = new JsonObject();
                p.addProperty("name", player.getName().getString());
                p.addProperty("uuid", player.getUuidAsString());
                p.addProperty("ip", player.getIp());
                players.add(p);
            }
            payload.add("players", players);

            // ENVÍO: Fuera del hilo principal
            AchievementClient.sendRequest("api/v1/bridge/heartbeat", payload);
        });
    }

    private record SnapshotData(JsonObject baseData, java.util.List<ServerPlayerEntity> players) {}
}
