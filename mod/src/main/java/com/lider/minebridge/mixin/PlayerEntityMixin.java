package com.lider.minebridge.mixin;

import com.lider.minebridge.networking.AchievementClient;
import net.minecraft.entity.Entity;
import net.minecraft.entity.player.PlayerEntity;
import net.minecraft.registry.Registries;
import net.minecraft.util.math.BlockPos;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfo;

@Mixin(PlayerEntity.class)
public abstract class PlayerEntityMixin {

    @Inject(method = "sleep(Lnet/minecraft/util/math/BlockPos;)V", at = @At("HEAD"))
    private void onSleep(BlockPos pos, CallbackInfo ci) {
        PlayerEntity player = (PlayerEntity) (Object) this;
        if (!player.getWorld().isClient) {
            AchievementClient.sendEvent(player.getUuidAsString(), "bed_slept", 1);
        }
    }

    @Inject(method = "sendPickup(Lnet/minecraft/entity/Entity;I)V", at = @At("HEAD"))
    private void onPickup(Entity itemEntity, int count, CallbackInfo ci) {
        PlayerEntity player = (PlayerEntity) (Object) this;
        if (!player.getWorld().isClient && itemEntity instanceof net.minecraft.entity.ItemEntity) {
            net.minecraft.entity.ItemEntity item = (net.minecraft.entity.ItemEntity) itemEntity;
            String itemId = Registries.ITEM.getId(item.getStack().getItem()).toString();
            
            AchievementClient.sendEvent(player.getUuidAsString(), "item_pickup:" + itemId, count);
            AchievementClient.sendEvent(player.getUuidAsString(), "item_pickup", count);
            
            if (itemId.contains("emerald")) {
                AchievementClient.sendEvent(player.getUuidAsString(), "item_acquired:minecraft:emerald", count);
            }
        }
    }
}
