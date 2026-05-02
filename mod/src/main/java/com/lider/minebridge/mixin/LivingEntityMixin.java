package com.lider.minebridge.mixin;

import com.lider.minebridge.events.combat.CombatLogic;
import com.lider.minebridge.events.special.MemeLogic;
import net.minecraft.entity.LivingEntity;
import net.minecraft.entity.damage.DamageSource;
import net.minecraft.registry.Registries;
import net.minecraft.server.network.ServerPlayerEntity;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfo;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfoReturnable;

@Mixin(LivingEntity.class)
public abstract class LivingEntityMixin {

    @Inject(method = "onDeath", at = @At("HEAD"))
    private void onDeath(DamageSource source, CallbackInfo ci) {
        LivingEntity victim = (LivingEntity) (Object) this;
        
        if (source.getAttacker() instanceof ServerPlayerEntity player) {
            String victimId = Registries.ENTITY_TYPE.getId(victim.getType()).toString().replace(":", ".");
            CombatLogic.onEntityKill(player.getUuidAsString(), "entity." + victimId);
        }
    }

    @Inject(method = "tryUseTotem", at = @At("RETURN"))
    private void onTotemUsed(DamageSource source, CallbackInfoReturnable<Boolean> cir) {
        if (cir.getReturnValue() && (Object)this instanceof ServerPlayerEntity player) {
            CombatLogic.onTotemUsed(player.getUuidAsString());
        }
    }

    @Inject(method = "addStatusEffect", at = @At("HEAD"))
    private void onEffectAdded(net.minecraft.entity.effect.StatusEffectInstance effect, CallbackInfoReturnable<Boolean> cir) {
        if ((Object)this instanceof ServerPlayerEntity player) {
            String effectId = effect.getEffectType().getKey().get().getValue().getPath();
            if (effectId.contains("darkness")) {
                CombatLogic.onWardenDarkness(player.getUuidAsString());
            }
        }
    }

    @Inject(method = "damage", at = @At("HEAD"))
    private void onDamage(DamageSource source, float amount, CallbackInfoReturnable<Boolean> cir) {
        if ((Object)this instanceof ServerPlayerEntity player) {
            MemeLogic.onAttackedWithoutArmor(player);
        }
    }
}
