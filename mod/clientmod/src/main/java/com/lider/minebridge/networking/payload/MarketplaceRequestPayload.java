package com.lider.minebridge.networking.payload;

import net.minecraft.network.RegistryByteBuf;
import net.minecraft.network.codec.PacketCodec;
import net.minecraft.network.codec.PacketCodecs;
import net.minecraft.network.packet.CustomPayload;
import net.minecraft.util.Identifier;

public record MarketplaceRequestPayload(String tradeData) implements CustomPayload {
    public static final CustomPayload.Id<MarketplaceRequestPayload> ID = new CustomPayload.Id<>(Identifier.of("minebridge", "marketplace_request"));
    public static final PacketCodec<RegistryByteBuf, MarketplaceRequestPayload> CODEC = PacketCodec.tuple(
        PacketCodecs.STRING, MarketplaceRequestPayload::tradeData, MarketplaceRequestPayload::new
    );

    @Override
    public CustomPayload.Id<? extends CustomPayload> getId() {
        return ID;
    }
}
