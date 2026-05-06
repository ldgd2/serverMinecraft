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
    public static final ScreenHandlerType<MarketplaceTransactionScreenHandler> TYPE = 
        new ScreenHandlerType<>((syncId, inv) -> new MarketplaceTransactionScreenHandler(syncId, inv, -1), net.minecraft.resource.featuretoggle.FeatureSet.empty());

    private final Inventory inventory = new SimpleInventory(1); // 0: Pago
    private final int tradeId;

    public MarketplaceTransactionScreenHandler(int syncId, PlayerInventory playerInventory, int tradeId) {
        super(TYPE, syncId); 
        this.tradeId = tradeId;
        
        // Slot de PAGO (Donde el comprador pone lo que se pide)
        this.addSlot(new Slot(inventory, 0, 80, 35));

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
            if (invSlot < 1) {
                if (!this.insertItem(originalStack, 1, this.slots.size(), true)) {
                    return ItemStack.EMPTY;
                }
            } else if (!this.insertItem(originalStack, 0, 1, false)) {
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
}
