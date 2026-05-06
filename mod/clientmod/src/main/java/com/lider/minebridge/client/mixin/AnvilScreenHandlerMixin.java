package com.lider.minebridge.client.mixin;

import com.lider.minebridge.events.ClientAchievementLogic;
import net.minecraft.entity.player.PlayerEntity;
import net.minecraft.screen.AnvilScreenHandler;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfo;

@Mixin(AnvilScreenHandler.class)
public class AnvilScreenHandlerMixin {
    @Inject(method = "onTakeOutput", at = @At("HEAD"))
    private void onAnvilTake(PlayerEntity player, net.minecraft.item.ItemStack stack, CallbackInfo ci) {
        if (player.getWorld().isClient) {
            ClientAchievementLogic.onAnvilUse();
        }
    }
}
