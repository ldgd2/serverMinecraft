package com.lider.minebridge.mixin;

import com.lider.minebridge.events.economy.EconomyLogic;
import net.minecraft.entity.mob.PiglinBrain;
import net.minecraft.entity.mob.PiglinEntity;
import net.minecraft.item.ItemStack;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfo;

import java.util.List;

@Mixin(PiglinBrain.class)
public abstract class PiglinBrainMixin {

    @Inject(method = "barter(Lnet/minecraft/entity/mob/PiglinEntity;Ljava/util/List;)V", at = @At("HEAD"))
    private static void onBarter(PiglinEntity piglin, List<ItemStack> items, CallbackInfo ci) {
        if (piglin.getTarget() instanceof net.minecraft.entity.player.PlayerEntity player) {
            EconomyLogic.onPiglinBarter(player.getUuidAsString());
        }
    }
}
