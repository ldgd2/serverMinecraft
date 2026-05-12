package com.lider.minebridge.ui.framework;

import com.lider.minebridge.ui.framework.core.UIConstants;
import net.minecraft.client.gui.DrawContext;

/**
 * Módulo Global de Renderizado: Proporciona funciones centralizadas para fondos, overlays y paneles.
 */
public class UIBackgrounds {
    
    // --- Overlays Predefinidos (Fondos Rápidos) ---

    /**
     * Fondo Negro Total (Sólido).
     */
    public static void renderBlack(DrawContext context, int width, int height) {
        renderCustom(context, 0, 0, width, height, 0xFF000000);
    }

    /**
     * Fondo Oscuro Estándar (Translúcido).
     */
    public static void renderDark(DrawContext context, int width, int height) {
        renderCustom(context, 0, 0, width, height, 0xAA000000);
    }

    /**
     * Fondo Claro (Translúcido).
     */
    public static void renderLight(DrawContext context, int width, int height) {
        renderCustom(context, 0, 0, width, height, 0x44FFFFFF);
    }

    /**
     * Fondo Estilo Cristal (Glassmorphism).
     */
    public static void renderGlass(DrawContext context, int width, int height) {
        renderCustom(context, 0, 0, width, height, 0x33FFFFFF);
    }

    /**
     * Fondo Rojo (Peligro/Reinicios).
     */
    public static void renderWarning(DrawContext context, int width, int height) {
        renderCustom(context, 0, 0, width, height, 0x44FF0000);
    }

    /**
     * Fondo Verde (Éxito/Confirmación).
     */
    public static void renderSuccess(DrawContext context, int width, int height) {
        renderCustom(context, 0, 0, width, height, 0x4400FF00);
    }

    /**
     * Renderizado Estándar (Alias de Dark).
     */
    public static void renderStandard(DrawContext context, int width, int height) {
        renderDark(context, width, height);
    }

    // --- Motor de Renderizado Flexible ---

    /**
     * Renderizado Flexible: Permite definir posición, tamaño y color del fondo a gusto.
     */
    public static void renderCustom(DrawContext context, int x, int y, int width, int height, int color) {
        context.fill(x, y, x + width, y + height, color);
    }

    // --- Paneles (Contenedores con bordes) ---

    /**
     * Dibuja un panel con la estética estándar del framework.
     */
    public static void drawPanel(DrawContext context, int x, int y, int width, int height) {
        drawPanelCustom(context, x, y, width, height, UIConstants.PANEL_BG, UIConstants.PANEL_LIGHT, UIConstants.PANEL_DARK);
    }

    /**
     * Dibuja un panel con colores e iluminación totalmente personalizados.
     */
    public static void drawPanelCustom(DrawContext context, int x, int y, int width, int height, int bgColor, int lightColor, int darkColor) {
        context.fill(x, y, x + width, y + height, bgColor);
        context.fill(x, y, x + width, y + 1, lightColor);
        context.fill(x, y, x + 1, y + height, lightColor);
        context.fill(x, y + height - 1, x + width, y + height, darkColor);
        context.fill(x + width - 1, y, x + width, y + height, darkColor);
    }

    /**
     * Dibuja un panel hundido (Inset).
     */
    public static void drawInset(DrawContext context, int x, int y, int width, int height) {
        drawPanelCustom(context, x, y, width, height, 0xFF000000, UIConstants.PANEL_DARK, UIConstants.PANEL_LIGHT);
    }

    /**
     * Alias para drawInset utilizado por componentes de contenedor.
     */
    public static void drawInsetPanel(DrawContext context, int x, int y, int width, int height) {
        drawInset(context, x, y, width, height);
    }

    // --- Compatibilidad ---
    
    @Deprecated
    public static void renderStandardBackground(DrawContext context, int width, int height) {
        renderStandard(context, width, height);
    }

    @Deprecated
    public static void renderCustomBackground(DrawContext context, int width, int height, int color) {
        renderCustom(context, 0, 0, width, height, color);
    }
}
