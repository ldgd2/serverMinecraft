package com.lider.minebridge.mixin;

import com.lider.minebridge.events.items.ItemLogic;
import net.minecraft.block.entity.BrewingStandBlockEntity;
import net.minecraft.inventory.Inventory;
import net.minecraft.item.ItemStack;
import net.minecraft.util.math.BlockPos;
import net.minecraft.world.World;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfo;

@Mixin(BrewingStandBlockEntity.class)
public abstract class BrewingStandBlockEntityMixin {

    @Inject(method = "craft", at = @At("HEAD"))
    private static void onPotionCrafted(World world, BlockPos pos, net.minecraft.util.collection.DefaultedList<ItemStack> slots, CallbackInfo ci) {
        // Encontrar al jugador más cercano al soporte de pociones (simplificación)
        // O mejor, el mod captura quién abrió el soporte anteriormente.
        // Por ahora, lo reportamos si hay un jugador cerca.
        net.minecraft.entity.player.PlayerEntity player = world.getClosestPlayer(pos.getX(), pos.getY(), pos.getZ(), 8.0, false);
        if (player != null) {
            ItemLogic.onPotionBrewed(player.getUuidAsString(), "unknown");
        }
    }
}
