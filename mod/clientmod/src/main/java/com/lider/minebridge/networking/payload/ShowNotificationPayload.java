package com.lider.minebridge.networking.payload;

import net.minecraft.network.RegistryByteBuf;
import net.minecraft.network.codec.PacketCodec;
import net.minecraft.network.codec.PacketCodecs;
import net.minecraft.network.packet.CustomPayload;
import net.minecraft.util.Identifier;

public record ShowNotificationPayload(String message, String type, int durationSeconds) implements CustomPayload {
    public static final CustomPayload.Id<ShowNotificationPayload> ID = new CustomPayload.Id<>(Identifier.of("minebridge", "show_notification"));

    public static final PacketCodec<RegistryByteBuf, ShowNotificationPayload> CODEC = PacketCodec.tuple(
            PacketCodecs.string(1024 * 1024), ShowNotificationPayload::message,
            PacketCodecs.string(1024 * 1024), ShowNotificationPayload::type,
            PacketCodecs.INTEGER, ShowNotificationPayload::durationSeconds,
            ShowNotificationPayload::new
    );

    @Override
    public CustomPayload.Id<? extends CustomPayload> getId() {
        return ID;
    }
}
