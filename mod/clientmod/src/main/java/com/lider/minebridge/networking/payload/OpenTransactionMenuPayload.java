package com.lider.minebridge.networking.payload;

import net.minecraft.network.RegistryByteBuf;
import net.minecraft.network.codec.PacketCodec;
import net.minecraft.network.codec.PacketCodecs;
import net.minecraft.network.packet.CustomPayload;
import net.minecraft.util.Identifier;

public record OpenTransactionMenuPayload(int tradeId) implements CustomPayload {
    public static final CustomPayload.Id<OpenTransactionMenuPayload> ID = new CustomPayload.Id<>(Identifier.of("minebridge", "open_transaction"));
    public static final PacketCodec<RegistryByteBuf, OpenTransactionMenuPayload> CODEC = PacketCodec.tuple(
        PacketCodecs.VAR_INT, OpenTransactionMenuPayload::tradeId,
        OpenTransactionMenuPayload::new
    );

    @Override
    public CustomPayload.Id<? extends CustomPayload> getId() {
        return ID;
    }
}
