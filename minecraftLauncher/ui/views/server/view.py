import tkinter as tk
from tkinter import ttk, messagebox, filedialog, simpledialog
import threading
import requests
import os
import time
import json
import websocket
from PIL import Image

from config.manager import config
from ui.theme import Colors, mc_font, Assets
from ui.widgets import PanoramaBackground, MinecraftLabel, MinecraftButton, MinecraftPanel, MinecraftInput

def _load_gui_sprite(path, size):
    if path and os.path.exists(path):
        try:
            return Image.open(path).convert("RGBA").resize(size, Image.NEAREST)
        except Exception:
            pass
    return None

class ServerView(tk.Frame):
    def __init__(self, master, app=None, **kwargs):
        super().__init__(master, bg=Colors.DARK, **kwargs)
        self.app = app
        self.servers = []
        self.selected_server = None
        self.ws = None
        self.ws_thread = None
        
        # Cargar Iconos
        s = (16, 16)
        self.ico_refresh = _load_gui_sprite(Assets.ICON_REFRESH, s)
        self.ico_create  = _load_gui_sprite(Assets.ICON_CREATE, s)
        self.ico_start   = _load_gui_sprite(Assets.ICON_START, s)
        self.ico_stop    = _load_gui_sprite(Assets.ICON_STOP, s)
        self.ico_restart = _load_gui_sprite(Assets.ICON_RESTART, s)
        self.ico_tp      = _load_gui_sprite(Assets.ICON_TP, s)
        self.ico_kick    = _load_gui_sprite(Assets.ICON_KICK, s)
        self.ico_ban     = _load_gui_sprite(Assets.ICON_BAN, s)
        self.ico_op      = _load_gui_sprite(Assets.ICON_SETTINGS, s)
        
        self.bg = PanoramaBackground(self, overlay_alpha=230, bg=Colors.DARK)
        self.bg.place(relx=0, rely=0, relwidth=1, relheight=1)
        
        self.title_lbl = MinecraftLabel(self.bg, text="Server", size=24, color=Colors.PREMIUM_GREEN, shadow=True)
        self.title_lbl.place(relx=0.5, y=20, anchor="n")
        
        self.main_panel = MinecraftPanel(self.bg)
        self.main_panel.place(relx=0.05, rely=0.12, relwidth=0.9, relheight=0.75)
        
        self._build_layout()
        
        btn_w = 200
        btn_h = 40
        self.back_btn = MinecraftButton(self.bg, text="Volver al Menú", width=btn_w, height=btn_h, command=self.go_back)
        self.back_btn.place(relx=0.5, rely=0.92, anchor="n")

    def _build_layout(self):
        # Left Panel (List)
        self.left_panel = tk.Frame(self.main_panel, bg=Colors.PANEL_DARK, width=250)
        self.left_panel.pack(side="left", fill="y", padx=10, pady=10)
        self.left_panel.pack_propagate(False)
        
        tk.Label(self.left_panel, text="Servidores", font=mc_font(12, bold=True), fg=Colors.WHITE, bg=Colors.PANEL_DARK).pack(pady=5)
        
        self.server_list_frame = tk.Frame(self.left_panel, bg=Colors.PANEL_DARK)
        self.server_list_frame.pack(fill="both", expand=True)
        
        # New server / refresh buttons
        btn_frame = tk.Frame(self.left_panel, bg=Colors.PANEL_DARK)
        btn_frame.pack(fill="x", pady=5)
        
        MinecraftButton(btn_frame, text="Refrescar", width=110, height=30, font_size=10, icon_img=self.ico_refresh, command=self.load_servers).pack(side="left", padx=2)
        MinecraftButton(btn_frame, text="Crear/Subir", width=110, height=30, font_size=10, icon_img=self.ico_create, command=self.show_create_dialog).pack(side="right", padx=2)
        
        # Right Panel (Details)
        self.right_panel = tk.Frame(self.main_panel, bg=Colors.PANEL_DARK)
        self.right_panel.pack(side="right", fill="both", expand=True, padx=10, pady=10)
        
        self.details_header = tk.Frame(self.right_panel, bg=Colors.PANEL_DARK)
        self.details_header.pack(fill="x", pady=5)
        
        self.server_title = tk.Label(self.details_header, text="Selecciona un servidor", font=mc_font(16, bold=True), fg=Colors.YELLOW, bg=Colors.PANEL_DARK)
        self.server_title.pack(side="left")
        
        self.status_lbl = tk.Label(self.details_header, text="", font=mc_font(12), fg=Colors.GRAY_TEXT, bg=Colors.PANEL_DARK)
        self.status_lbl.pack(side="left", padx=10)
        
        # Action Buttons
        self.actions_frame = tk.Frame(self.right_panel, bg=Colors.PANEL_DARK)
        self.actions_frame.pack(fill="x", pady=5)
        
        self.btn_start = MinecraftButton(self.actions_frame, text="Iniciar", width=100, height=30, font_size=10, icon_img=self.ico_start, command=lambda: self.control_server("start"))
        self.btn_stop = MinecraftButton(self.actions_frame, text="Detener", width=100, height=30, font_size=10, icon_img=self.ico_stop, command=lambda: self.control_server("stop"))
        self.btn_restart = MinecraftButton(self.actions_frame, text="Reiniciar", width=100, height=30, font_size=10, icon_img=self.ico_restart, command=lambda: self.control_server("restart"))
        
        # Notebook for Tabs
        self.notebook = ttk.Notebook(self.right_panel)
        self.notebook.pack(fill="both", expand=True, pady=10)
        
        # Console Tab
        self.tab_console = tk.Frame(self.notebook, bg=Colors.DARK)
        self.notebook.add(self.tab_console, text="Terminal")
        
        self.console_text = tk.Text(self.tab_console, bg="#000000", fg="#CCCCCC", font=("Consolas", 10), state="disabled", wrap="word")
        self.console_text.pack(fill="both", expand=True, padx=5, pady=5)
        
        cmd_frame = tk.Frame(self.tab_console, bg=Colors.DARK)
        cmd_frame.pack(fill="x", padx=5, pady=5)
        self.cmd_input = MinecraftInput(cmd_frame, width=400, height=30, font_size=10)
        self.cmd_input.pack(side="left", fill="x", expand=True)
        self.cmd_input.entry.bind("<Return>", lambda e: self.send_command())
        MinecraftButton(cmd_frame, text="Enviar", width=80, height=30, font_size=10, command=self.send_command).pack(side="right", padx=5)
        
        # Players Tab
        self.tab_players = tk.Frame(self.notebook, bg=Colors.DARK)
        self.notebook.add(self.tab_players, text="Jugadores")
        
        players_controls = tk.Frame(self.tab_players, bg=Colors.DARK)
        players_controls.pack(fill="x", padx=5, pady=5)
        MinecraftButton(players_controls, text="Refrescar Lista", width=150, height=30, font_size=10, icon_img=self.ico_refresh, command=self.load_players).pack(side="left")
        
        self.players_listbox = tk.Listbox(self.tab_players, bg="#111", fg="white", font=mc_font(11), selectbackground=Colors.PREMIUM_GREEN)
        self.players_listbox.pack(fill="both", expand=True, padx=5, pady=5)
        
        player_actions = tk.Frame(self.tab_players, bg=Colors.DARK)
        player_actions.pack(fill="x", padx=5, pady=5)
        MinecraftButton(player_actions, text="Kick", width=80, height=30, font_size=10, icon_img=self.ico_kick, command=lambda: self.player_action("kick")).pack(side="left", padx=2)
        MinecraftButton(player_actions, text="Ban", width=80, height=30, font_size=10, icon_img=self.ico_ban, command=lambda: self.player_action("ban")).pack(side="left", padx=2)
        MinecraftButton(player_actions, text="OP", width=80, height=30, font_size=10, icon_img=self.ico_op, command=lambda: self.player_action("op")).pack(side="left", padx=2)
        MinecraftButton(player_actions, text="De-OP", width=80, height=30, font_size=10, icon_img=self.ico_op, command=lambda: self.player_action("deop")).pack(side="left", padx=2)
        MinecraftButton(player_actions, text="TP a Mí", width=80, height=30, font_size=10, icon_img=self.ico_tp, command=lambda: self.player_action("tp_me")).pack(side="left", padx=2)
        
    def _get_api_headers(self):
        api_key = config.get("admin_api_key", "")
        return {"Authorization": f"Bearer {api_key}"}

    def _get_api_url(self):
        url = config.get("api_url", "http://127.0.0.1:8000/api/v1")
        return url.rstrip("/")

    def check_access(self):
        if not config.get("admin_api_key"):
            messagebox.showerror("Acceso Denegado", "Falta la Admin API Key en Ajustes Avanzados.")
            self.go_back()
            return False
        return True

    def on_show(self):
        if self.check_access():
            self.load_servers()

    def load_servers(self):
        def task():
            try:
                resp = requests.get(f"{self._get_api_url()}/servers/", headers=self._get_api_headers(), timeout=10)
                if resp.status_code == 200:
                    data = resp.json()
                    self.servers = data.get("data", [])
                    self.after(0, self.render_server_list)
                else:
                    self.after(0, lambda: messagebox.showerror("Error", f"Error API: {resp.text}"))
            except Exception as e:
                self.after(0, lambda: messagebox.showerror("Error de Conexión", str(e)))
        threading.Thread(target=task, daemon=True).start()

    def render_server_list(self):
        for w in self.server_list_frame.winfo_children():
            w.destroy()
            
        for srv in self.servers:
            btn = tk.Button(self.server_list_frame, text=f"{srv['name']} ({srv['status']})", 
                            bg=Colors.DARK_BUTTON, fg="white", font=mc_font(10), anchor="w", padx=10, pady=5, bd=0, cursor="hand2")
            btn.pack(fill="x", pady=1)
            btn.bind("<Button-1>", lambda e, s=srv: self.select_server(s))

    def select_server(self, srv):
        self.selected_server = srv
        self.server_title.config(text=srv['name'])
        self.status_lbl.config(text=f"[{srv['status']}]")
        
        self.btn_start.pack_forget()
        self.btn_stop.pack_forget()
        self.btn_restart.pack_forget()
        
        if srv['status'] == "OFFLINE":
            self.btn_start.pack(side="left", padx=5)
        elif srv['status'] == "RUNNING":
            self.btn_stop.pack(side="left", padx=5)
            self.btn_restart.pack(side="left", padx=5)
            
        self.connect_console()
        self.load_players()

    def control_server(self, action):
        if not self.selected_server: return
        def task():
            name = self.selected_server['name']
            try:
                resp = requests.post(f"{self._get_api_url()}/servers/{name}/control/{action}", headers=self._get_api_headers())
                if resp.status_code == 200:
                    self.after(0, lambda: self.load_servers())
            except Exception as e:
                self.after(0, lambda: messagebox.showerror("Error", str(e)))
        threading.Thread(target=task, daemon=True).start()

    def connect_console(self):
        if self.ws:
            self.ws.close()
            self.ws = None
            
        if not self.selected_server or self.selected_server['status'] != "RUNNING":
            self.log_console("\n[!] Servidor apagado o desconectado.\n")
            return
            
        self.console_text.config(state="normal")
        self.console_text.delete(1.0, "end")
        self.console_text.config(state="disabled")
        
        def run_ws():
            url = self._get_api_url().replace("http", "ws")
            ws_url = f"{url}/servers/{self.selected_server['name']}/console"
            
            def on_message(ws, message):
                self.after(0, lambda: self.log_console(message))
            def on_error(ws, error):
                self.after(0, lambda: self.log_console(f"[WS Error] {error}"))
            def on_close(ws, status, msg):
                self.after(0, lambda: self.log_console("[WS] Desconectado."))
                
            self.ws = websocket.WebSocketApp(ws_url, on_message=on_message, on_error=on_error, on_close=on_close, header=[f"Authorization: Bearer {config.get('admin_api_key')}"])
            self.ws.run_forever()
            
        self.ws_thread = threading.Thread(target=run_ws, daemon=True)
        self.ws_thread.start()

    def log_console(self, text):
        self.console_text.config(state="normal")
        self.console_text.insert("end", text + "\n")
        self.console_text.see("end")
        self.console_text.config(state="disabled")

    def send_command(self):
        cmd = self.cmd_input.get()
        if not cmd or not self.selected_server: return
        
        self.cmd_input.set("")
        def task():
            name = self.selected_server['name']
            requests.post(f"{self._get_api_url()}/servers/{name}/command", json={"command": cmd}, headers=self._get_api_headers())
        threading.Thread(target=task, daemon=True).start()

    def load_players(self):
        if not self.selected_server: return
        self.players_listbox.delete(0, "end")
        if self.selected_server['status'] != "RUNNING": return
        
        def task():
            name = self.selected_server['name']
            try:
                resp = requests.get(f"{self._get_api_url()}/servers/{name}/players", headers=self._get_api_headers())
                if resp.status_code == 200:
                    data = resp.json().get("data", {})
                    players = data.get("online_players", [])
                    self.after(0, lambda: self._update_players_ui(players))
            except: pass
        threading.Thread(target=task, daemon=True).start()

    def _update_players_ui(self, players):
        self.players_listbox.delete(0, "end")
        for p in players:
            self.players_listbox.insert("end", p.get("username", "Unknown"))

    def player_action(self, action):
        sel = self.players_listbox.curselection()
        if not sel or not self.selected_server: return
        target = self.players_listbox.get(sel[0])
        name = self.selected_server['name']
        
        def task():
            try:
                headers = self._get_api_headers()
                base = f"{self._get_api_url()}/servers/{name}"
                if action == "kick":
                    requests.post(f"{base}/players/{target}/kick", headers=headers)
                elif action == "ban":
                    requests.post(f"{base}/players/{target}/ban", json={"mode": "username", "reason": "Banned by Admin", "expires": "forever"}, headers=headers)
                elif action == "op":
                    requests.post(f"{base}/players/{target}/op", headers=headers)
                elif action == "deop":
                    requests.post(f"{base}/players/{target}/deop", headers=headers)
                elif action == "tp_me":
                    me = config.get("username")
                    if me:
                        requests.post(f"{base}/teleport", json={"mode": "player_to_player", "username": target, "target_username": me}, headers=headers)
                self.after(1000, self.load_players)
            except: pass
        threading.Thread(target=task, daemon=True).start()

    def show_create_dialog(self):
        # A simple dialog to create a server and optionally upload a map.
        win = tk.Toplevel(self)
        win.title("Crear Servidor / Subir Mapa")
        win.geometry("400x500")
        win.configure(bg=Colors.PANEL_DARK)
        
        tk.Label(win, text="Nombre del Servidor", bg=Colors.PANEL_DARK, fg="white").pack(pady=5)
        name_entry = tk.Entry(win, width=30)
        name_entry.pack()
        
        tk.Label(win, text="Versión (ej. 1.21.1)", bg=Colors.PANEL_DARK, fg="white").pack(pady=5)
        ver_entry = tk.Entry(win, width=30)
        ver_entry.insert(0, "1.21.1")
        ver_entry.pack()
        
        map_path_var = tk.StringVar()
        
        def pick_map():
            path = filedialog.askopenfilename(filetypes=[("ZIP Files", "*.zip")])
            if path: map_path_var.set(path)
            
        tk.Label(win, text="Mundo / Mapa (.zip) (Opcional)", bg=Colors.PANEL_DARK, fg="white").pack(pady=(15,0))
        tk.Label(win, textvariable=map_path_var, bg=Colors.PANEL_DARK, fg=Colors.YELLOW).pack()
        tk.Button(win, text="Seleccionar .zip", command=pick_map).pack(pady=5)
        
        def submit():
            name = name_entry.get().strip()
            ver = ver_entry.get().strip()
            if not name or not ver: return
            map_path = map_path_var.get()
            win.destroy()
            
            def create_task():
                # 1. Create Server via POST /servers/ or /servers/import if map
                try:
                    if map_path:
                        with open(map_path, 'rb') as f:
                            files = {'file': (os.path.basename(map_path), f, 'application/zip')}
                            resp = requests.post(f"{self._get_api_url()}/servers/import", headers=self._get_api_headers(), files=files)
                            if resp.status_code == 200:
                                self.after(0, lambda: messagebox.showinfo("Éxito", "Servidor y mapa importados!"))
                            else:
                                self.after(0, lambda: messagebox.showerror("Error", resp.text))
                    else:
                        payload = {"name": name, "version": ver, "ram_mb": 2048, "port": 0, "online_mode": False, "mod_loader": "VANILLA", "disk_mb": 5000, "max_players": 20}
                        resp = requests.post(f"{self._get_api_url()}/servers/", headers=self._get_api_headers(), json=payload)
                        if resp.status_code == 200:
                            self.after(0, lambda: messagebox.showinfo("Éxito", "Servidor creado!"))
                        else:
                            self.after(0, lambda: messagebox.showerror("Error", resp.text))
                    self.after(0, self.load_servers)
                except Exception as e:
                    self.after(0, lambda: messagebox.showerror("Error", str(e)))
            threading.Thread(target=create_task, daemon=True).start()
            
        tk.Button(win, text="Crear", width=20, bg=Colors.PREMIUM_GREEN, fg="white", command=submit).pack(pady=20)

    def go_back(self):
        if self.ws:
            self.ws.close()
            self.ws = None
        if self.app:
            self.app.show_home_view()
