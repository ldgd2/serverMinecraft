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
    private double scrollAmount = 0;
    private static final int ITEM_HEIGHT = 40;
    private static final int ITEMS_PER_ROW = 2;

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
        }).dimensions(centerX - 40, centerY + 85, 80, 18).build());
    }

    @Override
    public boolean mouseScrolled(double mouseX, double mouseY, double horizontalAmount, double verticalAmount) {
        this.scrollAmount = Math.max(0, this.scrollAmount - (verticalAmount * 15));
        return true;
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

        // Área de recorte para scrolling
        int listY1 = y1 + 28;
        int listY2 = y2 - 25;
        
        context.enableScissor(x1 + 5, listY1, x2 - 5, listY2);

        if (loading) {
            context.drawCenteredTextWithShadow(this.textRenderer, "§eCargando logros...", centerX, centerY, 0xFFFFFF);
        } else if (data == null || data.size() == 0) {
            context.drawCenteredTextWithShadow(this.textRenderer, "§7No tienes logros aún...", centerX, centerY, 0xAAAAAA);
        } else {
            int gridX = x1 + 8;
            int colWidth = (PANEL_WIDTH - 20) / ITEMS_PER_ROW;
            
            for (int i = 0; i < data.size(); i++) {
                int row = i / ITEMS_PER_ROW;
                int col = i % ITEMS_PER_ROW;
                
                int itemX = gridX + (col * colWidth);
                int itemY = (int) (listY1 + 5 + (row * (ITEM_HEIGHT + 5)) - scrollAmount);

                // Solo dibujar si está visible (optimización manual básica)
                if (itemY + ITEM_HEIGHT > listY1 && itemY < listY2) {
                    JsonObject ach = data.get(i).getAsJsonObject();
                    String title = ach.has("title") ? ach.get("title").getAsString() : "Logro";
                    String date = ach.has("unlocked_at") ? ach.get("unlocked_at").getAsString().split("T")[0] : "";

                    // Card de logro
                    context.fill(itemX, itemY, itemX + colWidth - 4, itemY + ITEM_HEIGHT, 0xFF252525);
                    context.fill(itemX, itemY, itemX + 2, itemY + ITEM_HEIGHT, 0xFFFFD700); // Borde dorado lateral
                    
                    context.drawText(this.textRenderer, "§e" + title, itemX + 6, itemY + 6, 0xFFFFFF, false);
                    context.drawText(this.textRenderer, "§7" + date, itemX + 6, itemY + 22, 0xAAAAAA, false);
                }
            }
        }
        
        context.disableScissor();

        super.render(context, mouseX, mouseY, delta);
    }

    @Override
    public boolean shouldPause() { return false; }
}
