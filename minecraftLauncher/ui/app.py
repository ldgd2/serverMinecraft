"""
Minecraft Launcher - App Entrypoint
Wires up all views with smooth slide transitions.
"""
import tkinter as tk
import os

from config.manager import config
from ui.theme import Colors, Assets, mc_font, load_minecraft_font

# Views
from ui.views.login     import LoginView
from ui.views.home      import HomeView
from ui.views.settings  import SettingsView
from ui.views.skins     import SkinsView
from ui.views.downloads import DownloadsView


class LauncherApp(tk.Tk):
    """Main launcher window — a thin shell that hosts the view stack."""

    def __init__(self):
        super().__init__()

        self.title("Minecraft Launcher")
        self.geometry("1100x700")
        self.minsize(900, 600)
        self.configure(bg=Colors.DARK)
        self.protocol("WM_DELETE_WINDOW", self.on_closing)

        # Load Minecraft font once
        load_minecraft_font()

        # Register font with tkinter if TTF file exists
        self._try_register_font()

        # Full-window container
        self.container = tk.Frame(self, bg=Colors.DARK)
        self.container.pack(fill="both", expand=True)

        # Instantiate all views (hidden by default)
        self.login_view     = LoginView(    self.container, app=self, on_login_success=self.on_login_success)
        self.home_view      = HomeView(     self.container, app=self)
        self.settings_view  = SettingsView( self.container, app=self)
        self.skins_view     = SkinsView(    self.container, app=self)
        self.downloads_view = DownloadsView(self.container, app=self,
                                             on_download_complete=self.home_view.sync_launch_settings)

        self.current_view: tk.Frame | None = None

        # Start on the right screen
        if config.get("logged_in"):
            self.show_home_view()
        else:
            self.show_login_view()

        # Optional: Discord RPC (non-fatal)
        try:
            from core.launcher import init_discord_rpc
            init_discord_rpc()
        except Exception:
            pass

    # ── Font registration ─────────────────────────────────────────────────────

    def _try_register_font(self):
        """Best-effort registration of Minecraft.ttf with tkinter."""
        font_path = Assets.FONT_MC
        if not os.path.exists(font_path):
            return
        try:
            # pyglet-based registration (works on Windows)
            import pyglet
            pyglet.font.add_file(font_path)
        except Exception:
            pass
        try:
            # Windows GDI registration via ctypes
            import ctypes
            ctypes.windll.gdi32.AddFontResourceW(font_path)
        except Exception:
            pass

    # ── View transitions ──────────────────────────────────────────────────────

    def _place(self, view: tk.Frame):
        view.place(relx=0, rely=0, relwidth=1, relheight=1)
        view.lift()

    def _hide(self, view: tk.Frame | None):
        if view and view.winfo_exists():
            view.place_forget()

    def show_view(self, view: tk.Frame, name: str):
        if self.current_view is view:
            return
        prev = self.current_view
        self.current_view = view

        # Slide-in animation
        view.place(relx=1.0, rely=0, relwidth=1, relheight=1)
        view.lift()
        self._slide(view, prev)

        # Sync live data for the target view
        if name == "home":
            self.home_view.sync_launch_settings()

    def _slide(self, view: tk.Frame, prev: tk.Frame | None, step: float = 0.0):
        if step >= 1.0:
            self._place(view)
            self._hide(prev)
            return
        x = (1.0 - step) ** 4          # eased
        view.place(relx=x, rely=0, relwidth=1, relheight=1)
        self.after(10, lambda: self._slide(view, prev, step + 0.06))

    # ── Named shortcuts ───────────────────────────────────────────────────────

    def show_login_view(self):
        self.current_view = self.login_view
        self._place(self.login_view)

    def show_home_view(self):
        self.show_view(self.home_view, "home")

    def show_settings_view(self, **_):
        self.show_view(self.settings_view, "settings")

    def show_skins_view(self, **_):
        self.show_view(self.skins_view, "skins")
        # Refresh preview after slide-in
        self.after(400, lambda: self.skins_view.on_show() if hasattr(self.skins_view, 'on_show') else None)

    def show_downloads_view(self, **_):
        self.show_view(self.downloads_view, "downloads")

    # ── Auth callbacks ────────────────────────────────────────────────────────

    def on_login_success(self):
        self._hide(self.login_view)
        self.home_view.sync_launch_settings()
        self.current_view = None
        self.show_home_view()

    def logout(self):
        config.set("logged_in",  False)
        config.set("username",   "")
        config.set("uuid",       "")
        config.set("auth_token", "")
        config.set("auth_type",  "nopremium")
        self._hide(self.home_view)
        self.current_view = None
        self.show_login_view()

    # ── Window events ─────────────────────────────────────────────────────────

    def on_closing(self):
        self.destroy()
