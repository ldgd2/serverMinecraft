package com.lider.minebridge.client;

import net.minecraft.client.gui.DrawContext;
import net.minecraft.client.toast.Toast;
import net.minecraft.client.toast.ToastManager;
import net.minecraft.text.Text;
import net.minecraft.util.Identifier;

public class AchievementToast implements Toast {
    private static final Identifier TEXTURE = Identifier.of("minecraft", "toast/advancement");
    private final Text title;
    private final Text description;
    private final int colorTitle;
    private long startTime;
    private boolean justUpdated;

    public AchievementToast(Text title, Text description, int colorTitle) {
        this.title = title;
        this.description = description;
        this.colorTitle = colorTitle;
    }

    @Override
    public Visibility draw(DrawContext context, ToastManager manager, long startTime) {
        if (this.justUpdated) {
            this.startTime = startTime;
            this.justUpdated = false;
        }

        context.drawGuiTexture(TEXTURE, 0, 0, this.getWidth(), this.getHeight());

        int colorDesc = 0xFFFFFF; // White

        context.drawText(manager.getClient().textRenderer, this.title, 30, 7, this.colorTitle, false);
        context.drawText(manager.getClient().textRenderer, this.description, 30, 18, colorDesc, false);

        return startTime - this.startTime >= 5000L ? Visibility.HIDE : Visibility.SHOW;
    }
}
