"""
Minecraft Launcher - Theme & Asset Path Helpers
"""
import os
import tkinter.font as tkfont

import sys

# ── Resource path helper for PyInstaller ──────────────────────────────────────
def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

    # If the relative path starts with 'ui/', we adjust it since _UI_DIR is already inside 'ui'
    if relative_path.startswith("ui/"):
        relative_path = relative_path[3:]
        
    return os.path.join(base_path, "minecraftLauncher", "ui", relative_path)

# Base directory for the UI package
_UI_DIR = os.path.dirname(os.path.abspath(__file__))

# Re-calculate directories using resource_path
_GUI_DIR = resource_path("gui")
_ASSETS_DIR = resource_path("assets")

def _a(*parts):
    return os.path.join(_ASSETS_DIR, *parts)

def _g(*parts):
    return os.path.join(_GUI_DIR, *parts)

# ── Color Palette ──────────────────────────────────────────────────────────────
class Colors:
    # Backgrounds
    DIRT_DARK     = "#1a1008"
    DARK          = "#1c1c1c"
    PANEL         = "#8b8b8b"   # Minecraft gray stone
    PANEL_LIGHT   = "#c6c6c6"
    PANEL_DARK    = "#373737"
    PANEL_BORDER  = "#555555"

    # Minecraft button shades (from real button.png palette)
    BTN_TOP       = "#9d9d9d"
    BTN_SHADOW    = "#3f3f3f"
    BTN_HOVER_TOP = "#c0c0ff"   # blue-tinted highlight
    BTN_DISABLED  = "#6d6d6d"

    # Text
    WHITE         = "#ffffff"
    YELLOW        = "#ffff55"   # Minecraft button hover text
    GRAY_TEXT     = "#aaaaaa"
    DARK_TEXT     = "#3f3f3f"
    SHADOW        = "#3f3f3f"

    # Badges
    PREMIUM_GREEN  = "#55ff55"
    NOPREMIUM_RED  = "#ff5555"

    # Accents
    ACCENT        = "#5b9bd5"
    GREEN_PLAY    = "#3c8527"
    GREEN_PLAY_HV = "#4aaa32"

    # Overlay
    BLACK_OVERLAY = "#000000cc"
    DARK_BUTTON   = "#222222"

# ── Asset Paths ────────────────────────────────────────────────────────────────
class Assets:
    FONT_MC     = _a("fonts", "minecraft", "Minecraft.ttf")
    BG          = _a("bg.png")

    # Title / logo
    TITLE_LOGO  = _g("title", "minecraft.png")
    TITLE_EDITION = _g("title", "edition.png")

    # Panorama frames
    PANORAMAS   = [_g("title", "background", f"panorama_{i}.png") for i in range(6)]

    # Widget sprites
    BTN         = _g("sprites", "widget", "button.png")
    BTN_HOV     = _g("sprites", "widget", "button_highlighted.png")
    BTN_DIS     = _g("sprites", "widget", "button_disabled.png")
    SLIDER      = _g("sprites", "widget", "slider.png")
    SLIDER_H    = _g("sprites", "widget", "slider_highlighted.png")
    SLIDER_HANDLE    = _g("sprites", "widget", "slider_handle.png")
    SLIDER_HANDLE_H  = _g("sprites", "widget", "slider_handle_highlighted.png")
    TEXT_FIELD  = _g("sprites", "widget", "text_field.png")
    TEXT_FIELD_H = _g("sprites", "widget", "text_field_highlighted.png")
    CHECKBOX    = _g("sprites", "widget", "checkbox.png")
    CHECKBOX_SEL = _g("sprites", "widget", "checkbox_selected.png")
    CHECKBOX_SEL_H = _g("sprites", "widget", "checkbox_selected_highlighted.png")
    MENU_BG     = _g("menu_background.png")
    MENU_LIST_BG = _g("menu_list_background.png")

    # Auth SVG icon
    ICON_MICROSOFT = _a("icons", "auth", "microsoft.svg")

    # GUI sprite icons (from gui/ — pixel art, no external deps)
    ICON_PLAY    = _g("sprites", "world_list", "join.png")
    ICON_WARN    = _g("sprites", "world_list", "warning.png")
    ICON_SEARCH  = _g("sprites", "icon", "search.png")
    ICON_SETTINGS = _g("sprites", "icon", "accessibility.png")

    # Separator
    HEADER_SEP  = _g("header_separator.png")

    # Advancement Frames
    FRAME_TASK    = _g("sprites", "advancements", "task_frame_obtained.png")
    FRAME_CHALLENGE = _g("sprites", "advancements", "challenge_frame_obtained.png")
    FRAME_GOAL    = _g("sprites", "advancements", "goal_frame_obtained.png")
    
    # Stats Icons
    ICON_BLOCKS   = _g("sprites", "statistics", "block_mined.png")
    ICON_ITEMS    = _g("sprites", "statistics", "item_used.png")
    ICON_KILLS    = _g("sprites", "statistics", "item_broken.png")


# ── Font Loader ────────────────────────────────────────────────────────────────
_font_name = "Minecraft"
_font_loaded = False

def load_minecraft_font():
    """Register the Minecraft TTF font with tkinter. Call once at startup."""
    global _font_loaded
    if _font_loaded:
        return _font_name
    font_path = Assets.FONT_MC
    if os.path.exists(font_path):
        try:
            # Load via pyglet or tkinter font.families trick
            import tkinter as tk
            _root_ref = tk._default_root
            if _root_ref:
                _root_ref.tk.call("font", "create", _font_name, "-family", _font_name)
            # Also try via PIL/ImageFont to validate
            _font_loaded = True
            return _font_name
        except Exception:
            pass
    return "Courier"  # Fallback monospace

def mc_font(size: int = 12, bold: bool = False) -> tuple:
    """Return a tkinter font tuple using the Minecraft font."""
    return (_font_name, size, "bold" if bold else "normal")
