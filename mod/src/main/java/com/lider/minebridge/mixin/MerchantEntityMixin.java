package com.lider.minebridge.mixin;

import com.lider.minebridge.events.special.MemeLogic;
import com.lider.minebridge.networking.AchievementClient;
import net.minecraft.entity.passive.MerchantEntity;
import net.minecraft.entity.passive.WanderingTraderEntity;
import net.minecraft.server.network.ServerPlayerEntity;
import net.minecraft.village.TradeOffer;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfo;

@Mixin({net.minecraft.entity.passive.VillagerEntity.class, net.minecraft.entity.passive.WanderingTraderEntity.class})
public abstract class MerchantEntityMixin {

    @Inject(method = "afterUsing", at = @At("HEAD"))
    private void onTrade(TradeOffer offer, CallbackInfo ci) {
        MerchantEntity merchant = (MerchantEntity) (Object) this;
        if (merchant.getCustomer() instanceof ServerPlayerEntity player) {
            com.lider.minebridge.events.economy.EconomyLogic.onTradeCompleted(
                player.getUuidAsString(), 
                offer.getOriginalFirstBuyItem(), 
                offer.getSellItem()
            );
            if (merchant instanceof WanderingTraderEntity) {
                MemeLogic.onWanderingTraderTrade(player);
            }
        }
    }
}
