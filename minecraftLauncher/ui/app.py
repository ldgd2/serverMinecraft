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
from ui.views.profile   import ProfileView
from ui.views.updates   import UpdatesView


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
        self.profile_view   = ProfileView(  self.container, app=self)
        self.updates_view   = UpdatesView(  self.container, app=self)
        self.downloads_view = DownloadsView(self.container, app=self,
                                             on_download_complete=self.home_view.sync_launch_settings)

        self.current_view: tk.Frame | None = None

        # Start on the right screen
        if config.get("logged_in"):
            self.show_home_view()
            self.after(500, self.check_birthday_events)
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

    def show_profile_view(self, **_):
        self.show_view(self.profile_view, "profile")
        self.after(400, lambda: self.profile_view.on_show() if hasattr(self.profile_view, 'on_show') else None)

    def show_downloads_view(self, **_):
        self.show_view(self.downloads_view, "downloads")

    def show_updates_view(self, **_):
        self.show_view(self.updates_view, "updates")
        self.after(300, lambda: self.updates_view.on_show() if hasattr(self.updates_view, 'on_show') else None)

    def on_launcher_update_detected(self, latest, url):
        """Llamado desde el updater en background cuando hay una nueva versión."""
        from core.info import VERSION as CURRENT
        from ui.widgets import MinecraftToast
        
        def do_update():
            self._hide_toast()
            self.show_updates_view()
            if hasattr(self.updates_view, "trigger_auto_update"):
                self.updates_view.trigger_auto_update(latest, url)

        msg = "¡Actualización Disponible!"
        sub = f"v{CURRENT} → v{latest}. ¡Nuevas mejoras listas!"
        
        self.show_toast(msg, sub, action_text="Actualizar", on_action=do_update)

    def show_toast(self, text, subtext="", action_text="OK", on_action=None):
        from ui.widgets import MinecraftToast
        self._hide_toast()
        
        self._current_toast = MinecraftToast(
            self, text=text, subtext=subtext,
            action_text=action_text, on_action=on_action,
            on_close=self._hide_toast
        )
        # Position at the top, sliding down
        self._current_toast.place(relx=0.5, y=-100, anchor="n", relwidth=0.8)
        self._animate_toast(target_y=20)

    def _hide_toast(self):
        if hasattr(self, "_current_toast") and self._current_toast:
            self._current_toast.destroy()
            self._current_toast = None

    def _animate_toast(self, target_y, current_y=-100):
        if not self._current_toast or not self._current_toast.winfo_exists():
            return
        if current_y >= target_y:
            self._current_toast.place(relx=0.5, y=target_y, anchor="n", relwidth=0.8)
            return
        new_y = current_y + 5
        self._current_toast.place(relx=0.5, y=new_y, anchor="n", relwidth=0.8)
        self.after(10, lambda: self._animate_toast(target_y, new_y))

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

    # ── Birthday Logic ────────────────────────────────────────────────────────
    
    def check_birthday_events(self):
        acc_type = config.get("account_type")
        if acc_type == "guest": return
        
        bday = config.get("birthday")
        
        if not bday and acc_type == "premium":
            self._prompt_for_birthday()
        elif bday:
            self._check_if_birthday_today(bday)
            
    def _prompt_for_birthday(self):
        from ui.widgets import MinecraftDatePicker, MinecraftButton
        from core.auth import AuthController
        
        prompt = tk.Toplevel(self)
        prompt.title("¡Falta tu Cumpleanos!")
        prompt.geometry("400x300")
        prompt.configure(bg=Colors.PANEL_DARK)
        prompt.resizable(False, False)
        prompt.transient(self)
        prompt.grab_set()
        
        x = self.winfo_rootx() + (self.winfo_width() // 2) - 200
        y = self.winfo_rooty() + (self.winfo_height() // 2) - 150
        prompt.geometry(f"+{x}+{y}")
        
        tk.Label(prompt, text="¿Cuándo es tu cumpleaños?", fg=Colors.YELLOW, bg=Colors.PANEL_DARK, font=mc_font(14, bold=True)).pack(pady=(20, 10))
        tk.Label(prompt, text="Para darte premios especiales en tu día.", fg=Colors.GRAY_TEXT, bg=Colors.PANEL_DARK, font=mc_font(9)).pack(pady=(0, 15))
        
        picker = MinecraftDatePicker(prompt, bg=Colors.PANEL_DARK)
        picker.pack(pady=10)
        
        def save():
            new_bday = picker.get()
            config.set("birthday", new_bday)
            
            # Send to backend
            def _send():
                auth = AuthController()
                token = config.get("player_token")
                if token:
                    auth.update_birthday(new_bday, token)
            
            import threading
            threading.Thread(target=_send, daemon=True).start()
            
            prompt.destroy()
            self._check_if_birthday_today(new_bday)
            
        MinecraftButton(prompt, text="Guardar", width=150, height=35, command=save).pack(pady=20)

    def _check_if_birthday_today(self, bday_str):
        import datetime
        import random
        try:
            # Expected format MM-DD or YYYY-MM-DD (fallback)
            parts = bday_str.split("-")
            if len(parts) == 3:
                month_idx, day_idx = 1, 2
            elif len(parts) == 2:
                month_idx, day_idx = 0, 1
            else:
                return
            
            today = datetime.date.today()
            if today.month == int(parts[month_idx]) and today.day == int(parts[day_idx]):
                
                # We show a message only once per day (to not annoy if they login multiple times)
                last_congrats = config.get("last_birthday_congrats")
                if last_congrats == str(today): return
                
                config.set("last_birthday_congrats", str(today))
                
                messages = [
                    "¡Feliz cumpleaños! Ojalá encuentres muchos diamantes hoy.",
                    "¡Feliz nivel nuevo en la vida real! Sigue minando.",
                    "¡Que tengas un día épico! Cuidado con los Creepers.",
                    "¡Feliz cumple! Hoy los zombies no te atacarán... (es broma, sí lo harán)."
                ]
                msg = random.choice(messages)
                
                # Show custom popup
                from ui.widgets import MinecraftButton
                win = tk.Toplevel(self)
                win.title("¡Feliz Cumpleanos!")
                win.geometry("450x200")
                win.configure(bg=Colors.PANEL_DARK)
                win.resizable(False, False)
                win.transient(self)
                
                x = self.winfo_rootx() + (self.winfo_width() // 2) - 225
                y = self.winfo_rooty() + (self.winfo_height() // 2) - 100
                win.geometry(f"+{x}+{y}")
                
                tk.Label(win, text="🎂 ¡FELIZ CUMPLEAÑOS! 🎂", fg=Colors.PREMIUM_GREEN, bg=Colors.PANEL_DARK, font=mc_font(16, bold=True)).pack(pady=(20, 10))
                tk.Label(win, text=msg, fg=Colors.WHITE, bg=Colors.PANEL_DARK, font=mc_font(10), wraplength=400, justify="center").pack(pady=(0, 20))
                
                MinecraftButton(win, text="¡Gracias!", width=150, height=35, command=win.destroy).pack()
        except Exception as e:
            print("Error checking birthday:", e)

    # ── Window events ─────────────────────────────────────────────────────────

    def on_closing(self):
        self.destroy()
