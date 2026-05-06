package com.lider.minebridge;

import com.lider.minebridge.client.ClientEvents;
import net.fabricmc.api.ModInitializer;
import net.fabricmc.api.EnvType;
import net.fabricmc.api.Environment;
import net.fabricmc.fabric.api.networking.v1.PayloadTypeRegistry;
import com.lider.minebridge.networking.payload.AchievementUnlockPayload;
import net.minecraft.util.Identifier;
import net.minecraft.registry.Registries;
import net.minecraft.registry.Registry;
import net.minecraft.screen.ScreenHandlerType;

@Environment(EnvType.CLIENT)
public class MineBridgeClient implements ModInitializer {
    public static ScreenHandlerType<com.lider.minebridge.marketplace.MarketplaceCreationScreenHandler> MARKETPLACE_CREATION_HANDLER;
    public static ScreenHandlerType<com.lider.minebridge.marketplace.MarketplaceTransactionScreenHandler> MARKETPLACE_TRANSACTION_HANDLER;

    @Override
    public void onInitialize() {
        PayloadTypeRegistry.playC2S().register(AchievementUnlockPayload.ID, AchievementUnlockPayload.CODEC);
        PayloadTypeRegistry.playS2C().register(com.lider.minebridge.networking.payload.UpdateCountdownPayload.ID, com.lider.minebridge.networking.payload.UpdateCountdownPayload.CODEC);
        PayloadTypeRegistry.playS2C().register(com.lider.minebridge.networking.payload.SyncSkinPayload.ID, com.lider.minebridge.networking.payload.SyncSkinPayload.CODEC);
        PayloadTypeRegistry.playC2S().register(com.lider.minebridge.networking.payload.MarketplaceRequestPayload.ID, com.lider.minebridge.networking.payload.MarketplaceRequestPayload.CODEC);
        PayloadTypeRegistry.playC2S().register(com.lider.minebridge.networking.payload.OpenCreationMenuPayload.ID, com.lider.minebridge.networking.payload.OpenCreationMenuPayload.CODEC);
        PayloadTypeRegistry.playC2S().register(com.lider.minebridge.networking.payload.OpenTransactionMenuPayload.ID, com.lider.minebridge.networking.payload.OpenTransactionMenuPayload.CODEC);
        PayloadTypeRegistry.playC2S().register(com.lider.minebridge.networking.payload.CompleteTradePayload.ID, com.lider.minebridge.networking.payload.CompleteTradePayload.CODEC);
        PayloadTypeRegistry.playS2C().register(com.lider.minebridge.networking.payload.TransactionScreenDataPayload.ID, com.lider.minebridge.networking.payload.TransactionScreenDataPayload.CODEC);
        
        MARKETPLACE_CREATION_HANDLER = Registry.register(Registries.SCREEN_HANDLER, Identifier.of("minebridge", "creation"), 
            new net.minecraft.screen.ScreenHandlerType<>(com.lider.minebridge.marketplace.MarketplaceCreationScreenHandler::new, net.minecraft.resource.featuretoggle.FeatureSet.empty()));

        MARKETPLACE_TRANSACTION_HANDLER = Registry.register(Registries.SCREEN_HANDLER, Identifier.of("minebridge", "transaction"), 
            new net.fabricmc.fabric.api.screenhandler.v1.ExtendedScreenHandlerType<>(
                (syncId, inv, data) -> new com.lider.minebridge.marketplace.MarketplaceTransactionScreenHandler(syncId, inv, data.tradeId(), data.req1(), data.req2()),
                com.lider.minebridge.networking.payload.TransactionScreenDataPayload.CODEC
            ));

        net.minecraft.client.gui.screen.ingame.HandledScreens.register(
            MARKETPLACE_CREATION_HANDLER, 
            com.lider.minebridge.client.ui.MarketplaceCreationScreen::new
        );

        net.minecraft.client.gui.screen.ingame.HandledScreens.register(
            MARKETPLACE_TRANSACTION_HANDLER, 
            com.lider.minebridge.client.ui.MarketplaceTransactionScreen::new
        );

        ClientEvents.init();
    }
}
