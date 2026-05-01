"""
Player Profile View — muestra el perfil, estadísticas y logros del jugador autenticado.
Se muestra como panel deslizante desde la pantalla de inicio.
"""
import tkinter as tk
import threading
from ui.theme import Colors, mc_font
from config.manager import config
from core.auth import AuthController


# ─── Helpers ──────────────────────────────────────────────────────────────────

def _format_playtime(seconds: int) -> str:
    h = seconds // 3600
    m = (seconds % 3600) // 60
    return f"{h}h {m}m"


# ─── Profile Panel ─────────────────────────────────────────────────────────────

class PlayerProfilePanel(tk.Frame):
    """
    Panel flotante que muestra el perfil del jugador actual.
    Se carga asíncronamente desde el backend.
    """

    def __init__(self, master, on_close=None, **kwargs):
        super().__init__(master, bg=Colors.PANEL_DARK,
                         highlightthickness=2,
                         highlightbackground=Colors.PANEL_BORDER, **kwargs)
        self.on_close = on_close
        self._auth = AuthController()
        self._profile = {}
        self._leaderboard = []

        self._build_ui()
        self._load_async()

    # ── UI Build ──────────────────────────────────────────────────────────────

    def _build_ui(self):
        # Header
        header = tk.Frame(self, bg=Colors.DARK_BUTTON)
        header.pack(fill="x", pady=(0, 8))

        tk.Label(header, text="👤  Perfil del Jugador", fg=Colors.YELLOW,
                 bg=Colors.DARK_BUTTON, font=mc_font(13, bold=True),
                 pady=10).pack(side="left", padx=12)

        tk.Button(header, text="✕", bg=Colors.DARK_BUTTON, fg=Colors.GRAY_TEXT,
                  font=mc_font(11, bold=True), bd=0, cursor="hand2",
                  command=self._close).pack(side="right", padx=10)

        # Spinner label
        self._status_lbl = tk.Label(self, text="Cargando perfil...",
                                     fg=Colors.GRAY_TEXT, bg=Colors.PANEL_DARK,
                                     font=mc_font(10))
        self._status_lbl.pack(pady=20)

        # Content frame (hidden until loaded)
        self._content = tk.Frame(self, bg=Colors.PANEL_DARK)

        # Username + type badge
        self._uname_var = tk.StringVar()
        self._type_var  = tk.StringVar()

        top_row = tk.Frame(self._content, bg=Colors.PANEL_DARK)
        top_row.pack(fill="x", padx=16, pady=(0, 8))

        tk.Label(top_row, textvariable=self._uname_var,
                 fg=Colors.WHITE, bg=Colors.PANEL_DARK,
                 font=mc_font(15, bold=True)).pack(side="left")
        self._badge_lbl = tk.Label(top_row, textvariable=self._type_var,
                                    fg=Colors.PANEL_DARK, bg=Colors.PREMIUM_GREEN,
                                    font=mc_font(8, bold=True), padx=6, pady=2)
        self._badge_lbl.pack(side="left", padx=8)

        # Member since
        self._since_var = tk.StringVar()
        tk.Label(self._content, textvariable=self._since_var,
                 fg=Colors.GRAY_TEXT, bg=Colors.PANEL_DARK,
                 font=mc_font(8)).pack(anchor="w", padx=16)

        # Separator
        tk.Frame(self._content, bg=Colors.PANEL_BORDER, height=1).pack(fill="x", padx=12, pady=10)

        # Stats grid
        self._stats_frame = tk.Frame(self._content, bg=Colors.PANEL_DARK)
        self._stats_frame.pack(fill="x", padx=16)

        # Highlights
        tk.Frame(self._content, bg=Colors.PANEL_BORDER, height=1).pack(fill="x", padx=12, pady=10)
        tk.Label(self._content, text="✨  Mejores Jugadas", fg=Colors.YELLOW,
                 bg=Colors.PANEL_DARK, font=mc_font(10, bold=True)).pack(anchor="w", padx=16)

        self._high_frame = tk.Frame(self._content, bg=Colors.PANEL_DARK)
        self._high_frame.pack(fill="x", padx=12, pady=(4, 8))

        # Achievements
        tk.Frame(self._content, bg=Colors.PANEL_BORDER, height=1).pack(fill="x", padx=12, pady=10)
        tk.Label(self._content, text="🏆  Logros", fg=Colors.YELLOW,
                 bg=Colors.PANEL_DARK, font=mc_font(10, bold=True)).pack(anchor="w", padx=16)

        self._ach_frame = tk.Frame(self._content, bg=Colors.PANEL_DARK)
        self._ach_frame.pack(fill="x", padx=12, pady=(4, 8))

        # Leaderboard button
        tk.Frame(self._content, bg=Colors.PANEL_BORDER, height=1).pack(fill="x", padx=12, pady=4)
        tk.Button(self._content, text="🏅  Ver Tabla de Clasificación", bd=0,
                  bg=Colors.DARK_BUTTON, fg=Colors.YELLOW,
                  font=mc_font(9), cursor="hand2",
                  command=self._show_leaderboard).pack(pady=8)

        # Leaderboard frame
        self._lb_frame = tk.Frame(self._content, bg=Colors.PANEL_DARK)
        self._lb_frame.pack(fill="x", padx=12, pady=(0, 8))

    # ── Async Loading ─────────────────────────────────────────────────────────

    def _load_async(self):
        def do():
            player_token = config.get("player_token") or ""
            profile = {}
            lb = []
            if player_token:
                profile = self._auth.get_player_profile(player_token)
            lb = self._auth.get_leaderboard()
            self.after(0, lambda: self._render(profile, lb))

        threading.Thread(target=do, daemon=True).start()

    def _render(self, profile: dict, leaderboard: list):
        self._status_lbl.pack_forget()
        self._profile = profile
        self._leaderboard = leaderboard

        if not profile:
            # No token / offline
            username = config.get("username") or "Invitado"
            acct_type = config.get("account_type") or "guest"
            self._uname_var.set(username)
            self._type_var.set(acct_type.upper())
            self._since_var.set("Sin perfil en el servidor")
            if acct_type == "guest":
                self._badge_lbl.config(bg=Colors.GRAY_TEXT)
            self._content.pack(fill="both", expand=True)
            return

        self._uname_var.set(profile.get("username", "—"))
        acct = profile.get("account_type", "nopremium")
        badge_colors = {"premium": Colors.PREMIUM_GREEN, "nopremium": "#e8a83a", "guest": Colors.GRAY_TEXT}
        self._type_var.set({"premium": "PREMIUM", "nopremium": "NO-PREMIUM", "guest": "INVITADO"}.get(acct, acct.upper()))
        self._badge_lbl.config(bg=badge_colors.get(acct, Colors.GRAY_TEXT))

        since_raw = profile.get("member_since", "")
        self._since_var.set(f"Miembro desde: {since_raw[:10]}" if since_raw else "")

        # Stats
        for w in self._stats_frame.winfo_children():
            w.destroy()

        stats = profile.get("stats", {})
        stat_rows = [
            ("⏱  Tiempo de juego", stats.get("playtime", "—")),
            ("⚔️  Kills",           str(stats.get("kills", 0))),
            ("💀  Muertes",          str(stats.get("deaths", 0))),
            ("⚖️  K/D Ratio",        str(stats.get("kd_ratio", 0))),
            ("🔥  Mejor racha",      str(stats.get("best_kill_streak", 0))),
            ("⛏️  Bloques rotos",    str(stats.get("blocks_broken", 0))),
            ("🧱  Bloques puestos",  str(stats.get("blocks_placed", 0))),
            ("🌐  Servidores",        str(profile.get("servers_played", 0))),
        ]

        for i, (label, value) in enumerate(stat_rows):
            row = i // 2
            col = (i % 2) * 2
            tk.Label(self._stats_frame, text=label, fg=Colors.GRAY_TEXT,
                     bg=Colors.PANEL_DARK, font=mc_font(8),
                     anchor="w", width=20).grid(row=row, column=col, sticky="w", pady=2)
            tk.Label(self._stats_frame, text=value, fg=Colors.WHITE,
                     bg=Colors.PANEL_DARK, font=mc_font(9, bold=True),
                     anchor="w").grid(row=row, column=col + 1, sticky="w", padx=(4, 16), pady=2)

        # Highlights
        for w in self._high_frame.winfo_children():
            w.destroy()
        
        highlights = profile.get("highlights", [])
        if not highlights:
            tk.Label(self._high_frame, text="Sin jugadas destacadas.",
                     fg=Colors.GRAY_TEXT, bg=Colors.PANEL_DARK, font=mc_font(8)).pack(anchor="w")
        else:
            for h in highlights[:5]:
                tk.Label(self._high_frame, text=h, fg=Colors.WHITE,
                         bg=Colors.PANEL_DARK, font=mc_font(8),
                         wraplength=340, justify="left").pack(anchor="w", pady=2)

        # Achievements
        for w in self._ach_frame.winfo_children():
            w.destroy()

        achievements = profile.get("achievements", [])
        if not achievements:
            tk.Label(self._ach_frame, text="Sin logros todavía. ¡Juega para desbloquearlos!",
                     fg=Colors.GRAY_TEXT, bg=Colors.PANEL_DARK, font=mc_font(8)).pack(anchor="w")
        else:
            for ach in achievements[:6]:  # Show max 6
                row_f = tk.Frame(self._ach_frame, bg=Colors.DARK_BUTTON,
                                 highlightthickness=1, highlightbackground=Colors.PANEL_BORDER)
                row_f.pack(fill="x", pady=2)
                icon = ach.get("icon", "🏆")
                name = ach.get("name", "Logro")
                desc = ach.get("description", "")
                server = ach.get("server_name", "")
                tk.Label(row_f, text=f"  {icon}  {name}", fg=Colors.YELLOW,
                         bg=Colors.DARK_BUTTON, font=mc_font(9, bold=True),
                         anchor="w").pack(anchor="w", padx=8, pady=(4, 1))
                if desc:
                    tk.Label(row_f, text=f"     {desc}", fg=Colors.GRAY_TEXT,
                             bg=Colors.DARK_BUTTON, font=mc_font(8)).pack(anchor="w", padx=8, pady=(0, 2))
                if server:
                    tk.Label(row_f, text=f"     📍 {server}", fg="#888888",
                             bg=Colors.DARK_BUTTON, font=mc_font(7)).pack(anchor="w", padx=8, pady=(0, 4))

        self._content.pack(fill="both", expand=True)

    def _show_leaderboard(self):
        for w in self._lb_frame.winfo_children():
            w.destroy()

        if not self._leaderboard:
            tk.Label(self._lb_frame, text="Sin datos del servidor.", fg=Colors.GRAY_TEXT,
                     bg=Colors.PANEL_DARK, font=mc_font(8)).pack()
            return

        # Header
        header_f = tk.Frame(self._lb_frame, bg=Colors.DARK_BUTTON)
        header_f.pack(fill="x", pady=(0, 2))
        for text, w in [("#", 3), ("Jugador", 16), ("Kills", 7), ("K/D", 7), ("Horas", 7)]:
            tk.Label(header_f, text=text, fg=Colors.YELLOW, bg=Colors.DARK_BUTTON,
                     font=mc_font(8, bold=True), width=w, anchor="w").pack(side="left", padx=2)

        current_user = config.get("username") or ""
        for entry in self._leaderboard[:10]:
            is_me = entry["username"] == current_user
            bg = "#1a3a1a" if is_me else Colors.PANEL_DARK
            row_f = tk.Frame(self._lb_frame, bg=bg)
            row_f.pack(fill="x", pady=1)
            for text, w in [
                (str(entry["rank"]), 3),
                (entry["username"], 16),
                (str(entry["kills"]), 7),
                (str(entry["kd_ratio"]), 7),
                (str(entry["playtime_hours"]), 7),
            ]:
                fg = Colors.PREMIUM_GREEN if is_me else Colors.WHITE
                tk.Label(row_f, text=text, fg=fg, bg=bg,
                         font=mc_font(8, bold=is_me), width=w, anchor="w").pack(side="left", padx=2)

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _close(self):
        self.place_forget()
        self.destroy()
        if self.on_close:
            self.on_close()
