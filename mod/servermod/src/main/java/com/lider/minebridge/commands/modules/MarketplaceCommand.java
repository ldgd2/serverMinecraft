package com.lider.minebridge.commands.modules;

import com.mojang.brigadier.CommandDispatcher;
import com.mojang.brigadier.arguments.IntegerArgumentType;
import com.google.gson.JsonObject;
import com.lider.minebridge.networking.TradeClient;
import net.minecraft.command.argument.ItemStackArgument;
import net.minecraft.command.argument.ItemStackArgumentType;
import net.minecraft.item.ItemStack;
import net.minecraft.registry.Registries;
import net.minecraft.server.command.CommandManager;
import net.minecraft.server.command.ServerCommandSource;
import net.minecraft.server.network.ServerPlayerEntity;
import net.minecraft.text.Text;
import net.minecraft.command.CommandRegistryAccess;

public class MarketplaceCommand {

    public static void register(CommandDispatcher<ServerCommandSource> dispatcher, CommandRegistryAccess registryAccess) {
        // Marketplace: /vender <count> <item>
        dispatcher.register(CommandManager.literal("vender")
            .then(CommandManager.argument("cantidad", IntegerArgumentType.integer(1))
                .then(CommandManager.argument("item", ItemStackArgumentType.itemStack(registryAccess))
                    .executes(context -> publishItem(context.getSource(), 
                        IntegerArgumentType.getInteger(context, "cantidad"),
                        ItemStackArgumentType.getItemStackArgument(context, "item")))
                )
            )
        );
    }

    private static int publishItem(ServerCommandSource source, int count, ItemStackArgument itemReq) {
        try {
            ServerPlayerEntity player = source.getPlayerOrThrow();
            ItemStack hand = player.getMainHandStack();
            
            if (hand.isEmpty()) {
                source.sendError(Text.of("§cDebes tener un item en la mano para venderlo."));
                return 0;
            }

            JsonObject selling = new JsonObject();
            selling.addProperty("id", Registries.ITEM.getId(hand.getItem()).toString());
            selling.addProperty("count", hand.getCount());

            JsonObject asking = new JsonObject();
            asking.addProperty("id", Registries.ITEM.getId(itemReq.getItem()).toString());
            asking.addProperty("count", count);

            TradeClient.publishTrade(
                player.getUuidAsString(),
                player.getName().getString(),
                "Oferta de " + hand.getName().getString(),
                selling, asking
            );
            source.sendFeedback(() -> Text.of("§a¡Oferta publicada en el Marketplace!"), true);
            
            return 1;
        } catch (Exception e) {
            source.sendError(Text.of("§cError al publicar la oferta."));
            return 0;
        }
    }
}
