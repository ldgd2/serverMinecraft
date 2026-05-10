package com.lider.minebridge.marketplace.networking;

import net.minecraft.network.RegistryByteBuf;
import net.minecraft.network.codec.PacketCodec;
import net.minecraft.network.codec.PacketCodecs;
import net.minecraft.network.packet.CustomPayload;
import net.minecraft.util.Identifier;

public record MarketplaceRequestPayload(String json) implements CustomPayload {
    public static final CustomPayload.Id<MarketplaceRequestPayload> ID = new CustomPayload.Id<>(Identifier.of("minebridge", "marketplace_request"));
    
    public static final PacketCodec<RegistryByteBuf, MarketplaceRequestPayload> CODEC = PacketCodec.tuple(
            PacketCodecs.string(1024 * 1024), MarketplaceRequestPayload::json, // 1MB limit for trade list
            MarketplaceRequestPayload::new
    );

    @Override
    public CustomPayload.Id<? extends CustomPayload> getId() {
        return ID;
    }
}
