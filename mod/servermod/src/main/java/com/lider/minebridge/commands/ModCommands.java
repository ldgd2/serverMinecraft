package com.lider.minebridge.commands;

import com.lider.minebridge.commands.modules.*;
import net.fabricmc.fabric.api.command.v2.CommandRegistrationCallback;

public class ModCommands {
    
    public static void init() {
        CommandRegistrationCallback.EVENT.register((dispatcher, registryAccess, environment) -> {
            
            // Register Modular Commands
            AdminCommand.register(dispatcher);
            TeleportCommand.register(dispatcher);
            SkinCommand.register(dispatcher);
            MarketplaceCommand.register(dispatcher, registryAccess);
            
        });
    }
}
