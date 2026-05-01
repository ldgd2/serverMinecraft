package com.lider.minebridge.mixin;

import com.lider.minebridge.MineBridge;
import net.minecraft.entity.damage.DamageSource;
import net.minecraft.server.network.ServerPlayerEntity;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfo;

@Mixin(ServerPlayerEntity.class)
public abstract class ServerPlayerEntityMixin {
    private int tickCounter = 0;

    @Inject(method = "onDeath", at = @At("HEAD"))
    private void onPlayerDeath(DamageSource source, CallbackInfo ci) {
        ServerPlayerEntity player = (ServerPlayerEntity) (Object) this;
        String killerName = source.getAttacker() != null ? source.getAttacker().getName().getString() : "environment";
        String cause = source.getName();
        
        if (MineBridge.getBackendClient() != null) {
            MineBridge.getBackendClient().notifyPlayerDeath(
                player.getName().getString(),
                cause,
                killerName
            );
        }
    }

    @Inject(method = "tick", at = @At("TAIL"))
    private void onTick(CallbackInfo ci) {
        ServerPlayerEntity player = (ServerPlayerEntity) (Object) this;
        
        // Every 5 seconds (100 ticks) send state update to backend
        tickCounter++;
        if (tickCounter >= 100 && MineBridge.getBackendClient() != null) {
            tickCounter = 0;
            MineBridge.getBackendClient().notifyPlayerState(
                player.getName().getString(),
                player.getHealth(),
                player.getHungerManager().getFoodLevel(),
                player.getX(),
                player.getY(),
                player.getZ(),
                player.getWorld().getRegistryKey().getValue().toString()
            );
        }
    }
}
