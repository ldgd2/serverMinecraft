package com.lider.minebridge.events.modules;

import com.lider.minebridge.networking.AchievementClient;
import net.minecraft.entity.Entity;
import net.minecraft.registry.Registries;
import net.minecraft.server.network.ServerPlayerEntity;

public class WorldEvents {
    public static void onEntityInteract(ServerPlayerEntity player, Entity entity) {
        String entityId = Registries.ENTITY_TYPE.getId(entity.getType()).toString();
        AchievementClient.sendEvent(player.getUuidAsString(), "entity_interact:" + entityId, 1);
    }
}
