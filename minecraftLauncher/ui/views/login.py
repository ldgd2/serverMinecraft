"""
Minecraft Launcher - Login View
3 modes:
  - Microsoft  → Premium, opens browser OAuth → username auto set by Mojang
  - Servidor   → No-Premium, server IP+pass, username taken from server response (read-only)
  - Invitado   → No-Premium, custom editable username, no server needed
"""
import tkinter as tk
import os
import threading
from PIL import Image, ImageTk, ImageDraw

from ui.theme import Colors, Assets, mc_font
from ui.widgets import (
    MinecraftButton, MinecraftInput,
    PanoramaBackground
)
from config.manager import config
from core.auth import AuthController
from core.security import encrypt_data
from core.info import VERSION


# ── Microsoft logo renderer (pure PIL, no cairosvg) ─────────────────────────

def _make_ms_logo(size: int = 22) -> Image.Image:
    """
    Draw the Microsoft 4-color logo (2x2 grid) as a PIL RGBA image.
    """
    pad = 2
    inner = size - pad * 2
    half = inner // 2
    gap = 1
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    # Top-left  — red
    d.rectangle([pad, pad, pad + half - gap, pad + half - gap], fill="#f25022")
    # Top-right — green
    d.rectangle([pad + half + gap, pad, pad + inner, pad + half - gap], fill="#7fba00")
    # Bottom-left — blue
    d.rectangle([pad, pad + half + gap, pad + half - gap, pad + inner], fill="#00a4ef")
    # Bottom-right — yellow
    d.rectangle([pad + half + gap, pad + half + gap, pad + inner, pad + inner], fill="#ffb900")
    return img


