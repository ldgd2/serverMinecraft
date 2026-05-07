package com.lider.minebridge.config;

import com.google.gson.JsonObject;
import com.google.gson.JsonParser;
import net.fabricmc.loader.api.FabricLoader;
import java.io.File;
import java.nio.file.Files;

public class ClientConfig {
    // El Empaquetador (build_all.py) reemplazará este valor durante la compilación
    private static String backendUrl = "http://185.214.134.23:8000";

    public static void load() {
        // La IP ya viene inyectada por el empaquetador, 
        // pero mantenemos el método por compatibilidad.
        if (backendUrl.equals("PENDING")) {
            backendUrl = "http://127.0.0.1:8000/";
        }
    }

    public static String getApiUrl() {
        return backendUrl.endsWith("/") ? backendUrl : backendUrl + "/";
    }
}
