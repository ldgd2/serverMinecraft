package com.lider.minebridge.marketplace;

import com.lider.minebridge.marketplace.handler.MarketplaceCreationScreenHandler;
import com.lider.minebridge.marketplace.handler.MarketplaceTransactionScreenHandler;
import com.lider.minebridge.marketplace.networking.*;
import net.fabricmc.fabric.api.networking.v1.PayloadTypeRegistry;
import net.minecraft.registry.Registries;
import net.minecraft.registry.Registry;
import net.minecraft.screen.ScreenHandlerType;
import net.minecraft.util.Identifier;

/**
 * Módulo Central de Marketplace: Encapsula toda la lógica, red y registros.
 */
public class MarketplaceModule {
    public static ScreenHandlerType<MarketplaceCreationScreenHandler> CREATION_HANDLER;
    public static ScreenHandlerType<MarketplaceTransactionScreenHandler> TRANSACTION_HANDLER;

    public static void initCommon() {
        // Registro de Payloads (Módulo Marketplace)
        PayloadTypeRegistry.playC2S().register(OpenCreationMenuPayload.ID, OpenCreationMenuPayload.CODEC);
        PayloadTypeRegistry.playC2S().register(OpenTransactionMenuPayload.ID, OpenTransactionMenuPayload.CODEC);
        PayloadTypeRegistry.playC2S().register(CompleteTradePayload.ID, CompleteTradePayload.CODEC);
        PayloadTypeRegistry.playS2C().register(TransactionScreenDataPayload.ID, TransactionScreenDataPayload.CODEC);
        PayloadTypeRegistry.playS2C().register(MarketplaceDataPayload.ID, MarketplaceDataPayload.CODEC);
        PayloadTypeRegistry.playC2S().register(PublishTradePayload.ID, PublishTradePayload.CODEC);
        PayloadTypeRegistry.playC2S().register(CancelTradePayload.ID, CancelTradePayload.CODEC);

        // Registro de Handlers
        CREATION_HANDLER = Registry.register(Registries.SCREEN_HANDLER, Identifier.of("minebridge", "creation"), 
            new ScreenHandlerType<>(MarketplaceCreationScreenHandler::new, net.minecraft.resource.featuretoggle.FeatureSet.empty()));

        TRANSACTION_HANDLER = Registry.register(Registries.SCREEN_HANDLER, Identifier.of("minebridge", "transaction"), 
            new net.fabricmc.fabric.api.screenhandler.v1.ExtendedScreenHandlerType<>(
                (syncId, inv, data) -> null, // No se usa en el servidor
                TransactionScreenDataPayload.CODEC
            ));

        // Receptores de Red (Módulo Marketplace)

        net.fabricmc.fabric.api.networking.v1.ServerPlayNetworking.registerGlobalReceiver(OpenCreationMenuPayload.ID, (payload, context) -> {
            context.server().execute(() -> MarketplaceManager.openCreationMenu(context.player()));
        });

        net.fabricmc.fabric.api.networking.v1.ServerPlayNetworking.registerGlobalReceiver(OpenTransactionMenuPayload.ID, (payload, context) -> {
            context.server().execute(() -> MarketplaceManager.openTransactionMenu(context.player(), payload.tradeId()));
        });

        net.fabricmc.fabric.api.networking.v1.ServerPlayNetworking.registerGlobalReceiver(CompleteTradePayload.ID, (payload, context) -> {
            context.server().execute(() -> MarketplaceManager.completeTradeOnServer(context.player(), payload.tradeId()));
        });

        net.fabricmc.fabric.api.networking.v1.ServerPlayNetworking.registerGlobalReceiver(PublishTradePayload.ID, (payload, context) -> {
            context.server().execute(() -> MarketplaceManager.handlePublishTrade(context.player(), payload.title()));
        });

        net.fabricmc.fabric.api.networking.v1.ServerPlayNetworking.registerGlobalReceiver(CancelTradePayload.ID, (payload, context) -> {
            context.server().execute(() -> MarketplaceManager.deleteTrade(context.player(), payload.tradeId()));
        });
    }
}
