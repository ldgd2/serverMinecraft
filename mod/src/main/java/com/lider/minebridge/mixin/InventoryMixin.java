package com.lider.minebridge.mixin;

import com.lider.minebridge.networking.AchievementClient;
import net.minecraft.entity.player.PlayerEntity;
import net.minecraft.item.ItemStack;
import net.minecraft.server.network.ServerPlayerEntity;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfo;

@Mixin(PlayerEntity.class)
public abstract class InventoryMixin {

    @Inject(method = "increaseStat", at = @At("HEAD"))
    private void onStatIncreased(net.minecraft.stat.Stat<?> stat, int amount, CallbackInfo ci) {
        if ((Object)this instanceof ServerPlayerEntity player) {
            // Esto captura muchísimos eventos nativos de MC
            String statId = stat.getValue().toString().replace(":", ".");
            // AchievementClient.sendEvent(player.getUuidAsString(), "stat." + statId, amount);
        }
    }

    @Inject(method = "onHandledScreenClosed", at = @At("HEAD"))
    private void onContainerClosed(CallbackInfo ci) {
        if ((Object)this instanceof ServerPlayerEntity player) {
            // Verificar inventario al cerrar cofres o inventario
            for (ItemStack stack : player.getInventory().main) {
                if (!stack.isEmpty()) {
                    String itemId = stack.getItem().getTranslationKey();
                    if (itemId.contains("poisonous_potato")) {
                        AchievementClient.sendEvent(player.getUuidAsString(), "item_acquired:minecraft:poisonous_potato", 1);
                    }
                    if (itemId.contains("dragon_egg")) {
                        AchievementClient.sendEvent(player.getUuidAsString(), "has_dragon_egg", 1);
                    }
                }
            }
        }
    }
}
