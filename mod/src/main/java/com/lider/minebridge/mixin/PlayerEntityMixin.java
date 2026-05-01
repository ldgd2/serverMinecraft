package com.lider.minebridge.mixin;

import com.lider.minebridge.MineBridge;
import com.lider.minebridge.networking.BackendClient;
import net.minecraft.entity.ItemEntity;
import net.minecraft.entity.player.PlayerEntity;
import net.minecraft.item.ItemStack;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfo;

@Mixin(PlayerEntity.class)
public abstract class PlayerEntityMixin {
    
    @Inject(method = "sendPickup", at = @At("HEAD"))
    private void onPickupItem(net.minecraft.entity.Entity itemEntity, int count, CallbackInfo ci) {
        if (itemEntity instanceof ItemEntity item) {
            PlayerEntity player = (PlayerEntity) (Object) this;
            if (!player.getWorld().isClient) {
                ItemStack stack = item.getStack();
                String itemName = stack.getItem().getTranslationKey();
                int amount = stack.getCount();
                
                // Only send to backend if amount > 0 and client is ready
                if (amount > 0 && MineBridge.getBackendClient() != null) {
                    MineBridge.getBackendClient().notifyStatUpdate(
                        player.getName().getString(), 
                        "item_pickup", 
                        itemName, 
                        amount
                    );
                }
            }
        }
    }
}
