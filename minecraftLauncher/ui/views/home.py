"""
Minecraft Launcher - Home View
Main launcher screen: player info, version selector, play button, nav tiles.
"""
import tkinter as tk
import threading
import os
from PIL import Image, ImageTk

from ui.theme import Colors, Assets, mc_font
from ui.widgets import (
    MinecraftButton, MinecraftLabel, MinecraftPanel,
    SkinHead, PanoramaBackground, SectionHeader
)
from config.manager import config
from core.versions import get_installed_versions
from core.launcher import launch_minecraft, filter_versions
from core.info import VERSION
from ui.views.profile import PlayerProfilePanel


LOADER_TYPES = ["Vanilla", "Fabric", "Forge"]


def _load_gui_sprite(path, size):
    if path and os.path.exists(path):
        try:
            img = Image.open(path).convert("RGBA")
            return img.resize(size, Image.NEAREST)
        except Exception:
            pass
    return None


class HomeView(tk.Frame):
    """Main Launcher home screen."""

    def __init__(self, master, app=None, **kwargs):
        super().__init__(master, bg=Colors.DARK, **kwargs)
        self.app = app
        self._launching = False

        ico_size = (32, 32)
        self._icon_play    = _load_gui_sprite(Assets.ICON_PLAY,  ico_size)
        self._icon_warn    = _load_gui_sprite(Assets.ICON_WARN,  ico_size)
        self._icon_search  = _load_gui_sprite(Assets.ICON_SEARCH, ico_size)

        self._build_ui()
        self._update_loader_tabs()
        self._load_versions()

    # ── Build ──────────────────────────────────────────────────────────────────

    def _build_ui(self):
        # 1. Background panorama
        self.panorama = PanoramaBackground(self, bg=Colors.DARK)
        self.panorama.place(relx=0, rely=0, relwidth=1, relheight=1)

        # 2. Main Logo
        mc_logo_path = Assets.TITLE_LOGO
        if os.path.exists(mc_logo_path):
            img = Image.open(mc_logo_path).convert("RGBA")
            w = 548
            h = int(w * img.height / img.width)
            img = img.resize((w, h), Image.NEAREST)
            self._tk_header_logo = ImageTk.PhotoImage(img)
            
            self.panorama.create_image(
                self.winfo_screenwidth()//2 if self.winfo_screenwidth() > 100 else 600, 
                100, image=self._tk_header_logo, anchor="center", tags="mc_logo")
            
            def on_resize_logo(e):
                self.panorama.coords("mc_logo", e.width // 2, max(80, int(e.height * 0.15)))
            self.panorama.bind("<Configure>", on_resize_logo, add="+")

        # 3. Center buttons
        btn_w = 400
        btn_h = 40
        base_y = 0.40
        
        self._play_btn = MinecraftButton(
            self.panorama, text="Jugar",
            width=btn_w, height=btn_h, font_size=12,
            command=self._play, bg=Colors.DARK
        )
        self._play_btn.place(relx=0.5, rely=base_y, anchor="n")

        self._skins_btn = MinecraftButton(
            self.panorama, text="Skins",
            width=btn_w, height=btn_h, font_size=12,
            command=self._go_skins, bg=Colors.DARK
        )
        self._skins_btn.place(relx=0.5, rely=base_y + 0.08, anchor="n")

        self._versions_btn = MinecraftButton(
            self.panorama, text="Versiones (Gestor)",
            width=btn_w, height=btn_h, font_size=12,
            command=self._go_downloads, bg=Colors.DARK
        )
        self._versions_btn.place(relx=0.5, rely=base_y + 0.16, anchor="n")

        half_w = (btn_w - 10) // 2

        # ── Version Label (Bottom Right) ──────────────────────────────────────
        self.version_lbl = tk.Label(self, text=f"v{VERSION}", fg=Colors.GRAY_TEXT,
                                    bg="#1a1a1a", font=mc_font(10))
        self.version_lbl.place(relx=1.0, rely=1.0, x=-10, y=-10, anchor="se")
        
        self._opts_btn = MinecraftButton(
            self.panorama, text="Opciones...",
            width=half_w, height=btn_h, font_size=12,
            command=self._go_settings, bg=Colors.DARK
        )
        self._opts_btn.place(relx=0.5, rely=base_y + 0.28, x=-(half_w//2 + 5), anchor="n")

        self._quit_btn = MinecraftButton(
            self.panorama, text="Cerrar sesion",
            width=half_w, height=btn_h, font_size=12,
            command=self._logout, bg=Colors.DARK
        )
        self._quit_btn.place(relx=0.5, rely=base_y + 0.28, x=(half_w//2 + 5), anchor="n")

        # 4. Bottom Left Info (Version & Loader)
        self.info_frame = tk.Frame(self.panorama, bg=Colors.DARK)
        self.info_frame.place(relx=0.02, rely=0.98, anchor="sw")
        
        self._loader_var = tk.StringVar(value=config.get("selected_type") or "Vanilla")
        
        # Container for the loader tabs
        self._loader_tabs_frame = tk.Frame(self.info_frame, bg=Colors.DARK)
        self._loader_tabs_frame.pack(side="left")

        # Dropdown
        self._version_var = tk.StringVar(value="Cargando...")
        self._version_menu = tk.OptionMenu(self.info_frame, self._version_var, "Cargando...", command=self._on_version_selected)
        self._version_menu.config(
            bg=Colors.PANEL_DARK, fg=Colors.WHITE,
            activebackground=Colors.PANEL_BORDER, activeforeground=Colors.YELLOW,
            font=mc_font(10), bd=0, width=24,
            highlightthickness=1, highlightbackground=Colors.PANEL_BORDER,
        )
        self._version_menu["menu"].config(bg=Colors.PANEL_DARK, fg=Colors.WHITE, font=mc_font(10))
        self._version_menu.pack(side="left", padx=(10, 0))

        # User Info
        right_info = tk.Frame(self.panorama, bg=Colors.DARK)
        right_info.place(relx=0.85, rely=0.45, anchor="center")
        
        self._skin_head = SkinHead(right_info, size=96, bg=Colors.DARK)
        self._skin_head.pack(side="top", pady=(0, 10))

        self._header_username = tk.Label(right_info, text=config.get("username") or "Player",
                                          fg=Colors.WHITE, bg=Colors.DARK, font=mc_font(14))
        self._header_username.pack(side="top")

        self._header_badge = tk.Label(right_info, text="", fg=Colors.PREMIUM_GREEN, bg=Colors.DARK, font=mc_font(10))
        self._header_badge.pack(side="top")

        # Profile button under the skin
        tk.Button(right_info, text="👤 Ver Perfil", bd=0,
                  bg=Colors.DARK_BUTTON, fg=Colors.YELLOW,
                  font=mc_font(9), cursor="hand2",
                  command=self._show_profile).pack(side="top", pady=(6, 0))

        self._profile_panel = None
        
        # Log area
        self._log_text = tk.Text(
            self.panorama, height=8, bg="#111111", fg=Colors.GRAY_TEXT,
            font=("Courier", 9), bd=0, state="disabled",
            highlightthickness=1, highlightbackground=Colors.PANEL_BORDER, wrap="word"
        )

    # ── Logic ────────────────────────────────────────────────────────

    def _update_loader_tabs(self):
        """Recreates the loader buttons. Active one has yellow text to indicate selection."""
        for w in self._loader_tabs_frame.winfo_children():
            w.destroy()
            
        current = self._loader_var.get()
        for lt in LOADER_TYPES:
            # We override text color via a tiny trick: since MinecraftButton uses _make_shadow(fill=Colors.WHITE),
            # we don't have direct prop, but we can set the text to yellow.
            # wait, MinecraftButton doesn't support custom inner text color easily. 
            # So I will just add brackets or a custom character to show it's active.
            # Wait, the user specifically asked for "letras en amarillas".
            # Let's see if we can patch MinecraftButton or just use standard buttons here.
            # I will use a standard tk.Label configured like a button if MinecraftButton is inflexible,
            # or just rely on the existing _make_shadow. Note: I will use a custom label for active.
            
            def create_btn(txt=lt):
                is_active = (txt == current)
                color = Colors.YELLOW if is_active else Colors.WHITE
                lbl = tk.Label(self._loader_tabs_frame, text=f" [{txt}] " if is_active else f"  {txt}  ",
                              fg=color, bg=Colors.PANEL_DARK if is_active else Colors.DARK, 
                              font=mc_font(10, bold=is_active), cursor="hand2")
                lbl.bind("<Button-1>", lambda e, t=txt: self._select_loader(t))
                lbl.pack(side="left", padx=2, ipady=4)
            create_btn()

    def _select_loader(self, loader_type: str):
        self._loader_var.set(loader_type)
        config.set("selected_type", loader_type)
        self._update_loader_tabs()
        self._load_versions()

    def _load_versions(self):
        selected_modloader = self._loader_var.get()
        self._version_var.set("Cargando...")
        
        def fetch():
            # Get valid installed versions for this loader
            versions = filter_versions(selected_modloader, None)
            try:
                if self.winfo_exists():
                    self.after(0, lambda: self._update_version_menu(versions))
            except Exception: pass
            
        threading.Thread(target=fetch, daemon=True).start()

    def _update_version_menu(self, versions):
        menu = self._version_menu["menu"]
        menu.delete(0, "end")
        if not versions:
            self._version_var.set("Sin versiones")
            config.set("selected_version", "")
            return
            
        loader = self._loader_var.get()
        # Retrieve the saved version for this SPECIFIC loader, e.g. "selected_version_Fabric"
        saved = config.get(f"selected_version_{loader}") or config.get("selected_version")
        
        first = saved if saved in versions else versions[0]
        self._version_var.set(first)
        self._on_version_selected(first)
        
        for v in versions:
            menu.add_command(label=v, command=lambda val=v: self._on_version_selected(val))

    def _on_version_selected(self, val):
        self._version_var.set(val)
        loader = self._loader_var.get()
        config.set("selected_version", val)
        config.set(f"selected_version_{loader}", val) # Keep track of specific loader's last version

    # ── Launch Actions ──────────────────────────────────────────────

    def _get_launch_callbacks(self):
        return {
            "log":      lambda msg: self.after(0, lambda m=msg: self._log(m)),
            "started":  lambda: self.after(0, self._on_game_started),
            "finished": lambda rc: self.after(0, lambda c=rc: self._on_game_finished(c)),
        }

    def _play(self):
        if self._launching: return
        version = self._version_var.get()
        if not version or "Cargando" in version or "Sin versiones" in version:
            self._log("[!] No hay versión instalada seleccionada.")
            return

        self._launching = True
        self._play_btn.configure_state(True)
        self._play_btn.set_text("Iniciando...")
        launch_minecraft(version, self._get_launch_callbacks())

    def _on_game_started(self):
        self._play_btn.set_text("Jugando...")
        self._log("Minecraft iniciado.")

    def _on_game_finished(self, rc):
        self._launching = False
        self._play_btn.configure_state(False)
        self._play_btn.set_text("JUGAR")
        if rc != -1:
            self._log(f"Minecraft cerrado (código {rc}).")

    def _log(self, msg: str):
        self._log_text.config(state="normal")
        self._log_text.insert("end", msg + "\n")
        self._log_text.see("end")
        self._log_text.config(state="disabled")

    def _logout(self):
        if self.app:
            self.app.logout()

    def _go_skins(self):
        if self.app:
            self.app.show_skins_view()

    def _go_settings(self):
        if self.app:
            self.app.show_settings_view()

    def _go_downloads(self):
        if self.app:
            self.app.show_downloads_view()

    def _show_profile(self):
        if self._profile_panel and self._profile_panel.winfo_exists():
            self._profile_panel.pack_forget()
            self._profile_panel.destroy()
            self._profile_panel = None
            return
        self._profile_panel = PlayerProfilePanel(
            self,
            on_close=lambda: setattr(self, '_profile_panel', None),
            width=380,
        )
        self._profile_panel.place(relx=0.98, rely=0.02, anchor="ne", width=380, relheight=0.95)

    # ── Public update methods ─────────────────────────────────────────────────

    def update_premium_ui(self):
        auth_type = config.get("auth_type") or "nopremium"
        username  = config.get("username") or "Player"

        if auth_type == "premium":
            badge = "[Premium]"
            badge_color = Colors.PREMIUM_GREEN
        else:
            badge = "[No Premium]"
            badge_color = Colors.NOPREMIUM_RED

        self._header_username.config(text=username)
        self._header_badge.config(text=badge, fg=badge_color)

    def update_skin_preview(self, force=False):
        auth_type = config.get("auth_type") or "nopremium"
        skin_path = config.get("skin_path") or ""

        if auth_type == "premium":
            uuid = config.get("uuid") or ""
            from core.skin_fetch import get_cached_skin, fetch_skin_from_mojang
            cached = get_cached_skin(uuid) or skin_path
            self._skin_head.set_skin(cached if os.path.exists(cached) else None)
            if uuid:
                def on_skin(path):
                    if path:
                        config.set("skin_path", path)
                        try:
                            if self.winfo_exists():
                                self.after(0, lambda p=path: self._skin_head.set_skin(p))
                        except Exception: pass
                fetch_skin_from_mojang(uuid, on_skin, force=force)
        else:
            self._skin_head.set_skin(skin_path if os.path.exists(skin_path) else None)

    def sync_launch_settings(self):
        """Refresh when returning to home."""
        self.update_premium_ui()
        self.update_skin_preview()
        self._select_loader(config.get("selected_type") or "Vanilla")
