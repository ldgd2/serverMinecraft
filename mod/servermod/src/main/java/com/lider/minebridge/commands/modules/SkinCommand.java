package com.lider.minebridge.commands.modules;

import com.mojang.brigadier.CommandDispatcher;
import com.lider.minebridge.networking.SkinClient;
import net.minecraft.command.argument.EntityArgumentType;
import net.minecraft.server.command.CommandManager;
import net.minecraft.server.command.ServerCommandSource;
import net.minecraft.server.network.ServerPlayerEntity;
import net.minecraft.text.Text;

import java.util.Collection;

public class SkinCommand {

    public static void register(CommandDispatcher<ServerCommandSource> dispatcher) {
        // Global direct alias: /skin refresh (for all players)
        dispatcher.register(CommandManager.literal("skin")
            .then(CommandManager.literal("refresh")
                .executes(context -> refreshSelfSkin(context.getSource()))
                .then(CommandManager.argument("targets", EntityArgumentType.players())
                    .requires(source -> source.hasPermissionLevel(4))
                    .executes(context -> refreshOtherSkins(context.getSource(), EntityArgumentType.getPlayers(context, "targets")))
                )
            )
        );
    }

    private static int refreshSelfSkin(ServerCommandSource source) {
        try {
            ServerPlayerEntity player = source.getPlayerOrThrow();
            source.sendFeedback(() -> Text.literal("§e[MineBridge] Solicitando actualización de skin..."), false);
            SkinClient.syncSkin(player, () -> {
                source.sendFeedback(() -> Text.literal("§a[MineBridge] ✅ Tu skin ha sido actualizada."), false);
            });
            return 1;
        } catch (Exception e) {
            source.sendError(Text.literal("§c[MineBridge] Solo los jugadores pueden usar este comando."));
            return 0;
        }
    }

    private static int refreshOtherSkins(ServerCommandSource source, Collection<ServerPlayerEntity> targets) {
        source.sendFeedback(() -> Text.literal("§e[MineBridge] Actualizando skins para " + targets.size() + " jugadores..."), true);
        for (ServerPlayerEntity player : targets) {
            SkinClient.syncSkin(player);
        }
        return targets.size();
    }
}
