package com.lider.minebridge.mixin;

import com.lider.minebridge.events.combat.CombatLogic;
import com.lider.minebridge.networking.AchievementClient;
import net.minecraft.entity.Entity;
import net.minecraft.entity.projectile.ProjectileEntity;
import net.minecraft.entity.mob.SkeletonEntity;
import net.minecraft.entity.mob.GhastEntity;
import net.minecraft.server.network.ServerPlayerEntity;
import net.minecraft.util.hit.EntityHitResult;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfo;

@Mixin(ProjectileEntity.class)
public abstract class ProjectileEntityMixin {

    @Inject(method = "onEntityHit", at = @At("HEAD"))
    private void onHit(EntityHitResult entityHitResult, CallbackInfo ci) {
        ProjectileEntity projectile = (ProjectileEntity) (Object) this;
        Entity victim = entityHitResult.getEntity();
        Entity owner = projectile.getOwner();

        if (owner instanceof ServerPlayerEntity player) {
            // 1. SKELETON SNIPER (Duelo a distancia)
            if (victim instanceof SkeletonEntity) {
                double distance = player.getPos().distanceTo(victim.getPos());
                CombatLogic.onSkeletonSnipe(player.getUuidAsString(), distance);
            }

            // 2. GHAST FIREBALL RETURN (Devolución de cortesía)
            // Si el proyectil es una bola de fuego (o similar) y mata a un Ghast
            if (victim instanceof GhastEntity ghast && ghast.isDead()) {
                AchievementClient.sendEvent(player.getUuidAsString(), "ghast_fireball_kill", 1);
            }
        }
    }
}
