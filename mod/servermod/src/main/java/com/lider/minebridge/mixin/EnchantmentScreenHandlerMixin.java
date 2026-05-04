package com.lider.minebridge.mixin;

import com.lider.minebridge.events.items.ItemLogic;
import net.minecraft.enchantment.Enchantment;
import net.minecraft.entity.player.PlayerEntity;
import net.minecraft.item.ItemStack;
import net.minecraft.registry.entry.RegistryEntry;
import net.minecraft.screen.EnchantmentScreenHandler;
import net.minecraft.server.network.ServerPlayerEntity;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfoReturnable;

import java.util.HashMap;
import java.util.Map;

@Mixin(EnchantmentScreenHandler.class)
public abstract class EnchantmentScreenHandlerMixin {

    @Inject(method = "onButtonClick", at = @At("RETURN"))
    private void onEnchanted(PlayerEntity playerEntity, int id, CallbackInfoReturnable<Boolean> cir) {
        if (cir.getReturnValue() != null && cir.getReturnValue() && playerEntity instanceof ServerPlayerEntity player) {
            EnchantmentScreenHandler handler = (EnchantmentScreenHandler) (Object) this;
            ItemStack stack = handler.getSlot(0).getStack();
            
            if (!stack.isEmpty()) {
                net.minecraft.component.type.ItemEnchantmentsComponent component = stack.getEnchantments();
                Map<RegistryEntry<Enchantment>, Integer> enchants = new HashMap<>();
                
                for (it.unimi.dsi.fastutil.objects.Object2IntMap.Entry<RegistryEntry<Enchantment>> entry : component.getEnchantmentEntries()) {
                    enchants.put(entry.getKey(), entry.getIntValue());
                }
                
                ItemLogic.onItemEnchanted(player, stack, 0, enchants);
            }
        }
    }
}
