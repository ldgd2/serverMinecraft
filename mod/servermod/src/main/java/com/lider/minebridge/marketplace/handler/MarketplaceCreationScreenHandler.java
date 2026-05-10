package com.lider.minebridge.marketplace.handler;

import net.minecraft.entity.player.PlayerEntity;
import net.minecraft.entity.player.PlayerInventory;
import net.minecraft.inventory.Inventory;
import net.minecraft.inventory.SimpleInventory;
import net.minecraft.item.ItemStack;
import net.minecraft.screen.ScreenHandler;
import net.minecraft.screen.slot.Slot;

public class MarketplaceCreationScreenHandler extends ScreenHandler {
    private final Inventory inventory = new SimpleInventory(18);

    public MarketplaceCreationScreenHandler(int syncId, PlayerInventory playerInventory) {
        super(com.lider.minebridge.marketplace.MarketplaceModule.CREATION_HANDLER, syncId); 
        
        // Requisitos (Derecha) - Slots 9-17
        for (int i = 0; i < 3; i++) {
            for (int j = 0; j < 3; j++) {
                this.addSlot(new Slot(inventory, 9 + j + i * 3, 108 + j * 18, 40 + i * 18));
            }
        }
        // Oferta (Izquierda) - Slots 0-8
        for (int i = 0; i < 3; i++) {
            for (int j = 0; j < 3; j++) {
                this.addSlot(new Slot(inventory, j + i * 3, 34 + j * 18, 40 + i * 18));
            }
        }
        // Inventario del Jugador
        for (int i = 0; i < 3; i++) {
            for (int j = 0; j < 9; j++) {
                this.addSlot(new Slot(playerInventory, j + i * 9 + 9, 17 + j * 18, 112 + i * 18));
            }
        }
        // Hotbar
        for (int i = 0; i < 9; i++) {
            this.addSlot(new Slot(playerInventory, i, 17 + i * 18, 172));
        }
    }

    @Override
    public ItemStack quickMove(PlayerEntity player, int invSlot) {
        ItemStack newStack = ItemStack.EMPTY;
        Slot slot = this.slots.get(invSlot);
        if (slot != null && slot.hasStack()) {
            ItemStack originalStack = slot.getStack();
            newStack = originalStack.copy();
            if (invSlot < 18) {
                if (!this.insertItem(originalStack, 18, this.slots.size(), true)) return ItemStack.EMPTY;
            } else {
                if (!this.insertItem(originalStack, 0, 18, false)) return ItemStack.EMPTY;
            }
            if (originalStack.isEmpty()) slot.setStack(ItemStack.EMPTY);
            else slot.markDirty();
        }
        return newStack;
    }

    @Override
    public boolean canUse(PlayerEntity player) { return true; }
    public Inventory getTradeInventory() { return inventory; }
    
    @Override
    public void onClosed(PlayerEntity player) {
        super.onClosed(player);
        this.dropInventory(player, inventory);
    }
}
