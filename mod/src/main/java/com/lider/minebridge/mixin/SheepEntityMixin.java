package com.lider.minebridge.mixin;

import com.lider.minebridge.networking.AchievementClient;
import net.minecraft.entity.passive.SheepEntity;
import net.minecraft.entity.player.PlayerEntity;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfo;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfoReturnable;

@Mixin(SheepEntity.class)
public abstract class SheepEntityMixin {

    @Inject(method = "sheared", at = @At("HEAD"))
    private void onSheared(PlayerEntity player, net.minecraft.item.ItemStack item, net.minecraft.world.World world, net.minecraft.util.math.BlockPos pos, CallbackInfo ci) {
        if (!player.getWorld().isClient) {
            AchievementClient.sendEvent(player.getUuidAsString(), "sheep_sheared", 1);
        }
    }

    @Inject(method = "interactMob", at = @At("HEAD"))
    private void onInteract(PlayerEntity player, net.minecraft.util.Hand hand, CallbackInfoReturnable<net.minecraft.util.ActionResult> cir) {
        SheepEntity sheep = (SheepEntity) (Object) this;
        if (sheep.getColor() == net.minecraft.util.DyeColor.PINK) {
            AchievementClient.sendEvent(player.getUuidAsString(), "pink_sheep_found", 1);
        }
    }
}
