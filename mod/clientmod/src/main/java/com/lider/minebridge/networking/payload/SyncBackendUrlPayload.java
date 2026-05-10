package com.lider.minebridge.networking.payload;

import net.minecraft.network.RegistryByteBuf;
import net.minecraft.network.codec.PacketCodec;
import net.minecraft.network.codec.PacketCodecs;
import net.minecraft.network.packet.CustomPayload;
import net.minecraft.util.Identifier;

/**
 * Sincroniza la URL del backend con el cliente para llamadas API directas.
 */
public record SyncBackendUrlPayload(String url) implements CustomPayload {
    public static final CustomPayload.Id<SyncBackendUrlPayload> ID = new CustomPayload.Id<>(Identifier.of("minebridge", "sync_backend_url"));
    
    public static final PacketCodec<RegistryByteBuf, SyncBackendUrlPayload> CODEC = PacketCodec.tuple(
            PacketCodecs.STRING, SyncBackendUrlPayload::url,
            SyncBackendUrlPayload::new
    );

    @Override
    public CustomPayload.Id<? extends CustomPayload> getId() {
        return ID;
    }
}
