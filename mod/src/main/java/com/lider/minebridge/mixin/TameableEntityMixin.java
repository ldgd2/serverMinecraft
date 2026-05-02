package com.lider.minebridge.mixin;

import com.lider.minebridge.networking.AchievementClient;
import net.minecraft.entity.passive.TameableEntity;
import net.minecraft.entity.player.PlayerEntity;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfo;

@Mixin(TameableEntity.class)
public abstract class TameableEntityMixin {

    @Inject(method = "setOwner", at = @At("HEAD"))
    private void onTamed(PlayerEntity player, CallbackInfo ci) {
        if (player != null && !player.getWorld().isClient) {
            AchievementClient.sendEvent(player.getUuidAsString(), "animal_tamed", 1);
        }
    }
}
