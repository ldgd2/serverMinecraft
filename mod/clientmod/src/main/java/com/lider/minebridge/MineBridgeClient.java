package com.lider.minebridge;

import com.lider.minebridge.client.ClientEvents;
import com.lider.minebridge.achievements.AchievementModule;
import com.lider.minebridge.marketplace.MarketplaceModule;
import com.lider.minebridge.networking.payload.SyncSkinPayload;
import com.lider.minebridge.networking.payload.UpdateCountdownPayload;
import com.lider.minebridge.marketplace.networking.*;
import com.lider.minebridge.achievements.networking.AchievementUnlockPayload;
import net.fabricmc.api.ModInitializer;
import net.fabricmc.api.EnvType;
import net.fabricmc.api.Environment;
import net.fabricmc.fabric.api.networking.v1.PayloadTypeRegistry;

import com.lider.minebridge.networking.payload.SyncBackendUrlPayload;
import com.lider.minebridge.networking.BackendClient;
import net.fabricmc.api.ClientModInitializer;
import net.fabricmc.fabric.api.client.networking.v1.ClientPlayNetworking;

@Environment(EnvType.CLIENT)
public class MineBridgeClient implements ClientModInitializer {

    @Override
    public void onInitializeClient() {
        // Registro de Payloads Globales (Los específicos de módulo van en su init)
        PayloadTypeRegistry.playS2C().register(UpdateCountdownPayload.ID, UpdateCountdownPayload.CODEC);
        PayloadTypeRegistry.playS2C().register(SyncSkinPayload.ID, SyncSkinPayload.CODEC);
        PayloadTypeRegistry.playS2C().register(SyncBackendUrlPayload.ID, SyncBackendUrlPayload.CODEC);
        
        // Payloads de Logros
        PayloadTypeRegistry.playC2S().register(AchievementUnlockPayload.ID, AchievementUnlockPayload.CODEC);
        PayloadTypeRegistry.playS2C().register(AchievementUnlockPayload.ID, AchievementUnlockPayload.CODEC);

        // Payloads de Marketplace
        PayloadTypeRegistry.playC2S().register(MarketplaceRequestPayload.ID, MarketplaceRequestPayload.CODEC);
        PayloadTypeRegistry.playC2S().register(OpenCreationMenuPayload.ID, OpenCreationMenuPayload.CODEC);
        PayloadTypeRegistry.playC2S().register(OpenTransactionMenuPayload.ID, OpenTransactionMenuPayload.CODEC);
        PayloadTypeRegistry.playC2S().register(CompleteTradePayload.ID, CompleteTradePayload.CODEC);
        PayloadTypeRegistry.playC2S().register(PublishTradePayload.ID, PublishTradePayload.CODEC);
        PayloadTypeRegistry.playC2S().register(CancelTradePayload.ID, CancelTradePayload.CODEC);
        
        PayloadTypeRegistry.playS2C().register(MarketplaceDataPayload.ID, MarketplaceDataPayload.CODEC);
        PayloadTypeRegistry.playS2C().register(TransactionScreenDataPayload.ID, TransactionScreenDataPayload.CODEC);

        ClientPlayNetworking.registerGlobalReceiver(SyncBackendUrlPayload.ID, (payload, context) -> {
            BackendClient.updateUrl(payload.url());
        });

        // --- Carga de Módulos ---
        MarketplaceModule.initClient();
        AchievementModule.initClient();
        
        // Registros Globales Restantes
        ClientEvents.init();
    }
}
