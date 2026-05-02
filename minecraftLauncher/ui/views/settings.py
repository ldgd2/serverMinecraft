import tkinter as tk
from tkinter import filedialog
import ctypes
import os

from config.manager import config
from ui.theme import Colors, Assets, mc_font
from ui.widgets import (
    PanoramaBackground, MinecraftButton, MinecraftLabel, 
    MinecraftInput, MinecraftSlider, MinecraftPanel
)
from PIL import Image

def _load_gui_sprite(path, size):
    if path and os.path.exists(path):
        try:
            return Image.open(path).convert("RGBA").resize(size, Image.NEAREST)
        except Exception:
            pass
    return None

class MEMORYSTATUSEX(ctypes.Structure):
    _fields_ = [
        ("dwLength", ctypes.c_ulong),
        ("dwMemoryLoad", ctypes.c_ulong),
        ("ullTotalPhys", ctypes.c_ulonglong),
        ("ullAvailPhys", ctypes.c_ulonglong),
        ("ullTotalPageFile", ctypes.c_ulonglong),
        ("ullAvailPageFile", ctypes.c_ulonglong),
        ("ullTotalVirtual", ctypes.c_ulonglong),
        ("ullAvailVirtual", ctypes.c_ulonglong),
        ("sullAvailExtendedPhys", ctypes.c_ulonglong),
    ]

def get_total_ram_mb():
    try:
        stat = MEMORYSTATUSEX()
        stat.dwLength = ctypes.sizeof(stat)
        ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(stat))
        return stat.ullTotalPhys // (1024 * 1024)
    except:
        return 16384

class SettingsRow(tk.Frame):
    def __init__(self, master, title, desc, value, browse_type=None, **kwargs):
        super().__init__(master, bg=Colors.PANEL_DARK, **kwargs)
        self.browse_type = browse_type
        
        lbl_frame = tk.Frame(self, bg=Colors.PANEL_DARK)
        lbl_frame.pack(side="top", fill="x", pady=(0, 5))
        
        title_lbl = tk.Label(lbl_frame, text=title, font=mc_font(12, bold=True), fg=Colors.WHITE, bg=Colors.PANEL_DARK, anchor="w")
        title_lbl.pack(side="top", fill="x")
        
        if desc:
            desc_lbl = tk.Label(lbl_frame, text=desc, font=mc_font(10), fg=Colors.GRAY_TEXT, bg=Colors.PANEL_DARK, anchor="w")
            desc_lbl.pack(side="top", fill="x")
            
        input_frame = tk.Frame(self, bg=Colors.PANEL_DARK)
        input_frame.pack(side="top", fill="x")
        
        self.input_field = MinecraftInput(input_frame, width=300, height=36, font_size=12)
        if value is not None:
            self.input_field.set(str(value))
        self.input_field.pack(side="left", fill="x", expand=True)
        
        if browse_type:
            btn = MinecraftButton(input_frame, text="Examinar...", width=100, height=36, font_size=10, command=self.browse)
            btn.pack(side="left", padx=(10, 0))
            
    def browse(self):
        curr = self.input_field.get()
        if self.browse_type == "directory":
            init_dir = curr if curr and os.path.exists(curr) else "."
            path = filedialog.askdirectory(initialdir=init_dir)
            if path:
                self.input_field.set(path)
        elif self.browse_type == "file":
            init_dir = os.path.dirname(curr) if curr and os.path.exists(curr) else "."
            path = filedialog.askopenfilename(initialdir=init_dir)
            if path:
                self.input_field.set(path)
                
    def get(self):
        return self.input_field.get()
        
    def set(self, val):
        self.input_field.set(val)

