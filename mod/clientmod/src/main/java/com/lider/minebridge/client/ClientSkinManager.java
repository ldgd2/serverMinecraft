package com.lider.minebridge.client;

import com.mojang.authlib.GameProfile;
import com.mojang.authlib.properties.Property;
import net.minecraft.client.MinecraftClient;
import net.minecraft.client.util.SkinTextures;

import java.util.HashMap;
import java.util.Map;
import java.util.UUID;

public class ClientSkinManager {
    private static final Map<UUID, SkinTextures> customSkins = new HashMap<>();

    public static void updateSkin(UUID uuid, String value, String signature) {
        GameProfile profile = new GameProfile(uuid, "Player");
        profile.getProperties().put("textures", new Property("textures", value, signature));

        MinecraftClient.getInstance().getSkinProvider().fetchSkinTextures(profile).thenAccept(textures -> {
            if (textures != null) {
                customSkins.put(uuid, (SkinTextures) textures); // Cast in case it's an Object or Optional in older mappings, but in 1.21.1 it's SkinTextures directly
            }
        });
    }

    public static SkinTextures getSkin(UUID uuid) {
        return customSkins.get(uuid);
    }
}
