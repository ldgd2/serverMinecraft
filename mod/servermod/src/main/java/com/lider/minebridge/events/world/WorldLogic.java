package com.lider.minebridge.events.world;

import com.lider.minebridge.networking.AchievementClient;
import net.minecraft.entity.passive.TameableEntity;

public class WorldLogic {

    public static void init() {
        // La domesticación se maneja preferiblemente vía Mixins para mayor precisión
    }

    public static void onFishCaught(String playerUuid, String fishId) {
        AchievementClient.sendEvent(playerUuid, "fish_caught:" + fishId, 1);
        AchievementClient.sendEvent(playerUuid, "total_fish_caught", 1);
    }

    public static void onCropHarvested(String playerUuid, String cropId) {
        AchievementClient.sendEvent(playerUuid, "crop_harvested:" + cropId, 1);
    }
}
