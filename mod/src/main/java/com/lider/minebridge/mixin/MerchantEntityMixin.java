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

@Mixin(MerchantEntity.class)
public abstract class MerchantEntityMixin {

    @Inject(method = "afterUsing", at = @At("HEAD"))
    private void onTrade(TradeOffer offer, CallbackInfo ci) {
        MerchantEntity merchant = (MerchantEntity) (Object) this;
        if (merchant.getCustomer() instanceof ServerPlayerEntity player) {
            AchievementClient.sendEvent(player.getUuidAsString(), "villager_trade", 1);
            if (merchant instanceof WanderingTraderEntity) {
                MemeLogic.onWanderingTraderTrade(player);
            }
        }
    }
}
