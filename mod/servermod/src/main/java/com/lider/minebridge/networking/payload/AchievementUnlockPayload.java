package com.lider.minebridge.networking.payload;

import net.minecraft.network.RegistryByteBuf;
import net.minecraft.network.codec.PacketCodec;
import net.minecraft.network.codec.PacketCodecs;
import net.minecraft.network.packet.CustomPayload;
import net.minecraft.util.Identifier;

public record AchievementUnlockPayload(String achievementKey) implements CustomPayload {
    public static final CustomPayload.Id<AchievementUnlockPayload> ID = new CustomPayload.Id<>(Identifier.of("minebridge", "achievement_unlock"));

    public static final PacketCodec<RegistryByteBuf, AchievementUnlockPayload> CODEC = PacketCodec.tuple(
            PacketCodecs.STRING, AchievementUnlockPayload::achievementKey,
            AchievementUnlockPayload::new
    );

    @Override
    public CustomPayload.Id<? extends CustomPayload> getId() {
        return ID;
    }
}
