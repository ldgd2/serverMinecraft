package com.lider.minebridge.achievements;

import com.google.gson.Gson;
import com.google.gson.GsonBuilder;
import com.google.gson.reflect.TypeToken;
import net.fabricmc.loader.api.FabricLoader;
import java.io.File;
import java.io.FileReader;
import java.io.FileWriter;
import java.nio.file.Path;
import java.util.HashSet;
import java.util.Set;

public class AchievementStorage {
    private static final Path PATH = FabricLoader.getInstance().getConfigDir().resolve("minebridge_unlocked.json");
    private static final Gson GSON = new GsonBuilder().setPrettyPrinting().create();
    private static final Set<String> unlockedIds = HashSet.newKeySet();

    public static void load() {
        File file = PATH.toFile();
        if (!file.exists()) return;

        try (FileReader reader = new FileReader(file)) {
            java.lang.reflect.Type type = new TypeToken<HashSet<String>>(){}.getType();
            HashSet<String> loaded = GSON.fromJson(reader, type);
            if (loaded != null) {
                unlockedIds.addAll(loaded);
            }
        } catch (Exception e) {}
    }

    public static void save() {
        com.lider.minebridge.core.MineCore.async(() -> {
            try (FileWriter writer = new FileWriter(PATH.toFile())) {
                GSON.toJson(unlockedIds, writer);
            } catch (Exception e) {}
        });
    }

    public static boolean isUnlocked(String achievementId) {
        return unlockedIds.contains(achievementId);
    }

    public static void unlock(String achievementId) {
        if (unlockedIds.add(achievementId)) {
            save();
        }
    }
}
