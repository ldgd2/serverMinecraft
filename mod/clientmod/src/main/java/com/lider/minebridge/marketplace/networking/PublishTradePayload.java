package com.lider.minebridge.marketplace.networking;

import net.minecraft.network.RegistryByteBuf;
import net.minecraft.network.codec.PacketCodec;
import net.minecraft.network.codec.PacketCodecs;
import net.minecraft.network.packet.CustomPayload;
import net.minecraft.util.Identifier;

public record PublishTradePayload(String title) implements CustomPayload {
    public static final CustomPayload.Id<PublishTradePayload> ID = new CustomPayload.Id<>(Identifier.of("minebridge", "publish_trade"));
    
    public static final PacketCodec<RegistryByteBuf, PublishTradePayload> CODEC = PacketCodec.tuple(
            PacketCodecs.STRING, PublishTradePayload::title,
            PublishTradePayload::new
    );

    @Override
    public CustomPayload.Id<? extends CustomPayload> getId() {
        return ID;
    }
}
