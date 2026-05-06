package com.lider.minebridge.networking.payload;

import net.minecraft.network.RegistryByteBuf;
import net.minecraft.network.codec.PacketCodec;
import net.minecraft.network.codec.PacketCodecs;
import net.minecraft.network.packet.CustomPayload;
import net.minecraft.util.Identifier;

public record CompleteTradePayload(int tradeId) implements CustomPayload {
    public static final Id<CompleteTradePayload> ID = new Id<>(Identifier.of("minebridge", "complete_trade"));
    public static final PacketCodec<RegistryByteBuf, CompleteTradePayload> CODEC = PacketCodec.tuple(
            PacketCodecs.VAR_INT, CompleteTradePayload::tradeId,
            CompleteTradePayload::new
    );

    @Override
    public Id<? extends CustomPayload> getId() {
        return ID;
    }
}
