package com.lider.minebridge.mixin;

import com.lider.minebridge.networking.AchievementClient;
import net.minecraft.entity.ItemEntity;
import net.minecraft.entity.player.PlayerEntity;
import net.minecraft.registry.Registries;
import net.minecraft.server.network.ServerPlayerEntity;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfo;

@Mixin(ItemEntity.class)
public abstract class ItemEntityMixin {

    private long lastPickupTime = 0;
    
    @Inject(method = "onPlayerCollision", at = @At("HEAD"))
    private void onCollision(PlayerEntity player, CallbackInfo ci) {
        if (player instanceof ServerPlayerEntity serverPlayer && !serverPlayer.getWorld().isClient) {
            ItemEntity item = (ItemEntity) (Object) this;
            
            // Solo nos interesa si el jugador realmente puede recoger el objeto
            if (!item.getStack().isEmpty() && !item.isRemoved()) {
                long currentTime = System.currentTimeMillis();
                if (currentTime - lastPickupTime < 1000) {
                    return; // Evitar saturar el backend con el mismo objeto repetidas veces
                }
                lastPickupTime = currentTime;

                String itemId = Registries.ITEM.getId(item.getStack().getItem()).toString();
                int count = item.getStack().getCount();
                
                // Enviar el evento (reducido por el debounce)
                AchievementClient.sendEvent(serverPlayer.getUuidAsString(), "item_pickup:" + itemId, count);
                AchievementClient.sendEvent(serverPlayer.getUuidAsString(), "item_pickup", count);
                
                if (itemId.contains("emerald")) {
                    AchievementClient.sendEvent(serverPlayer.getUuidAsString(), "item_acquired:minecraft:emerald", count);
                }
            }
        }
    }
}
