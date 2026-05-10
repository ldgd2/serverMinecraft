package com.lider.minebridge.commands.modules;

import com.mojang.brigadier.CommandDispatcher;
import net.minecraft.command.argument.EntityArgumentType;
import net.minecraft.command.argument.Vec3ArgumentType;
import net.minecraft.server.command.CommandManager;
import net.minecraft.server.command.ServerCommandSource;
import net.minecraft.server.network.ServerPlayerEntity;
import net.minecraft.text.Text;
import net.minecraft.util.math.Vec3d;

public class TeleportCommand {

    public static void register(CommandDispatcher<ServerCommandSource> dispatcher) {
        // Teleport Command: /t <coords> or /t <player>
        dispatcher.register(CommandManager.literal("t")
            // Subcommand: /t <x> <y> <z>
            .then(CommandManager.argument("posicion", Vec3ArgumentType.vec3())
                .executes(context -> teleportToCoords(context.getSource(), Vec3ArgumentType.getVec3(context, "posicion")))
            )
            // Subcommand: /t <player>
            .then(CommandManager.argument("jugador", EntityArgumentType.player())
                .executes(context -> teleportToPlayer(context.getSource(), EntityArgumentType.getPlayer(context, "jugador")))
            )
        );
    }

    private static int teleportToCoords(ServerCommandSource source, Vec3d pos) {
        try {
            ServerPlayerEntity player = source.getPlayerOrThrow();
            int cost = 15; // Costo por coordenadas

            if (player.experienceLevel < cost) {
                source.sendError(Text.of("§cNo tienes suficiente experiencia. Necesitas " + cost + " niveles."));
                return 0;
            }

            player.addExperienceLevels(-cost);
            player.teleport(source.getWorld(), pos.x, pos.y, pos.z, player.getYaw(), player.getPitch());
            
            source.sendFeedback(() -> Text.of("§aTeletransportado a las coordenadas. §e-" + cost + " niveles."), false);
            return 1;
        } catch (Exception e) {
            source.sendError(Text.of("§cError al teletransportar."));
            return 0;
        }
    }

    private static int teleportToPlayer(ServerCommandSource source, ServerPlayerEntity target) {
        try {
            ServerPlayerEntity player = source.getPlayerOrThrow();
            int cost = 5; // Costo por jugador

            if (player.getUuid().equals(target.getUuid())) {
                source.sendError(Text.of("§cYa estás en tu posición."));
                return 0;
            }

            if (player.experienceLevel < cost) {
                source.sendError(Text.of("§cNo tienes suficiente experiencia. Necesitas " + cost + " niveles."));
                return 0;
            }

            player.addExperienceLevels(-cost);
            player.teleport(target.getServerWorld(), target.getX(), target.getY(), target.getZ(), player.getYaw(), player.getPitch());
            
            source.sendFeedback(() -> Text.of("§aTeletransportado a " + target.getName().getString() + ". §e-" + cost + " niveles."), false);
            return 1;
        } catch (Exception e) {
            source.sendError(Text.of("§cError al teletransportar."));
            return 0;
        }
    }
}
