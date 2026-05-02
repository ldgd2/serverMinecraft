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

    @Inject(method = "interactMob", at = @At("HEAD"))
    private void onInteract(PlayerEntity player, net.minecraft.util.Hand hand, CallbackInfoReturnable<net.minecraft.util.ActionResult> cir) {
        if (!player.getWorld().isClient) {
            SheepEntity sheep = (SheepEntity) (Object) this;
            
            // Logro de encontrar oveja rosa
            if (sheep.getColor() == net.minecraft.util.DyeColor.PINK) {
                AchievementClient.sendEvent(player.getUuidAsString(), "pink_sheep_found", 1);
            }
            
            // Logro de esquilar oveja (reemplaza la inyeccion antigua en 'sheared')
            net.minecraft.item.ItemStack stack = player.getStackInHand(hand);
            if (stack.isOf(net.minecraft.item.Items.SHEARS) && sheep.isShearable()) {
                AchievementClient.sendEvent(player.getUuidAsString(), "sheep_sheared", 1);
            }
        }
    }
}
