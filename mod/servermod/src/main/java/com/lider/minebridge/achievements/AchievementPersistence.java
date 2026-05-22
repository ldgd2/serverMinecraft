package com.lider.minebridge.achievements;

import com.google.gson.Gson;
import com.google.gson.GsonBuilder;
import com.google.gson.JsonObject;
import com.google.gson.reflect.TypeToken;
import net.fabricmc.loader.api.FabricLoader;
import java.io.File;
import java.io.FileReader;
import java.io.FileWriter;
import java.nio.file.Path;
import java.util.HashSet;
import java.util.Set;
import java.util.concurrent.ConcurrentHashMap;

public class AchievementPersistence {
    private static final Path PATH = FabricLoader.getInstance().getConfigDir().resolve("minebridge_achievements.json");
    private static final Gson GSON = new GsonBuilder().setPrettyPrinting().create();
    private static final ConcurrentHashMap<String, Set<String>> playerAchievements = new ConcurrentHashMap<>();

    public static void load() {
        File file = PATH.toFile();
        if (!file.exists()) return;

        try (FileReader reader = new FileReader(file)) {
            java.lang.reflect.Type type = new TypeToken<ConcurrentHashMap<String, Set<String>>>(){}.getType();
            ConcurrentHashMap<String, Set<String>> loaded = GSON.fromJson(reader, type);
            if (loaded != null) {
                playerAchievements.putAll(loaded);
            }
        } catch (Exception e) {
            e.printStackTrace();
        }
    }

    public static synchronized void save() {
        com.lider.minebridge.networking.NetworkManager.getExecutor().execute(() -> {
            synchronized (AchievementPersistence.class) {
                try (FileWriter writer = new FileWriter(PATH.toFile())) {
                    GSON.toJson(playerAchievements, writer);
                } catch (Exception e) {
                    e.printStackTrace();
                }
            }
        });
    }

    public static boolean hasUnlocked(String uuid, String achievementId) {
        return playerAchievements.getOrDefault(uuid, new HashSet<>()).contains(achievementId);
    }

    public static void unlock(String uuid, String achievementId) {
        playerAchievements.computeIfAbsent(uuid, k -> HashSet.newKeySet()).add(achievementId);
        save();
    }
}