class SettingsView(tk.Frame):
    def __init__(self, master, app=None, **kwargs):
        super().__init__(master, bg=Colors.DARK, **kwargs)
        self.app = app
        
        # 1. Background (Dark Transparent Panorama)
        self.bg = PanoramaBackground(self, overlay_alpha=210, bg=Colors.DARK)
        self.bg.place(relx=0, rely=0, relwidth=1, relheight=1)
        
        # 2. Main Title
        self.title_lbl = MinecraftLabel(self.bg, text="Opciones", size=24, color=Colors.WHITE, shadow=True)
        self.title_lbl.place(relx=0.5, y=30, anchor="n")
        
        # 3. Split Layout Container (Bedrock inspired layout)
        self.main_panel = MinecraftPanel(self.bg)
        self.main_panel.place(relx=0.1, rely=0.15, relwidth=0.8, relheight=0.7)
        
        # Left Sidebar for Categories
        self.sidebar = tk.Frame(self.main_panel, bg=Colors.PANEL_DARK, width=220)
        self.sidebar.pack(side="left", fill="y", padx=(15, 10), pady=15)
        self.sidebar.pack_propagate(False) # keep width
        
        # Vertical Separator
        self.sep = tk.Frame(self.main_panel, bg=Colors.PANEL_BORDER, width=2)
        self.sep.pack(side="left", fill="y", pady=15)
        
        # Right Content Area (Scrollable)
        self.details_container = tk.Frame(self.main_panel, bg=Colors.PANEL_DARK)
        self.details_container.pack(side="left", fill="both", expand=True, padx=(15, 5), pady=15)
        
        self.canvas = tk.Canvas(self.details_container, bg=Colors.PANEL_DARK, highlightthickness=0)
        self.scrollbar = tk.Scrollbar(self.details_container, orient="vertical", command=self.canvas.yview)
        self.details_area = tk.Frame(self.canvas, bg=Colors.PANEL_DARK)
        
        self.scrollable_window = self.canvas.create_window((0, 0), window=self.details_area, anchor="nw")
        
        def configure_details(event):
            self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        self.details_area.bind("<Configure>", configure_details)
        
        def configure_canvas(event):
            self.canvas.itemconfig(self.scrollable_window, width=event.width)
        self.canvas.bind("<Configure>", configure_canvas)
        
        def _on_mousewheel(event):
            # Safe binding context guard
            if str(event.widget).startswith(str(self.details_container)):
                self.canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        self.canvas.bind_all("<MouseWheel>", _on_mousewheel)
        
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        
        self.scrollbar.pack(side="right", fill="y")
        self.canvas.pack(side="left", fill="both", expand=True, padx=(0, 10))
        
        self.tabs = {}
        self.inputs = {}
        self.toggles = {}
        self.sidebar_btns = {}
        self.current_tab = None
        
        self._build_sidebar()
        self._build_general_tab()
        self._build_java_tab()
        self._build_avanzado_tab()
        
        # 4. Bottom Controls (Save / Back)
        btn_w = 200
        btn_h = 40
        self.save_btn = MinecraftButton(self.bg, text="Guardar Cambios", width=btn_w, height=btn_h, command=self.save_settings)
        self.save_btn.place(relx=0.5, rely=0.9, x=-(btn_w//2 + 10), anchor="n")
        
        self.back_btn = MinecraftButton(self.bg, text="Volver al Menú", width=btn_w, height=btn_h, command=self.go_back)
        self.back_btn.place(relx=0.5, rely=0.9, x=(btn_w//2 + 10), anchor="n")
        
        # Start on General tab
        self.switch_tab("general")

    def _build_sidebar(self):
        cat_lbl = tk.Label(self.sidebar, text="Categorías", font=mc_font(12, bold=True), fg=Colors.GRAY_TEXT, bg=Colors.PANEL_DARK, anchor="w")
        cat_lbl.pack(fill="x", pady=(0, 15))
        
        ico_gen = _load_gui_sprite(Assets.ICON_PLAY, (20, 20))
        btn_gen = MinecraftButton(self.sidebar, text="General", width=190, height=36, font_size=11, icon_img=ico_gen, command=lambda: self.switch_tab("general"))
        btn_gen.pack(pady=4)
        self.sidebar_btns["general"] = btn_gen
        
        ico_java = _load_gui_sprite(Assets.ICON_WARN, (20, 20)) # Using warning/setting icon
        btn_java = MinecraftButton(self.sidebar, text="Config. de Java", width=190, height=36, font_size=11, icon_img=ico_java, command=lambda: self.switch_tab("java"))
        btn_java.pack(pady=4)
        self.sidebar_btns["java"] = btn_java

        ico_adv = _load_gui_sprite(Assets.ICON_SEARCH, (20, 20)) 
        btn_adv = MinecraftButton(self.sidebar, text="Avanzado", width=190, height=36, font_size=11, icon_img=ico_adv, command=lambda: self.switch_tab("avanzado"))
        btn_adv.pack(pady=4)
        self.sidebar_btns["avanzado"] = btn_adv

    def _build_general_tab(self):
        frame = tk.Frame(self.details_area, bg=Colors.PANEL_DARK)
        self.tabs["general"] = frame
        
        lbl = MinecraftLabel(frame, text="Ajustes Generales", size=18, color=Colors.WHITE)
        lbl.pack(anchor="w", pady=(0, 25))
        
        acc_type = config.get("account_type", "guest")
        
        if acc_type == "guest":
            self.inputs["username"] = SettingsRow(
                frame, "Nombre de Usuario", "Tu nombre en el juego (Modo Offline)", 
                config.get("username")
            )
            self.inputs["username"].pack(fill="x", pady=10)
        else:
            provider = "Microsoft" if acc_type == "premium" else "Servidor"
            ro_lbl = tk.Label(frame, text=f"Usuario ({provider}): {config.get('username')} (Protegido)", font=mc_font(10), fg=Colors.GRAY_TEXT, bg=Colors.PANEL_DARK, anchor="w")
            ro_lbl.pack(fill="x", pady=10)
        
        self.inputs["minecraft_dir"] = SettingsRow(
            frame, "Directorio del Juego", "Donde se guardan los assets y versiones", 
            config.get("minecraft_dir"), browse_type="directory"
        )
        self.inputs["minecraft_dir"].pack(fill="x", pady=10)
        
        self._create_toggle(frame, "fullscreen", "Forzar Pantalla Completa", "Inicia el juego abarcando completamente tu monitor sin bordes de ventana.")

    def _build_java_tab(self):
        frame = tk.Frame(self.details_area, bg=Colors.PANEL_DARK)
        self.tabs["java"] = frame
        
        lbl = MinecraftLabel(frame, text="Configuración Avanzada", size=18, color=Colors.WHITE)
        lbl.pack(anchor="w", pady=(0, 25))
        
        # RAM Stepper section
        total_mb = get_total_ram_mb()
        max_ram_gb = total_mb // 1024
        if max_ram_gb < 2:
            max_ram_gb = 2
            
        current_ram_mb = int(config.get("ram_mb") or 2048)
        current_ram_gb = current_ram_mb // 1024
        config.set("ram_gb", current_ram_gb)
        
        self._create_stepper(frame, "ram_gb", "Asignación de Memoria RAM", 1, max_ram_gb, 1, "{} GB", "Límite máximo de memoria que el juego puede alcanzar (-Xmx).")
        
        self.inputs["java_path"] = SettingsRow(
            frame, "Ruta de Java", "Deja en blanco para usar el java por defecto del sistema", 
            config.get("java_path"), browse_type="file"
        )
        self.inputs["java_path"].pack(fill="x", pady=10)

        # ── JVM Builder ──
        lbl_jvm = tk.Label(frame, text="Argumentos JVM (Lanzador)", font=mc_font(12, bold=True), fg=Colors.WHITE, bg=Colors.PANEL_DARK, anchor="w")
        lbl_jvm.pack(fill="x", pady=(10, 5))

        self.jvm_mode_var = tk.StringVar(value="manual")
        
        mode_frame = tk.Frame(frame, bg=Colors.PANEL_DARK)
        mode_frame.pack(fill="x", pady=5)
        
        lbl_manual = tk.Label(mode_frame, text="Modo de Lanzamiento: Manual (Personalizado)", font=mc_font(10), fg=Colors.YELLOW, bg=Colors.PANEL_DARK)
        lbl_manual.pack(side="left")

        # Auto Container
        self.jvm_auto_frame = tk.Frame(frame, bg=Colors.PANEL_DARK)
        
        self._create_cycler(self.jvm_auto_frame, "jvm_gc", "Recolector de Basura", 
            {"G1GC": "G1GC (Recomendado)", "ZGC": "ZGC (Baja Latencia)", "Shenandoah": "Shenandoah", "CMS": "CMS (Antiguo)"},
            "Motor interno para liberar memoria. G1GC es el estándar ideal para Minecraft."
        )

        self._create_toggle(self.jvm_auto_frame, "jvm_experimental", "Opciones Experimentales (VM)", "Desbloquea comandos extra de Java que pueden ayudar al rendimiento.")
        
        self._create_stepper(self.jvm_auto_frame, "jvm_g1_new_size", "G1 New Size", 5, 60, 5, "{} %", "Porcentaje de RAM para nuevos objetos. Recomendado: 20. (-XX:G1NewSizePercent)")
        self._create_stepper(self.jvm_auto_frame, "jvm_g1_reserve", "G1 Reserve", 5, 50, 5, "{} %", "Porcentaje de reserva contra pausas largas. Recomendado: 20. (-XX:G1ReservePercent)")
        self._create_stepper(self.jvm_auto_frame, "jvm_max_pause", "Max GC Pause", 10, 200, 10, "{} ms", "Milisegundos máximos permitidos al limpiar la memoria (Optimizar Tirones). (-XX:MaxGCPauseMillis)")
        self._create_stepper(self.jvm_auto_frame, "jvm_g1_heap_region", "G1 Heap Region", 4, 32, 4, "{} MB", "Tamaño de bloque de RAM. Máximo recomendado: 32MB. (-XX:G1HeapRegionSize)")

        # Manual Container
        self.jvm_manual_frame = tk.Frame(frame, bg=Colors.PANEL_DARK)
        self.inputs["jvm_arguments"] = SettingsRow(
            self.jvm_manual_frame, "Argumentos en Crudo", "Ej: -XX:+UseG1GC -Xmx2G", 
            config.get("jvm_arguments")
        )
        self.inputs["jvm_arguments"].pack(fill="x", pady=5)

        self._switch_jvm_mode(self.jvm_mode_var.get())

    def _switch_jvm_mode(self, mode):
        self.jvm_mode_var.set("manual")
        
        self.jvm_auto_frame.pack_forget()
        self.jvm_manual_frame.pack(fill="x", pady=5)
            
        # Refrescar scroll
        self.details_area.update_idletasks()
        if hasattr(self, 'canvas'):
            self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def _create_stepper(self, parent, key, prefix, min_val, max_val, step, format_str, desc=""):
        config.set(key, int(float(config.get(key) or min_val)))
        
        container = tk.Frame(parent, bg=Colors.PANEL_DARK)
        container.pack(fill="x", pady=(8, 0))
        
        val_lbl = []
        
        def update_val(delta):
            new_val = int(float(config.get(key) or min_val)) + delta
            new_val = max(min_val, min(max_val, new_val))
            config.set(key, new_val)
            val_lbl[0].config(text=format_str.format(new_val))
        
        tk.Label(container, text=prefix + ":", font=mc_font(10), fg=Colors.WHITE, bg=Colors.PANEL_DARK, width=22, anchor="w").pack(side="left")
        
        btn_dec = MinecraftButton(container, text="<", width=30, height=30, command=lambda: update_val(-step))
        btn_dec.pack(side="left", padx=5)
        
        lbl = tk.Label(container, text=format_str.format(config.get(key)), font=mc_font(10, bold=True), fg=Colors.YELLOW, bg=Colors.PANEL_DARK, width=10)
        lbl.pack(side="left", padx=5)
        val_lbl.append(lbl)
        
        btn_inc = MinecraftButton(container, text=">", width=30, height=30, command=lambda: update_val(step))
        btn_inc.pack(side="left", padx=5)
        
        if desc:
            tk.Label(parent, text=desc, font=mc_font(9), fg=Colors.GRAY_TEXT, bg=Colors.PANEL_DARK, justify="left").pack(anchor="w", pady=(2, 6), padx=4)

    def _create_toggle(self, parent, key, prefix, desc=""):
        self.toggles[key] = bool(config.get(key))
        btn_wrapper = []
        def click_handler(k=key, p=prefix):
            self._flip_toggle(k, btn_wrapper[0], p)
        btn = MinecraftButton(parent, text=f"{prefix}: {'ACTIVADO' if self.toggles[key] else 'DESACTIVADO'}", width=340, height=36, font_size=11, command=click_handler)
        btn_wrapper.append(btn)
        btn.pack(anchor="w", pady=(8, 0))
        
        if desc:
            lbl = tk.Label(parent, text=desc, font=mc_font(9), fg=Colors.GRAY_TEXT, bg=Colors.PANEL_DARK, justify="left")
            lbl.pack(anchor="w", pady=(2, 6), padx=4)

    def _create_cycler(self, parent, key, prefix, options_dict, desc=""):
        self.cyclers = getattr(self, "cyclers", {})
        current_val = config.get(key)
        
        keys = list(options_dict.keys())
        if not current_val or current_val not in keys:
            current_val = keys[0]
            config.set(key, current_val)
        self.cyclers[key] = current_val
        
        btn_wrapper = []
        def click_handler(k=key, p=prefix, opts=options_dict):
            kys = list(opts.keys())
            idx = kys.index(self.cyclers[k])
            next_idx = (idx + 1) % len(kys)
            self.cyclers[k] = kys[next_idx]
            btn_wrapper[0].set_text(f"{p}: {opts[self.cyclers[k]]}")
            
        btn = MinecraftButton(parent, text=f"{prefix}: {options_dict[current_val]}", width=340, height=36, font_size=11, command=click_handler)
        btn_wrapper.append(btn)
        btn.pack(anchor="w", pady=(8, 0))
        
        if desc:
            lbl = tk.Label(parent, text=desc, font=mc_font(9), fg=Colors.GRAY_TEXT, bg=Colors.PANEL_DARK, justify="left")
            lbl.pack(anchor="w", pady=(2, 6), padx=4)

    def _flip_toggle(self, key, btn, prefix):
        self.toggles[key] = not self.toggles[key]
        btn.set_text(f"{prefix}: {'ACTIVADO' if self.toggles[key] else 'DESACTIVADO'}")

    def _build_avanzado_tab(self):
        frame = tk.Frame(self.details_area, bg=Colors.PANEL_DARK)
        self.tabs["avanzado"] = frame
        
        # Scrollable inner container isn't always needed, but settings is packed here 
        # using grids or packs simply. We will pack components.
        lbl = MinecraftLabel(frame, text="Configuraciones Avanzadas", size=18, color=Colors.WHITE)
        lbl.pack(anchor="w", pady=(0, 15))

        acc_type = config.get("account_type", "guest")

        # Universal
        self._create_toggle(frame, "discord_rpc", "Activar Discord RPC", "Muestra a tus amigos de Discord a qué estás jugando.")
        self._create_toggle(frame, "close_launcher_on_start", "Cerrar Launcher al Iniciar", "Cierra esta ventana al entrar al juego para liberar RAM en tu equipo.")

        if acc_type in ["premium", "server"]:
            auto_lbl = tk.Label(frame, text="Conexión Automática (Al Entrar)", font=mc_font(10, bold=True), fg=Colors.WHITE, bg=Colors.PANEL_DARK, anchor="w")
            auto_lbl.pack(fill="x", pady=(15, 5))
            
            self.inputs["auto_join_ip"] = SettingsRow(frame, "IP del Servidor (Auto-Join)", "Ej: mc.hypixel.net", config.get("auto_join_ip") or "")
            self.inputs["auto_join_ip"].pack(fill="x", pady=5)

        if acc_type == "guest":
            self._create_toggle(frame, "enable_local_skin_server", "Servidor Local de Skins", "Inicia un mini-servidor en tu PC para que te veas con skin jugando offline.")
            self._create_cycler(frame, "skin_variant", "Modelo de Skin", {"classic": "Clásico (Steve)", "slim": "Slim (Alex)"}, "Modifica el grosor de los brazos de tu skin offline.")
        
        if acc_type == "server":
            self._create_toggle(frame, "enable_skin_sync", "Sincronización Skins en Red", "Exclusivo de servidores: fuerza que descargues las skins de todos los jugadores de tu red.")
            
            self.inputs["server_ip"] = SettingsRow(frame, "IP Servidor Skins", "Ej: 192.168.1.5", config.get("server_ip") or "")
            self.inputs["server_ip"].pack(fill="x", pady=5)
            
            self.inputs["api_url"] = SettingsRow(frame, "URL API Skins", "Ej: http://192.168.1.5/api", config.get("api_url") or "")
            self.inputs["api_url"].pack(fill="x", pady=5)
            
            self._create_toggle(frame, "enable_custom_auth", "Autenticación Custom", "Valida tu sesión pirata usango Authlib Injector contra la base de datos del servidor.")
            
            self.inputs["auth_api_url"] = SettingsRow(frame, "URL Auth API", "Ej: http://auth.server.local", config.get("auth_api_url") or "")
            self.inputs["auth_api_url"].pack(fill="x", pady=5)

    def update_ram_label(self, val):
        mb = int(val / 1024) * 1024
        if mb < 1024:
            mb = 1024
        self.ram_lbl.config(text=f"Asignación de RAM: {mb // 1024} GB")

    def switch_tab(self, tab_id):
        if self.current_tab and self.current_tab in self.tabs:
            self.tabs[self.current_tab].pack_forget()
            
        for tid, btn in self.sidebar_btns.items():
            if tid == tab_id:
                btn.configure_state(True)
            else:
                btn.configure_state(False)
                
        if tab_id in self.tabs:
            self.tabs[tab_id].pack(fill="both", expand=True)
            self.current_tab = tab_id

    def save_settings(self):
        try:
            if "username" in self.inputs:
                config.set("username", self.inputs["username"].get())
            
            ram_gb = int(config.get("ram_gb", 2))
            config.set("ram_mb", ram_gb * 1024)
            
            config.set("java_path", self.inputs["java_path"].get())
            config.set("jvm_arguments", self.inputs["jvm_arguments"].get())
            config.set("minecraft_dir", self.inputs["minecraft_dir"].get())
            
            # Save Advanced Tab
            for k in ["server_ip", "api_url", "auth_api_url", "auto_join_ip"]:
                if k in self.inputs:
                    config.set(k, self.inputs[k].get())
            for k, v in self.toggles.items():
                config.set(k, v)
                
            if hasattr(self, "jvm_mode_var"):
                config.set("jvm_mode", self.jvm_mode_var.get())
            if hasattr(self, "cyclers"):
                for ck, cv in self.cyclers.items():
                    config.set(ck, cv)
            
            
            self.save_btn.set_text("¡Guardado!")
            self.after(2000, lambda: self.save_btn.set_text("Guardar Cambios"))
        except Exception as e:
            self.save_btn.set_text("Error")
            self.after(2000, lambda: self.save_btn.set_text("Guardar Cambios"))

    def go_back(self):
        if self.app:
            self.app.show_home_view()

    def update_username_from_home(self):
        if "username" in self.inputs:
            self.inputs["username"].set(config.get("username"))
        
    def on_show(self):
        # Allow stopping/starting panorama safely if we wanted
        pass
