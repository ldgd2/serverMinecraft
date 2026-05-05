package com.lider.minebridge.config;

import com.google.gson.Gson;
import com.google.gson.GsonBuilder;
import com.google.gson.JsonObject;
import com.lider.minebridge.MineBridge;
import net.fabricmc.loader.api.FabricLoader;

import java.io.File;
import java.io.FileReader;
import java.io.FileWriter;
import java.nio.file.Path;

public class ModConfig {
    private static final Path CONFIG_PATH = FabricLoader.getInstance().getConfigDir().resolve("minebridge.json");
    private static final Gson GSON = new GsonBuilder().setPrettyPrinting().create();
    
    private static String backendUrl = "PENDING";
    private static String localUrl = "PENDING";
    private static String apiKey = "PENDING";
    private static String serverIp = "0.0.0.0";
    private static String serverName = "MinecraftTest";

    public static void setBackendUrl(String url) {
        backendUrl = url;
        save();
    }

    public static void load() {
        File file = CONFIG_PATH.toFile();
        if (!file.exists()) {
            save();
            return;
        }

        try (FileReader reader = new FileReader(file)) {
            JsonObject json = GSON.fromJson(reader, JsonObject.class);
            if (json.has("backend_url")) backendUrl = json.get("backend_url").getAsString();
            if (json.has("local_url")) localUrl = json.get("local_url").getAsString();
            if (json.has("api_key")) apiKey = json.get("api_key").getAsString();
            if (json.has("server_ip")) serverIp = json.get("server_ip").getAsString();
            if (json.has("server_name")) serverName = json.get("server_name").getAsString();
        } catch (Exception e) {
            MineBridge.LOGGER.error("Failed to load config: " + e.getMessage());
        }
    }

    public static void save() {
        try (FileWriter writer = new FileWriter(CONFIG_PATH.toFile())) {
            JsonObject json = new JsonObject();
            json.addProperty("backend_url", backendUrl);
            json.addProperty("local_url", localUrl);
            json.addProperty("api_key", apiKey);
            json.addProperty("server_ip", serverIp);
            json.addProperty("server_name", serverName);
            GSON.toJson(json, writer);
        } catch (Exception e) {
            MineBridge.LOGGER.error("Failed to save config: " + e.getMessage());
        }
    }

    public static String getBackendUrl() { 
        // Si hay una URL local configurada y no es PENDING, podrías priorizarla o usarla como fallback
        // El usuario dice: si no recibe configuración local, usa la pública.
        return backendUrl; 
    }
    public static String getLocalUrl() { return localUrl; }
    public static String getApiKey() { return apiKey; }
    public static String getServerIp() { return serverIp; }
    public static String getServerName() { return serverName; }

    public static void setApiKey(String key) {
        apiKey = key;
        save();
    }

    public static void setServerIp(String ip) {
        serverIp = ip;
        save();
    }

    public static void setServerName(String name) {
        serverName = name;
        save();
    }
}
