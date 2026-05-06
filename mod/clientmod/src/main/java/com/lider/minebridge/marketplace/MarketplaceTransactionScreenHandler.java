package com.lider.minebridge.marketplace;

import net.minecraft.entity.player.PlayerEntity;
import net.minecraft.entity.player.PlayerInventory;
import net.minecraft.inventory.Inventory;
import net.minecraft.inventory.SimpleInventory;
import net.minecraft.item.ItemStack;
import net.minecraft.screen.ScreenHandler;
import net.minecraft.screen.ScreenHandlerType;
import net.minecraft.screen.slot.Slot;

public class MarketplaceTransactionScreenHandler extends ScreenHandler {

    private final Inventory inventory = new SimpleInventory(2); // 0: Pago 1, 1: Pago 2
    private final int tradeId;
    private final ItemStack req1;
    private final ItemStack req2;

    public MarketplaceTransactionScreenHandler(int syncId, PlayerInventory playerInventory, int tradeId, ItemStack req1, ItemStack req2) {
        super(com.lider.minebridge.MineBridgeClient.MARKETPLACE_TRANSACTION_HANDLER, syncId); 
        this.tradeId = tradeId;
        this.req1 = req1;
        this.req2 = req2;
        
        // Slots de PAGO (Donde el comprador pone lo que se pide)
        this.addSlot(new Slot(inventory, 0, 71, 40));
        this.addSlot(new Slot(inventory, 1, 97, 40));

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
            if (invSlot < 2) {
                if (!this.insertItem(originalStack, 2, this.slots.size(), true)) {
                    return ItemStack.EMPTY;
                }
            } else if (!this.insertItem(originalStack, 0, 2, false)) {
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

    public int getTradeId() {
        return tradeId;
    }

    public Inventory getInventory() {
        return inventory;
    }

    public ItemStack getReq1() { return req1; }
    public ItemStack getReq2() { return req2; }
}
