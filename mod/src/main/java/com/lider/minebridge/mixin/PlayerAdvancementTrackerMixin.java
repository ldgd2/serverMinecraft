package com.lider.minebridge.mixin;

import com.lider.minebridge.MineBridge;
import net.minecraft.advancement.AdvancementEntry;
import net.minecraft.advancement.PlayerAdvancementTracker;
import net.minecraft.server.network.ServerPlayerEntity;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.Shadow;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfoReturnable;

@Mixin(PlayerAdvancementTracker.class)
public abstract class PlayerAdvancementTrackerMixin {
    
    @Shadow private ServerPlayerEntity owner;

    @Inject(method = "grantCriterion", at = @At("RETURN"))
    private void onAdvancementGrant(AdvancementEntry advancement, String criterionName, CallbackInfoReturnable<Boolean> cir) {
        if (cir.getReturnValue() && this.owner != null && !this.owner.getWorld().isClient) {
            String advId = advancement.id().toString();
            // We only send if it's a real advancement (not recipes, etc. unless desired)
            if (advId.contains("adventure") || advId.contains("nether") || advId.contains("end") || advId.contains("husbandry") || advId.contains("story")) {
                MineBridge.getBackendClient().notifyStatUpdate(
                    this.owner.getName().getString(),
                    "advancement",
                    advId
                );
                
                // Mapeo específico para Piglin Barter
                if (advId.contains("distract_piglin")) {
                    com.lider.minebridge.networking.AchievementClient.sendEvent(this.owner.getUuidAsString(), "piglin_barter", 1);
                }
            }
        }
    }
}
