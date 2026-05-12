package com.lider.minebridge.client.gui;

import com.lider.minebridge.ui.framework.components.AlertComponent;
import com.lider.minebridge.ui.framework.components.NotificationComponent;
import net.fabricmc.fabric.api.client.rendering.v1.HudRenderCallback;
import net.minecraft.client.MinecraftClient;
import net.minecraft.client.gui.DrawContext;
import net.minecraft.util.math.MathHelper;

import java.util.ArrayList;
import java.util.List;

public class CustomOverlayHud {

    private static class ActiveAlert {
        String title;
        String desc;
        int color;
        int remainingTicks;
        int maxTicks;

        ActiveAlert(String title, String desc, int color, int seconds) {
            this.title = title;
            this.desc = desc;
            this.color = color;
            this.maxTicks = seconds * 20;
            this.remainingTicks = this.maxTicks;
        }
    }

    private static class ActiveNotification {
        String message;
        String type;
        int remainingTicks;
        int maxTicks;

        ActiveNotification(String message, String type, int seconds) {
            this.message = message;
            this.type = type;
            this.maxTicks = seconds * 20;
            this.remainingTicks = this.maxTicks;
        }
    }

    private static final List<ActiveAlert> activeAlerts = new ArrayList<>();
    private static final List<ActiveNotification> activeNotifications = new ArrayList<>();

    public static void showAnnouncement(String title, String desc, int color, int seconds) {
        activeAlerts.add(new ActiveAlert(title, desc, color, seconds));
    }

    public static void showNotification(String message, String type, int seconds) {
        activeNotifications.add(new ActiveNotification(message, type, seconds));
    }

    public static void tick() {
        activeAlerts.removeIf(a -> {
            a.remainingTicks--;
            return a.remainingTicks <= 0;
        });
        activeNotifications.removeIf(n -> {
            n.remainingTicks--;
            return n.remainingTicks <= 0;
        });
    }

    public static void register() {
        HudRenderCallback.EVENT.register((drawContext, tickCounter) -> {
            MinecraftClient client = MinecraftClient.getInstance();
            if (client.player == null) return;

            int screenWidth = client.getWindow().getScaledWidth();
            int screenHeight = client.getWindow().getScaledHeight();

            // 1. Renderizar Alertas (Centradas)
            if (!activeAlerts.isEmpty()) {
                ActiveAlert alert = activeAlerts.get(0); // Mostrar solo la más reciente o primera
                float alpha = 1.0f;
                if (alert.remainingTicks < 20) alpha = alert.remainingTicks / 20.0f;
                if (alert.maxTicks - alert.remainingTicks < 10) alpha = (alert.maxTicks - alert.remainingTicks) / 10.0f;

                int width = 200;
                int x = (screenWidth - width) / 2;
                int y = screenHeight / 4;

                // Simple fade logic (Minecraft doesn't support easy alpha for everything without GL calls, 
                // so we just skip rendering if very low or use colored text)
                if (alpha > 0.1f) {
                    AlertComponent.draw(drawContext, client.textRenderer, AlertComponent.AlertType.INFO, alert.title, alert.desc, x, y, width);
                }
            }

            // 2. Renderizar Notificaciones (Esquina Superior Derecha)
            int notY = 10;
            for (ActiveNotification note : activeNotifications) {
                int notWidth = client.textRenderer.getWidth(note.message) + 40;
                int notX = screenWidth - notWidth - 10;
                
                NotificationComponent.draw(drawContext, client.textRenderer, note.message, notX, notY);
                notY += 30; // Spacing
            }
        });
    }
}
