"""
Player Profile View — muestra el perfil, estadísticas y logros del jugador autenticado.
Se muestra como panel deslizante desde la pantalla de inicio.
"""
import tkinter as tk
import threading
from PIL import Image, ImageTk
from config.manager import config
from ui.theme import Colors, Assets, mc_font
from core.auth import AuthController


# ─── Helpers ──────────────────────────────────────────────────────────────────

import tkinter as tk
import threading
from PIL import Image, ImageTk
from config.manager import config
from ui.theme import Colors, Assets, mc_font
from core.auth import AuthController
from ui.widgets import MinecraftButton, MinecraftPanel, SkinHead, SectionHeader

class ProfileView(tk.Frame):
    """
    Pantalla completa que muestra el perfil del jugador actual,
    sus estadisticas y logros.
    """

    def __init__(self, master, app=None, **kwargs):
        super().__init__(master, bg=Colors.DARK, **kwargs)
        self.app = app
        self._auth = AuthController()
        self._profile = {}
        self._leaderboard = []
        self._icons = {}

        self._build_ui()

    def _get_icon(self, path, size=(16, 16)):
        if path in self._icons: return self._icons[path]
        try:
            img = Image.open(path).convert("RGBA")
            img = img.resize(size, Image.NEAREST)
            tk_img = ImageTk.PhotoImage(img)
            self._icons[path] = tk_img
            return tk_img
        except: return None

    def _build_ui(self):
        # Header
        header = tk.Frame(self, bg=Colors.PANEL_DARK,
                          highlightthickness=1,
                          highlightbackground=Colors.PANEL_BORDER,
                          height=48)
        header.pack(fill="x")
        header.pack_propagate(False)
        MinecraftButton(header, text="< Volver", width=120, height=34,
                         font_size=10, command=self._go_home).pack(side="left", padx=10, pady=7)
        tk.Label(header, text="Perfil y Logros", fg=Colors.WHITE, bg=Colors.PANEL_DARK,
                 font=mc_font(14)).pack(side="left", padx=20)

        self._body = tk.Frame(self, bg=Colors.DARK)
        self._body.pack(fill="both", expand=True, padx=20, pady=20)

        # Left panel: Player info & Stats
        self._left_panel = MinecraftPanel(self._body, width=320)
        self._left_panel.pack(side="left", fill="y", padx=(0, 20))
        self._left_panel.pack_propagate(False)

        # Right panel: Achievements & Highlights
        self._right_panel = MinecraftPanel(self._body)
        self._right_panel.pack(side="left", fill="both", expand=True)
        self._right_panel.pack_propagate(False)

        # Loading
        self._status_lbl = tk.Label(self._left_panel, text="Cargando perfil...", fg=Colors.GRAY_TEXT, bg=Colors.PANEL_DARK, font=mc_font(12))
        self._status_lbl.pack(expand=True)
        
        # UI elements to update
        self._left_content = tk.Frame(self._left_panel, bg=Colors.PANEL_DARK)
        self._right_content = tk.Frame(self._right_panel, bg=Colors.PANEL_DARK)

    def on_show(self):
        self._load_async()

    def _load_async(self):
        self._status_lbl.pack(expand=True)
        self._left_content.pack_forget()
        self._right_content.pack_forget()

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
        self._left_content.pack(fill="both", expand=True)
        self._right_content.pack(fill="both", expand=True)

        for w in self._left_content.winfo_children(): w.destroy()
        for w in self._right_content.winfo_children(): w.destroy()

        # LEFT PANEL -----------------------------------------------------------
        SectionHeader(self._left_content, text="Información", size=11, bg=Colors.PANEL_DARK).pack(anchor="w", padx=14, pady=(14, 10))

        skin_frame = tk.Frame(self._left_content, bg=Colors.PANEL_DARK)
        skin_frame.pack(fill="x", pady=10)
        
        skin_head = SkinHead(skin_frame, size=112, bg=Colors.PANEL_DARK)
        skin_head.pack(pady=5)
        skin_path = config.get("skin_path") or ""
        import os
        if os.path.exists(skin_path): skin_head.set_skin(skin_path)
        else: skin_head.set_skin(None)

        uname = profile.get("username", config.get("username") or "Jugador")
        tk.Label(self._left_content, text=uname, fg=Colors.WHITE, bg=Colors.PANEL_DARK, font=mc_font(16, bold=True)).pack()

        acct = profile.get("account_type", config.get("auth_type", "nopremium") if isinstance(config.get("auth_type"), str) else "nopremium")
        badge_colors = {"premium": Colors.PREMIUM_GREEN, "nopremium": "#e8a83a", "guest": Colors.GRAY_TEXT}
        tk.Label(self._left_content, text=acct.upper(), fg=Colors.PANEL_DARK, bg=badge_colors.get(acct, Colors.GRAY_TEXT), font=mc_font(8, bold=True), padx=8, pady=3).pack(pady=(6, 14))

        since = profile.get("member_since", "")
        if since:
            tk.Label(self._left_content, text=f"Miembro desde: {since[:10]}", fg=Colors.GRAY_TEXT, bg=Colors.PANEL_DARK, font=mc_font(9)).pack(pady=4)

        tk.Frame(self._left_content, bg=Colors.PANEL_BORDER, height=1).pack(fill="x", padx=14, pady=20)
        SectionHeader(self._left_content, text="Estadísticas Globales", size=11, bg=Colors.PANEL_DARK).pack(anchor="w", padx=14, pady=5)

        stats_f = tk.Frame(self._left_content, bg=Colors.PANEL_DARK)
        stats_f.pack(fill="x", padx=14, pady=10)

        stats = profile.get("stats", {})
        stat_rows = [
            (Assets.ICON_PLAY,   "⏱ Tiempo", stats.get("playtime", "—")),
            (Assets.ICON_KILLS,  "⚔️ Kills",  str(stats.get("kills", 0))),
            (Assets.ICON_WARN,   "💀 Muertes", str(stats.get("deaths", 0))),
            (Assets.ICON_KILLS,  "⚖️ K/D",     str(stats.get("kd_ratio", 0))),
            (Assets.ICON_PLAY,   "🔥 Racha",    str(stats.get("best_kill_streak", 0))),
            (Assets.ICON_BLOCKS, "⛏️ Bloques",  str(stats.get("blocks_broken", 0))),
            (Assets.ICON_BLOCKS, "🧱 Puestos",  str(stats.get("blocks_placed", 0))),
            (Assets.ICON_SEARCH, "🌐 Servers",  str(profile.get("servers_played", 0))),
        ]
        
        for i, (icon, lbl, val) in enumerate(stat_rows):
            row = tk.Frame(stats_f, bg=Colors.PANEL_DARK)
            row.pack(fill="x", pady=6)
            img = self._get_icon(icon, (16,16))
            if img: tk.Label(row, image=img, bg=Colors.PANEL_DARK).pack(side="left")
            tk.Label(row, text=lbl, fg=Colors.GRAY_TEXT, bg=Colors.PANEL_DARK, font=mc_font(10)).pack(side="left", padx=10)
            tk.Label(row, text=val, fg=Colors.WHITE, bg=Colors.PANEL_DARK, font=mc_font(11, bold=True)).pack(side="right")

        # RIGHT PANEL (Achievements + Highlights) ------------------------------
        SectionHeader(self._right_content, text="🏆 Tus Logros Desbloqueados", size=14, bg=Colors.PANEL_DARK).pack(anchor="w", padx=20, pady=(20, 10))

        # Scrollable area
        canvas = tk.Canvas(self._right_content, bg=Colors.PANEL_DARK, highlightthickness=0)
        scroll = tk.Scrollbar(self._right_content, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg=Colors.PANEL_DARK)
        
        scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw", width=self._right_panel.winfo_width() - 50)
        canvas.configure(yscrollcommand=scroll.set)
        
        def on_canvas_resize(e):
            canvas.itemconfig(1, width=e.width)
        canvas.bind("<Configure>", on_canvas_resize)
        
        def _on_mousewheel(e):
            canvas.yview_scroll(int(-1*(e.delta/120)), "units")
            
        canvas.bind("<Enter>", lambda e: canvas.bind_all("<MouseWheel>", _on_mousewheel))
        canvas.bind("<Leave>", lambda e: canvas.unbind_all("<MouseWheel>"))

        scroll.pack(side="right", fill="y", padx=(0, 5), pady=5)
        canvas.pack(side="left", fill="both", expand=True, padx=(20, 0), pady=5)

        achievements = profile.get("achievements", [])
        if not achievements:
            tk.Label(scrollable_frame, text="Aún no tienes logros. ¡Sigue jugando para desbloquearlos!", fg=Colors.GRAY_TEXT, bg=Colors.PANEL_DARK, font=mc_font(11)).pack(pady=30, anchor="w")
        else:
            for ach in achievements:
                ach_f = tk.Frame(scrollable_frame, bg=Colors.DARK_BUTTON, highlightthickness=1, highlightbackground=Colors.PANEL_BORDER)
                ach_f.pack(fill="x", pady=8, padx=(0, 15))
                
                icon_f = tk.Frame(ach_f, bg=Colors.DARK_BUTTON)
                icon_f.pack(side="left", fill="y", padx=15, pady=15)
                
                frame_img = self._get_icon(Assets.FRAME_TASK, (56, 56))
                if frame_img:
                    tk.Label(icon_f, image=frame_img, bg=Colors.DARK_BUTTON).pack()
                
                info_f = tk.Frame(ach_f, bg=Colors.DARK_BUTTON)
                info_f.pack(side="left", fill="both", expand=True, pady=15, padx=5)
                
                tk.Label(info_f, text=ach.get("name", "Logro"), fg=Colors.YELLOW, bg=Colors.DARK_BUTTON, font=mc_font(12, bold=True)).pack(anchor="w")
                tk.Label(info_f, text=ach.get("description", ""), fg=Colors.GRAY_TEXT, bg=Colors.DARK_BUTTON, font=mc_font(10), wraplength=400, justify="left").pack(anchor="w", pady=(4,0))
                
                server = ach.get("server_name", "")
                if server:
                    tk.Label(info_f, text=f"📍 Servidor: {server}", fg="#aaaaaa", bg=Colors.DARK_BUTTON, font=mc_font(9)).pack(anchor="w", pady=(8,0))

        # Highlights Section at the bottom of the scrollable frame
        tk.Frame(scrollable_frame, bg=Colors.PANEL_BORDER, height=1).pack(fill="x", pady=30, padx=(0, 15))
        SectionHeader(scrollable_frame, text="✨ Mejores Jugadas y Eventos Recientes", size=12, bg=Colors.PANEL_DARK).pack(anchor="w", pady=(0, 15))
        
        highlights = profile.get("highlights", [])
        if not highlights:
            tk.Label(scrollable_frame, text="Sin eventos recientes.", fg=Colors.GRAY_TEXT, bg=Colors.PANEL_DARK, font=mc_font(10)).pack(anchor="w")
        else:
            for h in highlights:
                row = tk.Frame(scrollable_frame, bg=Colors.PANEL_DARK)
                row.pack(fill="x", pady=4)
                tk.Label(row, text="🔹", fg=Colors.ACCENT, bg=Colors.PANEL_DARK, font=mc_font(11)).pack(side="left")
                tk.Label(row, text=h, fg=Colors.WHITE, bg=Colors.PANEL_DARK, font=mc_font(10)).pack(side="left", padx=8)
                
        # Margin at bottom
        tk.Frame(scrollable_frame, bg=Colors.PANEL_DARK, height=20).pack()

    def _go_home(self):
        if self.app:
            self.app.show_home_view()
