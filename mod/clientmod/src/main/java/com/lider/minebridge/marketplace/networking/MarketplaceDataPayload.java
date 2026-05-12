package com.lider.minebridge.marketplace.networking;

import net.minecraft.network.RegistryByteBuf;
import net.minecraft.network.codec.PacketCodec;
import net.minecraft.network.codec.PacketCodecs;
import net.minecraft.network.packet.CustomPayload;
import net.minecraft.util.Identifier;

/**
 * Payload: Envía la lista de trades (JSON) desde el servidor al cliente.
 */
public record MarketplaceDataPayload(String tradesJson) implements CustomPayload {
    public static final CustomPayload.Id<MarketplaceDataPayload> ID = new CustomPayload.Id<>(Identifier.of("minebridge", "marketplace_data"));
    
    public static final PacketCodec<RegistryByteBuf, MarketplaceDataPayload> CODEC = PacketCodec.tuple(
            PacketCodecs.string(1024 * 1024), MarketplaceDataPayload::tradesJson,
            MarketplaceDataPayload::new
    );

    @Override
    public CustomPayload.Id<? extends CustomPayload> getId() {
        return ID;
    }
}
