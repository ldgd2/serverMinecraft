package com.lider.minebridge.networking.payload;

import net.minecraft.network.RegistryByteBuf;
import net.minecraft.network.codec.PacketCodec;
import net.minecraft.network.codec.PacketCodecs;
import net.minecraft.network.packet.CustomPayload;
import net.minecraft.util.Identifier;
import java.util.UUID;

public record SyncSkinPayload(UUID playerId, String value, String signature) implements CustomPayload {
    public static final CustomPayload.Id<SyncSkinPayload> ID = new CustomPayload.Id<>(Identifier.of("minebridge", "sync_skin"));
    public static final PacketCodec<RegistryByteBuf, SyncSkinPayload> CODEC = PacketCodec.tuple(
            net.minecraft.util.Uuids.PACKET_CODEC, SyncSkinPayload::playerId,
            PacketCodecs.string(128 * 1024), SyncSkinPayload::value,
            PacketCodecs.string(128 * 1024), SyncSkinPayload::signature,
            SyncSkinPayload::new
    );

    @Override
    public Id<? extends CustomPayload> getId() {
        return ID;
    }
}
