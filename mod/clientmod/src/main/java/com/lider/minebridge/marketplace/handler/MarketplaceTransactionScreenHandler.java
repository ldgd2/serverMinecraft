package com.lider.minebridge.marketplace.handler;

import net.minecraft.entity.player.PlayerEntity;
import net.minecraft.entity.player.PlayerInventory;
import net.minecraft.inventory.Inventory;
import net.minecraft.inventory.SimpleInventory;
import net.minecraft.item.ItemStack;
import net.minecraft.screen.ScreenHandler;
import net.minecraft.screen.slot.Slot;
import java.util.List;

public class MarketplaceTransactionScreenHandler extends ScreenHandler {
    private final Inventory inventory = new SimpleInventory(9);
    private final int tradeId;
    private final List<ItemStack> requirements;

    public MarketplaceTransactionScreenHandler(int syncId, PlayerInventory playerInventory, int tradeId, List<ItemStack> requirements) {
        super(com.lider.minebridge.marketplace.MarketplaceModule.TRANSACTION_HANDLER, syncId); 
        this.tradeId = tradeId;
        this.requirements = requirements;
        
        for (int i = 0; i < 3; i++) {
            for (int j = 0; j < 3; j++) {
                this.addSlot(new Slot(inventory, j + i * 3, 35 + j * 18, 26 + i * 18));
            }
        }
        for (int i = 0; i < 3; i++) {
            for (int j = 0; j < 9; j++) {
                this.addSlot(new Slot(playerInventory, j + i * 9 + 9, 8 + j * 18, 84 + i * 18));
            }
        }
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
            if (invSlot < 9) {
                if (!this.insertItem(originalStack, 9, this.slots.size(), true)) return ItemStack.EMPTY;
            } else {
                if (!this.insertItem(originalStack, 0, 9, false)) return ItemStack.EMPTY;
            }
            if (originalStack.isEmpty()) slot.setStack(ItemStack.EMPTY);
            else slot.markDirty();
        }
        return newStack;
    }

    @Override
    public boolean canUse(PlayerEntity player) { return true; }
    public int getTradeId() { return tradeId; }
    public List<ItemStack> getRequirements() { return requirements; }
}
