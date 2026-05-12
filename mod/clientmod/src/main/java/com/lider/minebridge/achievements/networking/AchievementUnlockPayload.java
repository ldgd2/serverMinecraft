package com.lider.minebridge.achievements.networking;

import net.minecraft.network.RegistryByteBuf;
import net.minecraft.network.codec.PacketCodec;
import net.minecraft.network.codec.PacketCodecs;
import net.minecraft.network.packet.CustomPayload;
import net.minecraft.util.Identifier;

/**
 * Payload de Logros: Sincroniza desbloqueos entre servidor y cliente.
 */
public record AchievementUnlockPayload(String achievementId, String title) implements CustomPayload {
    public static final CustomPayload.Id<AchievementUnlockPayload> ID = new CustomPayload.Id<>(Identifier.of("minebridge", "achievement_unlock"));
    
    public static final PacketCodec<RegistryByteBuf, AchievementUnlockPayload> CODEC = PacketCodec.tuple(
            PacketCodecs.string(1024 * 1024), AchievementUnlockPayload::achievementId,
            PacketCodecs.string(1024 * 1024), AchievementUnlockPayload::title,
            AchievementUnlockPayload::new
    );

    @Override
    public CustomPayload.Id<? extends CustomPayload> getId() {
        return ID;
    }
}
