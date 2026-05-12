package com.lider.minebridge.networking.payload;

import net.minecraft.network.RegistryByteBuf;
import net.minecraft.network.codec.PacketCodec;
import net.minecraft.network.codec.PacketCodecs;
import net.minecraft.network.packet.CustomPayload;
import net.minecraft.util.Identifier;

public record ShowAlertPayload(String title, String description, int color, int durationSeconds) implements CustomPayload {
    public static final CustomPayload.Id<ShowAlertPayload> ID = new CustomPayload.Id<>(Identifier.of("minebridge", "show_alert"));

    public static final PacketCodec<RegistryByteBuf, ShowAlertPayload> CODEC = PacketCodec.tuple(
            PacketCodecs.string(1024 * 1024), ShowAlertPayload::title,
            PacketCodecs.string(1024 * 1024), ShowAlertPayload::description,
            PacketCodecs.INTEGER, ShowAlertPayload::color,
            PacketCodecs.INTEGER, ShowAlertPayload::durationSeconds,
            ShowAlertPayload::new
    );

    @Override
    public CustomPayload.Id<? extends CustomPayload> getId() {
        return ID;
    }
}
