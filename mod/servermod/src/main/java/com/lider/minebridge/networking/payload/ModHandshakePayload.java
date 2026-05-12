package com.lider.minebridge.networking.payload;

import net.minecraft.network.RegistryByteBuf;
import net.minecraft.network.codec.PacketCodec;
import net.minecraft.network.codec.PacketCodecs;
import net.minecraft.network.packet.CustomPayload;
import net.minecraft.util.Identifier;

/**
 * Payload para el intercambio de seguridad entre Cliente y Servidor.
 * El cliente envía su token de sesión al servidor para validar que tiene el mod y está logueado.
 */
public record ModHandshakePayload(String token) implements CustomPayload {
    public static final CustomPayload.Id<ModHandshakePayload> ID = new CustomPayload.Id<>(Identifier.of("minebridge", "mod_handshake"));
    
    public static final PacketCodec<RegistryByteBuf, ModHandshakePayload> CODEC = PacketCodec.tuple(
            PacketCodecs.string(2048), ModHandshakePayload::token,
            ModHandshakePayload::new
    );

    @Override
    public CustomPayload.Id<? extends CustomPayload> getId() {
        return ID;
    }
}
