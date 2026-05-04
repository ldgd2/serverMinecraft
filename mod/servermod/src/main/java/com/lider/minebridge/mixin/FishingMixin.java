package com.lider.minebridge.mixin;

import com.lider.minebridge.events.world.WorldLogic;
import net.minecraft.entity.projectile.FishingBobberEntity;
import net.minecraft.item.ItemStack;
import net.minecraft.server.network.ServerPlayerEntity;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfoReturnable;

@Mixin(FishingBobberEntity.class)
public abstract class FishingMixin {

    @Inject(method = "use", at = @At("RETURN"))
    private void onFishCaught(ItemStack usedItem, CallbackInfoReturnable<Integer> cir) {
        FishingBobberEntity bobber = (FishingBobberEntity)(Object)this;
        if (bobber.getOwner() instanceof ServerPlayerEntity player) {
                WorldLogic.onFishCaught(player.getUuidAsString(), "fish");
        }
    }
}
