package com.lider.minebridge;

import com.lider.minebridge.client.ClientEvents;
import net.fabricmc.api.ModInitializer;
import net.fabricmc.api.EnvType;
import net.fabricmc.api.Environment;
import net.fabricmc.fabric.api.networking.v1.PayloadTypeRegistry;
import com.lider.minebridge.networking.payload.AchievementUnlockPayload;

@Environment(EnvType.CLIENT)
public class MineBridgeClient implements ModInitializer {
    @Override
    public void onInitialize() {
        PayloadTypeRegistry.playC2S().register(AchievementUnlockPayload.ID, AchievementUnlockPayload.CODEC);
        PayloadTypeRegistry.playS2C().register(com.lider.minebridge.networking.payload.UpdateCountdownPayload.ID, com.lider.minebridge.networking.payload.UpdateCountdownPayload.CODEC);
        PayloadTypeRegistry.playS2C().register(com.lider.minebridge.networking.payload.SyncSkinPayload.ID, com.lider.minebridge.networking.payload.SyncSkinPayload.CODEC);
        PayloadTypeRegistry.playC2S().register(com.lider.minebridge.networking.payload.MarketplaceRequestPayload.ID, com.lider.minebridge.networking.payload.MarketplaceRequestPayload.CODEC);
        PayloadTypeRegistry.playC2S().register(com.lider.minebridge.networking.payload.OpenCreationMenuPayload.ID, com.lider.minebridge.networking.payload.OpenCreationMenuPayload.CODEC);
        
        net.minecraft.client.gui.screen.ingame.HandledScreens.register(
            com.lider.minebridge.marketplace.MarketplaceCreationScreenHandler.TYPE, 
            com.lider.minebridge.client.ui.MarketplaceCreationScreen::new
        );

        ClientEvents.init();
    }
}
