package com.lider.minebridge.mixin;

import com.lider.minebridge.MineBridge;
import com.lider.minebridge.events.player.PlayerLogic;
import com.lider.minebridge.events.special.MemeLogic;
import net.minecraft.entity.damage.DamageSource;
import net.minecraft.server.network.ServerPlayerEntity;
import net.minecraft.server.world.ServerWorld;
import net.minecraft.text.Text;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfo;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfoReturnable;

@Mixin(ServerPlayerEntity.class)
public abstract class ServerPlayerEntityMixin {
    private int tickCounter = 0;

    @Inject(method = "onDeath", at = @At("HEAD"))
    private void onPlayerDeath(DamageSource source, CallbackInfo ci) {
        ServerPlayerEntity player = (ServerPlayerEntity) (Object) this;
        Text deathMessage = player.getDamageTracker().getDeathMessage();
        PlayerLogic.onPlayerDeath(player, source, deathMessage);
    }

    @Inject(method = "teleport", at = @At("HEAD"))
    private void onDimensionChange(ServerWorld destination, double x, double y, double z, java.util.Set<net.minecraft.network.packet.s2c.play.PositionFlag> flags, float yaw, float pitch, CallbackInfo ci) {
        ServerPlayerEntity player = (ServerPlayerEntity) (Object) this;
        String dimId = destination.getRegistryKey().getValue().toString();
        PlayerLogic.onDimensionChange(player, dimId);
    }

    @Inject(method = "tick", at = @At("TAIL"))
    private void onTick(CallbackInfo ci) {
        ServerPlayerEntity player = (ServerPlayerEntity) (Object) this;
        
        PlayerLogic.checkPhysicalAchievements(player);

        tickCounter++;
        if (tickCounter >= 100 && MineBridge.getServer() != null) {
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

    @Inject(method = "damage", at = @At("TAIL"))
    private void onDamage(DamageSource source, float amount, CallbackInfoReturnable<Boolean> cir) {
        ServerPlayerEntity player = (ServerPlayerEntity) (Object) this;
        // En 1.21 DamageSource es complejo, usaremos un check simple
        PlayerLogic.onPlayerDamage(player, amount, source.getName().equals("fall"));
    }

    @Inject(method = "dropItem", at = @At("RETURN"))
    private void onDrop(net.minecraft.item.ItemStack stack, boolean throwRandomly, boolean retainOwnership, CallbackInfoReturnable<net.minecraft.entity.ItemEntity> cir) {
        ServerPlayerEntity player = (ServerPlayerEntity) (Object) this;
        MemeLogic.onItemDropped(player, stack);
    }
}
