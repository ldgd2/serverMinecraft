package com.lider.minebridge.networking.payload;

import net.minecraft.item.ItemStack;
import net.minecraft.network.RegistryByteBuf;
import net.minecraft.network.codec.PacketCodec;
import net.minecraft.network.codec.PacketCodecs;
import net.minecraft.network.packet.CustomPayload;
import net.minecraft.util.Identifier;

public record TransactionScreenDataPayload(int tradeId, ItemStack req1, ItemStack req2) implements CustomPayload {
    public static final Id<TransactionScreenDataPayload> ID = new Id<>(Identifier.of("minebridge", "transaction_data"));
    public static final PacketCodec<RegistryByteBuf, TransactionScreenDataPayload> CODEC = PacketCodec.tuple(
            PacketCodecs.VAR_INT, TransactionScreenDataPayload::tradeId,
            ItemStack.PACKET_CODEC, TransactionScreenDataPayload::req1,
            ItemStack.PACKET_CODEC, TransactionScreenDataPayload::req2,
            TransactionScreenDataPayload::new
    );

    @Override
    public Id<? extends CustomPayload> getId() {
        return ID;
    }
}
