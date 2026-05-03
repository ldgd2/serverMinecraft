package com.lider.minebridge.mixin;

import com.lider.minebridge.networking.AchievementClient;
import net.minecraft.entity.ItemEntity;
import net.minecraft.entity.player.PlayerEntity;
import net.minecraft.registry.Registries;
import net.minecraft.server.network.ServerPlayerEntity;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfo;

import java.util.Set;

@Mixin(ItemEntity.class)
public abstract class ItemEntityMixin {

    // Solo enviamos eventos para ítems que tienen logros mapeados
    private static final Set<String> ACHIEVEMENT_ITEMS = Set.of(
        // Minerales / materiales valiosos
        "diamond", "emerald", "amethyst_shard", "echo_shard",
        "netherite_ingot", "netherite_scrap", "ancient_debris",
        "nether_star", "dragon_egg",
        // Trofeos / drops especiales
        "wither_skeleton_skull", "creeper_head", "zombie_head",
        "ender_eye", "blaze_rod", "ghast_tear",
        "totem_of_undying", "trident",
        // Comida especial
        "golden_apple", "enchanted_golden_apple",
        // Libros / enchanting
        "enchanted_book"
    );

    @Inject(method = "onPlayerCollision", at = @At("HEAD"))
    private void onCollision(PlayerEntity player, CallbackInfo ci) {
        if (!(player instanceof ServerPlayerEntity serverPlayer) || serverPlayer.getWorld().isClient) return;

        ItemEntity item = (ItemEntity) (Object) this;
        if (item.getStack().isEmpty() || item.isRemoved()) return;

        String itemId = Registries.ITEM.getId(item.getStack().getItem()).getPath();

        // Solo enviamos si el ítem está en la whitelist de logros
        boolean relevant = false;
        for (String tracked : ACHIEVEMENT_ITEMS) {
            if (itemId.equals(tracked) || itemId.contains(tracked)) {
                relevant = true;
                break;
            }
        }

        if (!relevant) return; // Ignorar completamente cobblestone, dirt, madera, etc.

        String uuid = serverPlayer.getUuidAsString();
        int count = item.getStack().getCount();

        // Eventos específicos por ítem
        if (itemId.contains("diamond")) {
            AchievementClient.sendEvent(uuid, "item_acquired:minecraft:diamond", count);
        } else if (itemId.contains("emerald")) {
            AchievementClient.sendEvent(uuid, "item_acquired:minecraft:emerald", count);
        } else if (itemId.contains("totem")) {
            AchievementClient.sendEvent(uuid, "totem_collected", 1);
        } else if (itemId.contains("trident")) {
            AchievementClient.sendEvent(uuid, "trident_collected", 1);
        } else if (itemId.contains("enchanted_golden_apple")) {
            AchievementClient.sendEvent(uuid, "notch_apple_collected", 1);
        } else if (itemId.contains("nether_star")) {
            AchievementClient.sendEvent(uuid, "nether_star_collected", 1);
        } else if (itemId.contains("skull") || itemId.contains("head")) {
            AchievementClient.sendEvent(uuid, "skull_collected:minecraft:" + itemId, 1);
        }
        // No enviamos item_pickup genérico — era el mayor offender de tráfico
    }
}
