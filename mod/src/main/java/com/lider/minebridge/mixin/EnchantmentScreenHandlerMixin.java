package com.lider.minebridge.mixin;

import com.lider.minebridge.events.items.ItemLogic;
import net.minecraft.enchantment.Enchantment;
import net.minecraft.item.ItemStack;
import net.minecraft.registry.entry.RegistryEntry;
import net.minecraft.screen.EnchantmentScreenHandler;
import net.minecraft.server.network.ServerPlayerEntity;
import net.minecraft.world.World;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfo;

import java.util.HashMap;
import java.util.Map;

@Mixin(EnchantmentScreenHandler.class)
public abstract class EnchantmentScreenHandlerMixin {

    @Inject(method = "method_17411", at = @At("TAIL"))
    private void onEnchanted(ItemStack stack, World world, net.minecraft.util.math.BlockPos pos, ServerPlayerEntity player, CallbackInfo ci) {
        // En 1.21, los encantamientos están en un componente
        net.minecraft.component.type.ItemEnchantmentsComponent component = stack.getEnchantments();
        Map<RegistryEntry<Enchantment>, Integer> enchants = new HashMap<>();
        
        for (it.unimi.dsi.fastutil.objects.Object2IntMap.Entry<RegistryEntry<Enchantment>> entry : component.getEnchantmentEntries()) {
            enchants.put(entry.getKey(), entry.getIntValue());
        }
        
        ItemLogic.onItemEnchanted(player, stack, 0, enchants);
    }
}
