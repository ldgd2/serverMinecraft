package com.lider.minebridge.networking;

import com.lider.minebridge.networking.payload.AchievementUnlockPayload;
import net.fabricmc.fabric.api.client.networking.v1.ClientPlayNetworking;

public class AchievementClient {
    public static void triggerAchievement(String achievementId) {
        if (ClientPlayNetworking.canSend(AchievementUnlockPayload.ID)) {
            ClientPlayNetworking.send(new AchievementUnlockPayload(achievementId));
        }
    }
}
