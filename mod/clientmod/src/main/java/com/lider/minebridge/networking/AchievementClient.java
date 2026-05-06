package com.lider.minebridge.networking;

import com.lider.minebridge.client.AchievementToast;
import com.lider.minebridge.networking.payload.AchievementUnlockPayload;
import net.fabricmc.fabric.api.client.networking.v1.ClientPlayNetworking;
import net.minecraft.client.MinecraftClient;
import net.minecraft.text.Text;

import java.util.HashSet;
import java.util.Set;

public class AchievementClient {
    private static final Set<String> UNLOCKED_SESSION = new HashSet<>();

    public static final int COLOR_COMMON = 0xAAAAAA;
    public static final int COLOR_UNCOMMON = 0x55FF55;
    public static final int COLOR_RARE = 0x5555FF;
    public static final int COLOR_EPIC = 0xAA00AA;
    public static final int COLOR_LEGENDARY = 0xFFAA00;
    public static final int COLOR_MYTHIC = 0xAA0000;

    public static void triggerAchievement(String achievementId) {
        if (ClientPlayNetworking.canSend(AchievementUnlockPayload.ID)) {
            ClientPlayNetworking.send(new AchievementUnlockPayload(achievementId));
        }
    }

    public static void triggerAchievement(String key, String title, String description) {
        if (UNLOCKED_SESSION.contains(key)) return;
        UNLOCKED_SESSION.add(key);

        // 1. Enviar al servidor
        triggerAchievement(key);

        // 2. Mostrar Toast local
        MinecraftClient client = MinecraftClient.getInstance();
        if (client != null && client.getToastManager() != null) {
            int color = getColorForKey(key);
            client.getToastManager().add(new AchievementToast(Text.of(title), Text.of(description), color));
        }
    }

    private static int getColorForKey(String key) {
        return switch (key) {
            case "EDGE_REASON" -> COLOR_MYTHIC;
            case "DESCEND_MADNESS", "TIME_LEGEND", "TIME_ANCIENT", "DOMINATOR" -> COLOR_LEGENDARY;
            case "HARVEST_SOULS", "FATHOMLESS_ABYSS" -> COLOR_EPIC;
            case "BLOOD_SWEAT", "IMMINENT_MASSACRE" -> COLOR_RARE;
            case "MEME_VOID_STARK", "MEME_NO_AFECTO", "EVEREST", "MEME_HUMILDAD" -> COLOR_UNCOMMON;
            default -> COLOR_COMMON;
        };
    }
}
