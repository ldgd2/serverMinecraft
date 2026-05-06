package com.lider.minebridge.marketplace;

import net.minecraft.entity.player.PlayerEntity;
import net.minecraft.entity.player.PlayerInventory;
import net.minecraft.inventory.Inventory;
import net.minecraft.inventory.SimpleInventory;
import net.minecraft.item.ItemStack;
import net.minecraft.screen.ScreenHandler;
import net.minecraft.screen.ScreenHandlerType;
import net.minecraft.screen.slot.Slot;
import net.minecraft.util.Identifier;

public class MarketplaceCreationScreenHandler extends ScreenHandler {

    private final Inventory inventory = new SimpleInventory(3); // 0: Selling, 1: Asking 1, 2: Asking 2

    public MarketplaceCreationScreenHandler(int syncId, PlayerInventory playerInventory) {
        super(net.minecraft.registry.Registries.SCREEN_HANDLER.get(net.minecraft.util.Identifier.of("minebridge", "creation")), syncId); 
        
        // Slot de VENTA (Item real que se entregará al completar)
        this.addSlot(new Slot(inventory, 0, 44, 35));
        
        // Slots de PEDIDO (Items de referencia)
        this.addSlot(new Slot(inventory, 1, 100, 35));
        this.addSlot(new Slot(inventory, 2, 126, 35));

        // Player Inventory
        for (int i = 0; i < 3; i++) {
            for (int j = 0; j < 9; j++) {
                this.addSlot(new Slot(playerInventory, j + i * 9 + 9, 8 + j * 18, 84 + i * 18));
            }
        }

        // Player Hotbar
        for (int i = 0; i < 9; i++) {
            this.addSlot(new Slot(playerInventory, i, 8 + i * 18, 142));
        }
    }

    @Override
    public ItemStack quickMove(PlayerEntity player, int invSlot) {
        ItemStack newStack = ItemStack.EMPTY;
        Slot slot = this.slots.get(invSlot);
        if (slot != null && slot.hasStack()) {
            ItemStack originalStack = slot.getStack();
            newStack = originalStack.copy();
            if (invSlot < 3) {
                if (!this.insertItem(originalStack, 3, this.slots.size(), true)) {
                    return ItemStack.EMPTY;
                }
            } else if (!this.insertItem(originalStack, 0, 3, false)) {
                return ItemStack.EMPTY;
            }

            if (originalStack.isEmpty()) {
                slot.setStack(ItemStack.EMPTY);
            } else {
                slot.markDirty();
            }
        }

        return newStack;
    }

    @Override
    public boolean canUse(PlayerEntity player) {
        return true;
    }

    public Inventory getTradeInventory() {
        return inventory;
    }
}
