package com.lider.minebridge.networking.payload;

import net.minecraft.network.RegistryByteBuf;
import net.minecraft.network.codec.PacketCodec;
import net.minecraft.network.codec.PacketCodecs;
import net.minecraft.network.packet.CustomPayload;
import net.minecraft.util.Identifier;

public record UpdateCountdownPayload(int seconds) implements CustomPayload {
    public static final CustomPayload.Id<UpdateCountdownPayload> ID = new CustomPayload.Id<>(Identifier.of("minebridge", "update_countdown"));
    public static final PacketCodec<RegistryByteBuf, UpdateCountdownPayload> CODEC = PacketCodec.tuple(
            PacketCodecs.INTEGER, UpdateCountdownPayload::seconds,
            UpdateCountdownPayload::new
    );

    @Override
    public Id<? extends CustomPayload> getId() {
        return ID;
    }
}
