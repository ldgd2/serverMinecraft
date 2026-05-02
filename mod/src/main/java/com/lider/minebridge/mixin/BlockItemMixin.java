package com.lider.minebridge.mixin;

import com.lider.minebridge.events.blocks.BlockLogic;
import net.minecraft.item.BlockItem;
import net.minecraft.item.ItemPlacementContext;
import net.minecraft.registry.Registries;
import net.minecraft.util.ActionResult;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfoReturnable;

@Mixin(BlockItem.class)
public abstract class BlockItemMixin {

    @Inject(method = "place", at = @At("RETURN"))
    private void onPlace(ItemPlacementContext context, CallbackInfoReturnable<ActionResult> cir) {
        if (cir.getReturnValue() == ActionResult.SUCCESS || cir.getReturnValue() == ActionResult.CONSUME) {
            if (context.getPlayer() != null && !context.getWorld().isClient) {
                BlockItem item = (BlockItem) (Object) this;
                String blockId = Registries.BLOCK.getId(item.getBlock()).toString();
                BlockLogic.onBlockPlaced(blockId, context.getPlayer().getUuidAsString());
            }
        }
    }
}
