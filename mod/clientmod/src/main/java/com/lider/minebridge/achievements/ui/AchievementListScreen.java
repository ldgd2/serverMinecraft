package com.lider.minebridge.achievements.ui;

import com.google.gson.JsonArray;
import com.google.gson.JsonObject;
import net.minecraft.client.gui.DrawContext;
import net.minecraft.client.gui.screen.Screen;
import net.minecraft.client.gui.widget.ButtonWidget;
import net.minecraft.text.Text;

import java.util.ArrayList;
import java.util.List;

public class AchievementListScreen extends Screen {
    private JsonArray data = new JsonArray();
    private boolean loading = true;
    private static final int PANEL_WIDTH = 280;
    private static final int PANEL_HEIGHT = 200;

    public AchievementListScreen() {
        super(Text.of("§e§lMIS LOGROS"));
    }

    public AchievementListScreen(JsonArray data) {
        super(Text.of("§e§lMIS LOGROS"));
        this.data = data;
        this.loading = false;
    }

    @Override
    protected void init() {
        super.init();
        int centerX = this.width / 2;
        int centerY = this.height / 2;

        if (loading) {
            String uuid = net.minecraft.client.MinecraftClient.getInstance().getSession().getUuidOrNull().toString();
            com.lider.minebridge.networking.AchievementClient.getAchievements(uuid).thenAccept(res -> {
                this.data = res;
                this.loading = false;
            }).exceptionally(ex -> {
                this.loading = false;
                return null;
            });
        }

        this.addDrawableChild(ButtonWidget.builder(Text.of("§cRegresar"), button -> {
            net.minecraft.client.MinecraftClient.getInstance().setScreen(new com.lider.minebridge.client.ui.MainLauncherScreen());
        }).dimensions(centerX - 40, centerY + 80, 80, 20).build());
    }

    @Override
    public void renderBackground(DrawContext context, int mouseX, int mouseY, float delta) {
        com.lider.minebridge.ui.framework.UIBackgrounds.renderStandard(context, this.width, this.height);
    }

    @Override
    public void render(DrawContext context, int mouseX, int mouseY, float delta) {
        super.render(context, mouseX, mouseY, delta);
        int centerX = this.width / 2;
        int centerY = this.height / 2;
        int x1 = centerX - (PANEL_WIDTH / 2);
        int y1 = centerY - (PANEL_HEIGHT / 2);
        int x2 = centerX + (PANEL_WIDTH / 2);
        int y2 = centerY + (PANEL_HEIGHT / 2);

        // Fondo Premium Dark
        context.fill(x1 - 2, y1 - 2, x2 + 2, y2 + 2, 0xFFFFD700); 
        context.fill(x1, y1, x2, y2, 0xFF151515);
        context.fill(x1, y1, x2, y1 + 25, 0xFF2A2A2A);
        context.drawCenteredTextWithShadow(this.textRenderer, this.title, centerX, y1 + 8, 0xFFFFFF);

        // Dibujar lista de logros
        if (loading) {
            context.drawCenteredTextWithShadow(this.textRenderer, "§eCargando logros...", centerX, centerY, 0xFFFFFF);
        } else if (data == null || data.size() == 0) {
            context.drawCenteredTextWithShadow(this.textRenderer, "§7No tienes logros aún...", centerX, centerY, 0xAAAAAA);
        } else {
            for (int i = 0; i < Math.min(data.size(), 6); i++) {
                JsonObject ach = data.get(i).getAsJsonObject();
                String title = ach.get("title").getAsString();
                String date = ach.get("unlocked_at").getAsString().split("T")[0];
                
                int rowY = y1 + 35 + (i * 22);
                context.fill(x1 + 10, rowY, x2 - 10, rowY + 20, 0xFF252525);
                context.drawText(this.textRenderer, "§e★ " + title, x1 + 15, rowY + 6, 0xFFFFFF, false);
                context.drawText(this.textRenderer, "§7" + date, x2 - 80, rowY + 6, 0xAAAAAA, false);
            }
        }

        super.render(context, mouseX, mouseY, delta);
    }

    @Override
    public boolean shouldPause() { return false; }
}
