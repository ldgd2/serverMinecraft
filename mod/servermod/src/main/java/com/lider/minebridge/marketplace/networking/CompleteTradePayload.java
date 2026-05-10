package com.lider.minebridge.marketplace.networking;

import net.minecraft.network.RegistryByteBuf;
import net.minecraft.network.codec.PacketCodec;
import net.minecraft.network.codec.PacketCodecs;
import net.minecraft.network.packet.CustomPayload;
import net.minecraft.util.Identifier;

public record CompleteTradePayload(int tradeId) implements CustomPayload {
    public static final CustomPayload.Id<CompleteTradePayload> ID = new CustomPayload.Id<>(Identifier.of("minebridge", "complete_trade"));
    
    public static final PacketCodec<RegistryByteBuf, CompleteTradePayload> CODEC = PacketCodec.tuple(
            PacketCodecs.VAR_INT, CompleteTradePayload::tradeId,
            CompleteTradePayload::new
    );

    @Override
    public CustomPayload.Id<? extends CustomPayload> getId() {
        return ID;
    }
}