class LoginView(tk.Frame):
    """
    Full-screen login view with animated panorama background.
    
    Modes:
      'microsoft' — Premium OAuth login → Microsoft account
      'servidor'  — No-Premium server login → username from server (read-only)
      'invitado'  — No-Premium guest login → editable username, no server required
    """

    def __init__(self, master, app=None, on_login_success=None, **kwargs):
        super().__init__(master, bg=Colors.DARK, **kwargs)
        self.app = app
        self.on_login_success = on_login_success
        self._auth = AuthController()
        self._mode = "microsoft"

        # Pre-render Microsoft logo using PIL
        self._ms_logo_pil = _make_ms_logo(22)
        self._ms_logo_tk  = None   # set after build when canvas exists

        self._build_ui()

    # ── Build ──────────────────────────────────────────────────────────────────

    def _build_ui(self):
        # Panorama background fills the frame
        self.panorama = PanoramaBackground(self, bg=Colors.DARK)
        self.panorama.place(relx=0, rely=0, relwidth=1, relheight=1)

        # Outer centered column
        center = tk.Frame(self, bg=Colors.PANEL_DARK,
                          highlightthickness=2,
                          highlightbackground=Colors.PANEL_BORDER)
        center.place(relx=0.5, rely=0.5, anchor="center")
        self._center = center

        # ── Logo ──────────────────────────────────────────────────────────────
        if os.path.exists(Assets.TITLE_LOGO):
            img = Image.open(Assets.TITLE_LOGO).convert("RGBA")
            ratio = 360 / img.width
            img = img.resize((360, int(img.height * ratio)), Image.LANCZOS)
            self._tk_logo = ImageTk.PhotoImage(img)
            tk.Label(center, image=self._tk_logo, bg=Colors.PANEL_DARK,
                     bd=0).pack(pady=(16, 0))
        else:
            tk.Label(center, text="MINECRAFT", fg=Colors.WHITE,
                     bg=Colors.PANEL_DARK, font=mc_font(28, bold=True)).pack(pady=(16, 0))

        # Thin separator
        if os.path.exists(Assets.HEADER_SEP):
            sep_img = Image.open(Assets.HEADER_SEP).convert("RGBA")
            sep_img = sep_img.resize((420, max(sep_img.height, 2)), Image.NEAREST)
            self._tk_sep = ImageTk.PhotoImage(sep_img)
            tk.Label(center, image=self._tk_sep, bg=Colors.PANEL_DARK,
                     bd=0).pack(pady=(4, 12))

        # ── Settings Gear ──
        if os.path.exists(Assets.ICON_SETTINGS):
            img = Image.open(Assets.ICON_SETTINGS).convert("RGBA").resize((24, 24), Image.NEAREST)
            self._gear_tk = ImageTk.PhotoImage(img)
            self._gear_btn = tk.Button(self.panorama, image=self._gear_tk, bg="#000000", bd=0, 
                                        activebackground="#333333", cursor="hand2",
                                        command=self._open_api_settings)
            self._gear_btn.place(relx=1.0, x=-15, y=15, anchor="ne")
            tk.Label(center, image=self._tk_sep, bg=Colors.PANEL_DARK, bd=0).pack(pady=(4, 0))
        else:
            tk.Frame(center, bg=Colors.PANEL_BORDER, height=2).pack(fill="x", padx=12, pady=4)

        # ── Version Label (Bottom Right) ──────────────────────────────────────
        self.version_lbl = tk.Label(self, text=f"v{VERSION}", fg=Colors.GRAY_TEXT,
                                    bg=Colors.DARK, font=mc_font(10))
        self.version_lbl.place(relx=1.0, rely=1.0, x=-10, y=-10, anchor="se")

        # Splash subtitle
        tk.Label(center, text="Minecraft Launcher", fg=Colors.YELLOW,
                 bg=Colors.PANEL_DARK, font=mc_font(10)).pack(pady=(4, 10))

        # ── Mode tab buttons ──────────────────────────────────────────────────
        tabs_frame = tk.Frame(center, bg=Colors.PANEL_DARK)
        tabs_frame.pack(padx=10, pady=(0, 2))

        tab_w = 138
        self._tab_microsoft = MinecraftButton(tabs_frame, text="Microsoft", width=tab_w, height=30,
                                               font_size=9, command=lambda: self._switch_mode("microsoft"))
        self._tab_microsoft.pack(side="left", padx=2)

        self._tab_servidor = MinecraftButton(tabs_frame, text="Servidor", width=tab_w, height=30,
                                              font_size=9, command=lambda: self._switch_mode("servidor"))
        self._tab_servidor.pack(side="left", padx=2)

        self._tab_invitado = MinecraftButton(tabs_frame, text="Invitado", width=tab_w, height=30,
                                              font_size=9, command=lambda: self._switch_mode("invitado"))
        self._tab_invitado.pack(side="left", padx=2)

        # ── Inner panel (changes per mode) ────────────────────────────────────
        self._panel = tk.Frame(center, bg=Colors.PANEL_DARK,
                               highlightthickness=1,
                               highlightbackground=Colors.PANEL_BORDER,
                               padx=20, pady=14)
        self._panel.pack(fill="x", padx=10, pady=(4, 0))

        self._build_microsoft_form()
        self._build_servidor_form()
        self._build_invitado_form()

        # Status
        self._status_var = tk.StringVar(value="")
        self._status_lbl = tk.Label(center, textvariable=self._status_var,
                                    fg=Colors.NOPREMIUM_RED, bg=Colors.PANEL_DARK,
                                    font=mc_font(9), wraplength=420)
        self._status_lbl.pack(pady=(6, 14))

        self._switch_mode(config.get("last_login_mode") or "invitado")

    # ── Form builders ──────────────────────────────────────────────────────────

    def _build_microsoft_form(self):
        f = tk.Frame(self._panel, bg=Colors.PANEL_DARK)
        self._ms_frame = f

        info = tk.Label(f,
                         text="Inicia sesion con tu cuenta de Microsoft.\n"
                              "Se abrira el navegador; vuelve cuando hayas autorizado.",
                         fg=Colors.GRAY_TEXT, bg=Colors.PANEL_DARK,
                         font=mc_font(9), justify="center")
        info.pack(pady=(0, 10))

        # Microsoft button — canvas so we can draw the logo inline
        btn_container = tk.Frame(f, bg=Colors.PANEL_DARK)
        btn_container.pack()

        self._ms_btn = MinecraftButton(
            btn_container,
            text="  Iniciar sesion con Microsoft",
            width=420, height=44,
            icon_img=self._ms_logo_pil,
            command=self._start_microsoft_login
        )
        self._ms_btn.pack()

    def _build_servidor_form(self):
        f = tk.Frame(self._panel, bg=Colors.PANEL_DARK)
        self._srv_frame = f

        info = tk.Label(f, text="Inicia sesion con tu cuenta del servidor.", 
                        fg=Colors.GRAY_TEXT, bg=Colors.PANEL_DARK, font=mc_font(9))
        info.pack(pady=(0, 10))

        # Credentials
        usr_row = tk.Frame(f, bg=Colors.PANEL_DARK)
        usr_row.pack(fill="x", pady=(0, 4))
        tk.Label(usr_row, text="Usuario:", fg=Colors.WHITE,
                 bg=Colors.PANEL_DARK, font=mc_font(9), width=9, anchor="w").pack(side="left")
        self._srv_user = MinecraftInput(usr_row, placeholder="Nombre de usuario",
                                         width=320, height=30)
        self._srv_user.pack(side="left", padx=4)

        pass_row = tk.Frame(f, bg=Colors.PANEL_DARK)
        pass_row.pack(fill="x", pady=(0, 8))
        tk.Label(pass_row, text="Contrasena:", fg=Colors.WHITE,
                 bg=Colors.PANEL_DARK, font=mc_font(9), width=9, anchor="w").pack(side="left")
        self._srv_pass = MinecraftInput(pass_row, placeholder="Contrasena",
                                         width=320, height=30, show="*")
        self._srv_pass.pack(side="left", padx=4)

        btn_row = tk.Frame(f, bg=Colors.PANEL_DARK)
        btn_row.pack()
        self._srv_login_btn = MinecraftButton(btn_row, text="Iniciar Sesion",
                                               width=200, height=38,
                                               command=self._do_servidor_login)
        self._srv_login_btn.pack(side="left", padx=2)
        self._srv_reg_btn = MinecraftButton(btn_row, text="Registrarse",
                                             width=200, height=38,
                                             command=self._do_servidor_register)
        self._srv_reg_btn.pack(side="left", padx=2)

        tk.Label(f, text="El nombre de usuario proviene del servidor y no puede cambiarse manualmente.",
                 fg=Colors.GRAY_TEXT, bg=Colors.PANEL_DARK, font=mc_font(8),
                 wraplength=420).pack(pady=(6, 0))

    def _build_invitado_form(self):
        f = tk.Frame(self._panel, bg=Colors.PANEL_DARK)
        self._inv_frame = f

        info = tk.Label(f,
                         text="Juega como invitado sin necesidad de cuenta.\n"
                              "Elige tu nombre de usuario (se guardara para la proxima vez).",
                         fg=Colors.GRAY_TEXT, bg=Colors.PANEL_DARK,
                         font=mc_font(9), justify="center")
        info.pack(pady=(0, 10))

        usr_row = tk.Frame(f, bg=Colors.PANEL_DARK)
        usr_row.pack()
        tk.Label(usr_row, text="Nombre:", fg=Colors.WHITE,
                 bg=Colors.PANEL_DARK, font=mc_font(10), width=8, anchor="w").pack(side="left")
        self._inv_user = MinecraftInput(usr_row, placeholder="TuNombre",
                                         width=300, height=32, font_size=12)
        self._inv_user.pack(side="left", padx=6)
        saved = config.get("guest_username") or ""
        if saved:
            self._inv_user.set(saved)

        self._inv_btn = MinecraftButton(f, text="Jugar como Invitado",
                                         width=420, height=44, font_size=14,
                                         command=self._do_invitado_login)
        self._inv_btn.pack(pady=(12, 0))

    # ── Mode switching ────────────────────────────────────────────────────────

    def _switch_mode(self, mode):
        self._mode = mode
        config.set("last_login_mode", mode)

        for w in self._panel.winfo_children():
            w.pack_forget()

        if mode == "microsoft":
            self._ms_frame.pack(fill="x")
        elif mode == "servidor":
            self._srv_frame.pack(fill="x")
        else:
            self._inv_frame.pack(fill="x")

        self._status_var.set("")

    # ── Microsoft OAuth ───────────────────────────────────────────────────────

    def _start_microsoft_login(self):
        try:
            from core.oauth import start_oauth_flow, exchange_code_for_tokens
        except ImportError:
            self._set_status("Modulo OAuth no encontrado.", Colors.NOPREMIUM_RED)
            return

        self._set_status("Abriendo navegador... Espera hasta que completes el login.", Colors.GRAY_TEXT)
        self._ms_btn.configure_state(True)

        def on_code(code):
            if not self.winfo_exists(): return
            self.after(0, lambda: self._set_status("Verificando con Mojang...", Colors.GRAY_TEXT))
            result = exchange_code_for_tokens(code)
            if self.winfo_exists():
                self.after(0, lambda: self._handle_ms_result(result))

        def on_error(msg):
            if self.winfo_exists():
                self.after(0, lambda: self._set_status(f"Error: {msg}", Colors.NOPREMIUM_RED))
                self.after(0, lambda: self._ms_btn.configure_state(False))

        start_oauth_flow(on_code, on_error)

    def _handle_ms_result(self, result):
        self._ms_btn.configure_state(False)
        if result.get("status") == "OK":
            data = result["data"]
            config.set("username",   data["name"])
            config.set("uuid",       data["uuid"])
            config.set("auth_token", encrypt_data(data["access_token"]))
            config.set("ms_refresh_token", data.get("refresh_token", ""))
            config.set("auth_type",  "premium")
            config.set("account_type", "premium")
            config.set("logged_in",  True)

            # Notify backend and store player token in background
            def _notify_and_store():
                player_token = self._auth.notify_premium_login_backend(
                    data["name"], data["uuid"],
                    data.get("access_token", ""), data.get("refresh_token", "")
                )
                if player_token:
                    # player_token is actually a dict from our new backend login_premium_player if we modified auth.py to return it.
                    # Wait, notify_premium_login_backend only returned the token string previously.
                    # I need to update notify_premium_login_backend to return the full payload or just save the birthday here if possible.
                    pass
            # I will modify notify_premium_login_backend later to return the dict instead of string if needed.
            
            # Actually, _handle_ms_result is pure Microsoft OAuth result!
            # The backend notification happens in the thread. So the birthday is returned BY THE BACKEND.
            # So I will move the config.set("birthday") to inside that thread!
            
            def _notify_and_store_v2():
                res = self._auth.notify_premium_login_backend(
                    data["name"], data["uuid"],
                    data.get("access_token", ""), data.get("refresh_token", "")
                )
                if isinstance(res, dict) and res.get("status") == "success":
                    backend_data = res.get("data", {})
                    config.set("player_token", backend_data.get("access_token", ""))
                    config.set("birthday", backend_data.get("birthday", ""))
                elif isinstance(res, str):
                    config.set("player_token", res) # fallback
                
                # Check birthday immediately after
                self.after(0, self.app.check_birthday_events)

            threading.Thread(target=_notify_and_store_v2, daemon=True).start()

            self._set_status(f"Bienvenido, {data['name']}! (Premium)", Colors.PREMIUM_GREEN)
            self.after(700, self._fire_success)
        else:
            self._set_status(result.get("message", "Error desconocido."), Colors.NOPREMIUM_RED)

    # ── Servidor Login ────────────────────────────────────────────────────────

    def _do_servidor_login(self):
        username = self._srv_user.get().strip()
        password = self._srv_pass.get().strip()
        if not username or not password:
            self._set_status("Introduce usuario y contrasena.", Colors.NOPREMIUM_RED)
            return

        self._set_status("Conectando...", Colors.GRAY_TEXT)
        self._srv_login_btn.configure_state(True)

        def do():
            r = self._auth.login_no_premium(username, password)
            self.after(0, lambda: self._handle_srv_result(r))

        threading.Thread(target=do, daemon=True).start()

    def _handle_srv_result(self, result):
        self._srv_login_btn.configure_state(False)
        if result.get("status") == "OK":
            data = result["data"]
            # Username is ALWAYS what the server says — read-only after this
            server_username = data.get("username") or data.get("name") or self._srv_user.get()
            config.set("username",      server_username)
            config.set("uuid",          data.get("uuid", ""))
            config.set("auth_token",    encrypt_data(data.get("token", "")))
            config.set("player_token",  data.get("token", ""))  # JWT del jugador (sin cifrar, para la API)
            config.set("password",      self._srv_pass.get())   # Save password for auto-login
            config.set("auth_type",     "nopremium")
            config.set("account_type",  "server")
            config.set("birthday",      data.get("birthday", ""))
            config.set("logged_in",     True)
            config.set("guest_username", "")
            self._set_status(f"Bienvenido, {server_username}! (Servidor)", Colors.PREMIUM_GREEN)
            self.after(600, self._fire_success)
            self.after(800, self.app.check_birthday_events)
        elif result.get("status") == "RENAME":
            self._set_status("Usuario renombrado por el servidor. Intenta de nuevo.", Colors.YELLOW)
        else:
            self._set_status(result.get("message", "Error de autenticacion."), Colors.NOPREMIUM_RED)

    def _do_servidor_register(self):
        """Open a dedicated overlay window for registration."""
        reg_win = tk.Toplevel(self)
        reg_win.title("Registrar Nueva Cuenta")
        reg_win.geometry("400x450")
        reg_win.resizable(False, False)
        reg_win.configure(bg=Colors.PANEL_DARK)
        reg_win.transient(self)
        reg_win.grab_set()

        # Center on parent
        x = self.winfo_rootx() + (self.winfo_width() // 2) - 200
        y = self.winfo_rooty() + (self.winfo_height() // 2) - 225
        reg_win.geometry(f"+{x}+{y}")

        tk.Label(reg_win, text="Registro de Cuenta", fg=Colors.WHITE, 
                 bg=Colors.PANEL_DARK, font=mc_font(14, bold=True)).pack(pady=(20, 10))

        # Username
        tk.Label(reg_win, text="Usuario:", fg=Colors.GRAY_TEXT, bg=Colors.PANEL_DARK, font=mc_font(9)).pack(anchor="w", padx=40)
        reg_user = MinecraftInput(reg_win, placeholder="Nombre de usuario", width=320, height=36)
        reg_user.pack(pady=(0, 10))
        
        # Password
        tk.Label(reg_win, text="Contrasena:", fg=Colors.GRAY_TEXT, bg=Colors.PANEL_DARK, font=mc_font(9)).pack(anchor="w", padx=40)
        reg_pass = MinecraftInput(reg_win, placeholder="Contrasena secreta", width=320, height=36, show="*")
        reg_pass.pack(pady=(0, 10))

        # Birthday
        tk.Label(reg_win, text="Fecha de nacimiento:", fg=Colors.GRAY_TEXT, bg=Colors.PANEL_DARK, font=mc_font(9)).pack(anchor="w", padx=40)
        from ui.widgets import MinecraftDatePicker
        reg_bday = MinecraftDatePicker(reg_win, bg=Colors.PANEL_DARK)
        reg_bday.pack(pady=(5, 20))

        status_var = tk.StringVar()
        tk.Label(reg_win, textvariable=status_var, fg=Colors.NOPREMIUM_RED, bg=Colors.PANEL_DARK, font=mc_font(9), wraplength=320).pack(pady=(0, 10))

        def _submit_registration():
            username = reg_user.get().strip()
            password = reg_pass.get().strip()
            birthday = reg_bday.get()
            
            if not username or not password:
                status_var.set("Usuario y contrasena son obligatorios.")
                return
            
            status_var.set("Registrando...")
            reg_btn.configure_state(True)
            
            def do():
                result = self._auth.register_no_premium(username, password, birthday)
                self.after(0, lambda: _handle(result))
            threading.Thread(target=do, daemon=True).start()

        def _handle(result):
            reg_btn.configure_state(False)
            if result.get("status") == "OK":
                status_var.set("¡Cuenta creada con éxito! Iniciando sesión...")
                self.after(1000, reg_win.destroy)
                self._handle_register_result(result, reg_user.get().strip())
            else:
                status_var.set(result.get("message", "Error al registrar."))

        reg_btn = MinecraftButton(reg_win, text="Crear Cuenta", width=200, height=40, command=_submit_registration)
        reg_btn.pack(pady=10)

    def _handle_register_result(self, result, requested_username=""):
        if result.get("status") == "OK":
            data = result.get("data", {})
            if data.get("access_token") or data.get("token"):
                token = data.get("access_token") or data.get("token")
                server_username = data.get("username") or requested_username
                config.set("username",     server_username)
                config.set("uuid",         data.get("uuid", ""))
                config.set("auth_token",   encrypt_data(token))
                config.set("player_token", token)
                config.set("password",     reg_pass.get())  # Save password for auto-login
                config.set("auth_type",    "nopremium")
                config.set("account_type", "server")
                config.set("birthday",     data.get("birthday", ""))
                config.set("logged_in",    True)
                self._set_status(f"Cuenta creada. Bienvenido, {server_username}!", Colors.PREMIUM_GREEN)
                self.after(700, self._fire_success)
                self.after(900, self.app.check_birthday_events)
            else:
                self._set_status("Cuenta creada. Ya puedes iniciar sesion.", Colors.PREMIUM_GREEN)
        else:
            self._set_status(result.get("message", "Error al registrar."), Colors.NOPREMIUM_RED)

    # ── Invitado (Guest) Login ─────────────────────────────────────────────────

    def _do_invitado_login(self):
        username = self._inv_user.get().strip()
        if not username:
            self._set_status("Escribe un nombre de usuario.", Colors.NOPREMIUM_RED)
            return
        if len(username) < 3:
            self._set_status("El nombre debe tener al menos 3 caracteres.", Colors.NOPREMIUM_RED)
            return

        # Save guest username for next time
        config.set("guest_username", username)
        config.set("username",       username)
        config.set("uuid",           "")
        config.set("auth_token",     "")
        config.set("auth_type",      "nopremium")
        config.set("account_type",   "guest")
        config.set("logged_in",      True)

        self._set_status(f"Entrando como {username}...", Colors.GRAY_TEXT)
        self.after(400, self._fire_success)

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _set_status(self, msg, color=Colors.GRAY_TEXT):
        self._status_var.set(msg)
        self._status_lbl.config(fg=color)

    def _fire_success(self):
        if self.on_login_success:
            self.on_login_success()

    # ── API Settings Overlay ──
    def _open_api_settings(self):
        """Open a simple overlay to configure the API URL."""
        overlay = tk.Toplevel(self)
        overlay.title("Configuracion de API")
        overlay.geometry("450x320")
        overlay.resizable(False, False)
        overlay.configure(bg=Colors.PANEL_DARK)
        overlay.transient(self)
        overlay.grab_set()

        # Center on parent
        x = self.winfo_rootx() + (self.winfo_width() // 2) - 225
        y = self.winfo_rooty() + (self.winfo_height() // 2) - 100
        overlay.geometry(f"+{x}+{y}")

        tk.Label(overlay, text="URL del Servidor / API", fg=Colors.WHITE, 
                 bg=Colors.PANEL_DARK, font=mc_font(12, bold=True)).pack(pady=(20, 5))
        
        tk.Label(overlay, text="Ej: http://mi-servidor.com o http://localhost:8000", 
                 fg=Colors.GRAY_TEXT, bg=Colors.PANEL_DARK, font=mc_font(8)).pack(pady=(0, 10))

        api_input = MinecraftInput(overlay, width=400, height=36)
        api_input.pack(pady=5)
        
        current_api = config.get("api_url") or "http://localhost:8000/api/v1"
        # Strip /api/v1 for easier editing if present
        display_api = current_api.replace("/api/v1", "")
        api_input.set(display_api)

        tk.Label(overlay, text="API Key (Opcional para Admin)", fg=Colors.WHITE, 
                 bg=Colors.PANEL_DARK, font=mc_font(10)).pack(pady=(10, 5))
        
        key_input = MinecraftInput(overlay, width=400, height=36, show="*")
        key_input.pack(pady=5)
        key_input.set(config.get("api_key") or "")

        def save_api():
            new_url = api_input.get().strip()
            new_key = key_input.get().strip()
            if new_url:
                if not new_url.startswith("http"):
                    new_url = "http://" + new_url
                # Ensure it ends with /api/v1 for AuthController
                if not new_url.endswith("/api/v1"):
                    new_url = new_url.rstrip("/") + "/api/v1"
                
                config.set("api_url", new_url)
                config.set("api_key", new_key)
                # Also set server_ip for auto-join if it looks like an IP
                try:
                    parts = new_url.replace("http://", "").replace("https://", "").split("/")[0].split(":")
                    config.set("server_ip", parts[0])
                except:
                    pass
                
                # Re-init auth controller with new URL
                self._auth = AuthController()
                overlay.destroy()

        MinecraftButton(overlay, text="Guardar", width=150, height=36, command=save_api).pack(pady=15)
