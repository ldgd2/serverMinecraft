package com.lider.minebridge.marketplace;

import com.lider.minebridge.marketplace.handler.MarketplaceCreationScreenHandler;
import com.lider.minebridge.marketplace.handler.MarketplaceTransactionScreenHandler;
import com.lider.minebridge.marketplace.networking.MarketplaceDataPayload;
import com.lider.minebridge.marketplace.networking.TransactionScreenDataPayload;
import com.lider.minebridge.marketplace.ui.MarketplaceCreationScreen;
import com.lider.minebridge.marketplace.ui.MarketplaceGlobalScreen;
import com.lider.minebridge.marketplace.ui.MarketplaceTransactionScreen;
import net.fabricmc.fabric.api.client.networking.v1.ClientPlayNetworking;
import net.minecraft.client.gui.screen.ingame.HandledScreens;
import net.minecraft.item.ItemStack;
import net.minecraft.registry.Registries;
import net.minecraft.registry.Registry;
import net.minecraft.screen.ScreenHandlerType;
import net.minecraft.util.Identifier;
import java.util.ArrayList;
import java.util.List;

/**
 * Módulo de Marketplace (Cliente): Registra pantallas y tipos de handlers.
 */
public class MarketplaceModule {
    
    public static ScreenHandlerType<MarketplaceCreationScreenHandler> CREATION_HANDLER;
    public static ScreenHandlerType<MarketplaceTransactionScreenHandler> TRANSACTION_HANDLER;

    public static void initClient() {
        // 1. Registro de los Tipos de Handler (Deben coincidir con el servidor)
        CREATION_HANDLER = Registry.register(Registries.SCREEN_HANDLER, Identifier.of("minebridge", "creation"), 
            new ScreenHandlerType<>(MarketplaceCreationScreenHandler::new, net.minecraft.resource.featuretoggle.FeatureSet.empty()));

        TRANSACTION_HANDLER = Registry.register(Registries.SCREEN_HANDLER, Identifier.of("minebridge", "transaction"), 
            new net.fabricmc.fabric.api.screenhandler.v1.ExtendedScreenHandlerType<>(
                (syncId, inventory, data) -> {
                    List<ItemStack> requirements = new ArrayList<>();
                    com.google.gson.JsonArray array = com.google.gson.JsonParser.parseString(data.requirementsJson()).getAsJsonArray();
                    for (int i = 0; i < array.size(); i++) {
                        com.google.gson.JsonObject obj = array.get(i).getAsJsonObject();
                        requirements.add(new ItemStack(Registries.ITEM.get(Identifier.of(obj.get("id").getAsString())), obj.get("count").getAsInt()));
                    }
                    return new MarketplaceTransactionScreenHandler(syncId, inventory, data.tradeId(), requirements);
                },
                TransactionScreenDataPayload.CODEC
            ));

        // 2. Registro de Pantallas
        HandledScreens.register(CREATION_HANDLER, MarketplaceCreationScreen::new);
        HandledScreens.register(TRANSACTION_HANDLER, MarketplaceTransactionScreen::new);

        // 3. Receptor de datos para el Mercado Global
        ClientPlayNetworking.registerGlobalReceiver(MarketplaceDataPayload.ID, (payload, context) -> {
            // Procesamos el JSON en segundo plano (Núcleo aislado)
            com.lider.minebridge.core.MineCore.Processor.run(() -> {
                com.google.gson.JsonArray trades = com.google.gson.JsonParser.parseString(payload.tradesJson()).getAsJsonArray();
                // Una vez procesado, abrimos la pantalla en el hilo de renderizado
                com.lider.minebridge.core.MineCore.sync(() -> {
                    context.client().setScreen(new com.lider.minebridge.marketplace.ui.MarketplaceGlobalScreen(trades));
                });
            });
        });
    }
}
