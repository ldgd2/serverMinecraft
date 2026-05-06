package com.lider.minebridge.networking.payload;

import net.minecraft.network.RegistryByteBuf;
import net.minecraft.network.codec.PacketCodec;
import net.minecraft.network.packet.CustomPayload;
import net.minecraft.util.Identifier;

public record OpenCreationMenuPayload() implements CustomPayload {
    public static final CustomPayload.Id<OpenCreationMenuPayload> ID = new CustomPayload.Id<>(Identifier.of("minebridge", "open_creation"));
    public static final PacketCodec<RegistryByteBuf, OpenCreationMenuPayload> CODEC = PacketCodec.unit(new OpenCreationMenuPayload());

    @Override
    public CustomPayload.Id<? extends CustomPayload> getId() {
        return ID;
    }
}
