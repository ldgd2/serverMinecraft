package com.lider.minebridge.marketplace.networking;

import net.minecraft.network.RegistryByteBuf;
import net.minecraft.network.codec.PacketCodec;
import net.minecraft.network.codec.PacketCodecs;
import net.minecraft.network.packet.CustomPayload;
import net.minecraft.util.Identifier;

public record CancelTradePayload(int tradeId) implements CustomPayload {
    public static final CustomPayload.Id<CancelTradePayload> ID = new CustomPayload.Id<>(Identifier.of("minebridge", "cancel_trade"));
    
    public static final PacketCodec<RegistryByteBuf, CancelTradePayload> CODEC = PacketCodec.tuple(
            PacketCodecs.VAR_INT, CancelTradePayload::tradeId,
            CancelTradePayload::new
    );

    @Override
    public CustomPayload.Id<? extends CustomPayload> getId() {
        return ID;
    }
}
