package com.lider.minebridge.marketplace.networking;

import net.minecraft.network.RegistryByteBuf;
import net.minecraft.network.codec.PacketCodec;
import net.minecraft.network.codec.PacketCodecs;
import net.minecraft.network.packet.CustomPayload;
import net.minecraft.util.Identifier;

public record TransactionScreenDataPayload(int tradeId, String requirementsJson) implements CustomPayload {
    public static final CustomPayload.Id<TransactionScreenDataPayload> ID = new CustomPayload.Id<>(Identifier.of("minebridge", "transaction_data"));
    
    public static final PacketCodec<RegistryByteBuf, TransactionScreenDataPayload> CODEC = PacketCodec.tuple(
            PacketCodecs.VAR_INT, TransactionScreenDataPayload::tradeId,
            PacketCodecs.STRING, TransactionScreenDataPayload::requirementsJson,
            TransactionScreenDataPayload::new
    );

    @Override
    public CustomPayload.Id<? extends CustomPayload> getId() {
        return ID;
    }
}
