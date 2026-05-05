"""
Minecraft Launcher - Downloads View
Tabs: Vanilla | Fabric | Forge  — each with proper APIs and isolated mod profiles.
"""
import tkinter as tk
import threading
import requests

from ui.theme import Colors, mc_font
from ui.widgets import MinecraftButton, MinecraftPanel, MinecraftInput, SectionHeader
from config.manager import config
from core.versions import (
    get_installed_versions,
    get_available_vanilla_versions,
    install_vanilla_version,
    get_available_fabric_versions,
)

TAB_NAMES = ["Vanilla", "Fabric", "Forge"]
TAB_COLORS = {
    "Vanilla": "#1a5c1a",
    "Fabric":  "#1a3a6b",
    "Forge":   "#7a4a1a",
}


class DownloadsView(tk.Frame):

    def __init__(self, master, app=None, on_download_complete=None, **kwargs):
        super().__init__(master, bg=Colors.DARK, **kwargs)
        self.app = app
        self.on_download_complete = on_download_complete
        self._installing = {}
        self._active_tab = "Vanilla"
        self._mc_version_for_fabric = tk.StringVar(value="")
        self._mc_version_for_forge  = tk.StringVar(value="")
        self._build_ui()

    # ── Build ──────────────────────────────────────────────────────────────────

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
        tk.Label(header, text="Versiones de Minecraft", fg=Colors.WHITE, bg=Colors.PANEL_DARK,
                 font=mc_font(14)).pack(side="left", padx=20)
        MinecraftButton(header, text="Actualizar", width=120, height=34,
                         font_size=10, command=self._refresh_active).pack(side="right", padx=10)

        # Category tab bar
        tab_bar = tk.Frame(self, bg=Colors.PANEL_DARK, height=42)
        tab_bar.pack(fill="x")
        tab_bar.pack_propagate(False)
        self._tab_btns = {}
        for name in TAB_NAMES:
            b = MinecraftButton(tab_bar, text=name, width=130, height=36,
                                 font_size=11,
                                 command=lambda n=name: self._switch_tab(n))
            b.pack(side="left", padx=4, pady=3)
            self._tab_btns[name] = b

        # Status bar
        self._status_var = tk.StringVar(value="Selecciona una categoría")
        tk.Label(self, textvariable=self._status_var, fg=Colors.GRAY_TEXT,
                 bg=Colors.DARK, font=mc_font(10)).pack(pady=(4, 0))

        # Filter / options row (changes per tab)
        self._filter_frame = tk.Frame(self, bg=Colors.DARK)
        self._filter_frame.pack(fill="x", padx=20, pady=4)

        # Scrollable list area
        outer = tk.Frame(self, bg=Colors.DARK)
        outer.pack(fill="both", expand=True, padx=20, pady=(0, 10))

        self._canvas = tk.Canvas(outer, bg=Colors.DARK, highlightthickness=0)
        scrollbar = tk.Scrollbar(outer, orient="vertical", command=self._canvas.yview)
        self._canvas.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        self._canvas.pack(side="left", fill="both", expand=True)

        self._list_frame = tk.Frame(self._canvas, bg=Colors.DARK)
        self._cw = self._canvas.create_window((0, 0), window=self._list_frame, anchor="nw")

        self._list_frame.bind("<Configure>",
                               lambda e: self._canvas.configure(scrollregion=self._canvas.bbox("all")))
        self._canvas.bind("<Configure>",
                           lambda e: self._canvas.itemconfig(self._cw, width=e.width))
        self._canvas.bind_all("<MouseWheel>",
                               lambda e: self._canvas.yview_scroll(-1*(e.delta//120), "units"))

        self._switch_tab("Vanilla")

    # ── Tab logic ──────────────────────────────────────────────────────────────

    def _switch_tab(self, name):
        self._active_tab = name
        self._clear_list()
        self._clear_filter()
        self._status_var.set("Cargando...")

        if name == "Vanilla":
            self._build_vanilla_filter()
        elif name == "Fabric":
            self._build_fabric_filter()
        elif name == "Forge":
            self._build_forge_filter()

        self._refresh_active()

    def _clear_list(self):
        for w in self._list_frame.winfo_children():
            w.destroy()

    def _clear_filter(self):
        for w in self._filter_frame.winfo_children():
            w.destroy()

    def _build_vanilla_filter(self):
        tk.Label(self._filter_frame,
                 text="Versiones oficiales de Mojang (únicamente releases).",
                 fg=Colors.GRAY_TEXT, bg=Colors.DARK, font=mc_font(9)).pack(side="left")

    def _build_fabric_filter(self):
        tk.Label(self._filter_frame, text="Versión de MC base:",
                 fg=Colors.GRAY_TEXT, bg=Colors.DARK, font=mc_font(10)).pack(side="left")
        self._fabric_mc_entry = MinecraftInput(
            self._filter_frame, placeholder="ej. 1.21.1", width=130, height=28, font_size=10)
        self._fabric_mc_entry.pack(side="left", padx=6)
        MinecraftButton(self._filter_frame, text="Buscar Fabric", width=150, height=28,
                         font_size=9, command=self._load_fabric).pack(side="left", padx=4)
        if self._mc_version_for_fabric.get():
            self._fabric_mc_entry.set(self._mc_version_for_fabric.get())

    def _build_forge_filter(self):
        tk.Label(self._filter_frame, text="Versión de MC base:",
                 fg=Colors.GRAY_TEXT, bg=Colors.DARK, font=mc_font(10)).pack(side="left")
        self._forge_mc_entry = MinecraftInput(
            self._filter_frame, placeholder="ej. 1.21.1", width=130, height=28, font_size=10)
        self._forge_mc_entry.pack(side="left", padx=6)
        MinecraftButton(self._filter_frame, text="Buscar Forge", width=150, height=28,
                         font_size=9, command=self._load_forge).pack(side="left", padx=4)

    # ── Refresh / Load ─────────────────────────────────────────────────────────

    def _refresh_active(self):
        if self._active_tab == "Vanilla":
            self._load_vanilla()
        elif self._active_tab == "Fabric":
            self._load_fabric()
        elif self._active_tab == "Forge":
            self._load_forge()

    def _load_vanilla(self):
        self._clear_list()
        self._status_var.set("Obteniendo versiones de Mojang...")

        def fetch():
            available = get_available_vanilla_versions()
            installed = set(get_installed_versions())
            self.after(0, lambda: self._populate_list(available, installed, "Vanilla"))

        threading.Thread(target=fetch, daemon=True).start()

    def _load_fabric(self):
        mc_ver = ""
        if hasattr(self, "_fabric_mc_entry"):
            mc_ver = self._fabric_mc_entry.get().strip()

        if not mc_ver:
            # Mostrar instaladas por defecto
            from core.launcher import get_versions_by_profile
            installed = get_versions_by_profile("Fabric")
            if installed:
                self._status_var.set(f"Mostrando {len(installed)} versiones instaladas.")
                self._populate_list(installed, set(installed), "Fabric")
            else:
                self._status_var.set("Ingresa una versión de Minecraft base para Fabric.")
            return

        self._mc_version_for_fabric.set(mc_ver)
        self._clear_list()
        self._status_var.set(f"Obteniendo loaders Fabric para {mc_ver}...")

        def fetch():
            try:
                url = f"https://meta.fabricmc.net/v2/versions/loader/{mc_ver}"
                resp = requests.get(url, timeout=10)
                resp.raise_for_status()
                data = resp.json()
                versions = [f"fabric-loader-{d['loader']['version']}-{mc_ver}" for d in data]
            except Exception as e:
                versions = []
                self.after(0, lambda: self._status_var.set(f"Error: {e}"))
            installed = set(get_installed_versions())
            self.after(0, lambda: self._populate_list(versions, installed, "Fabric", mc_ver))

        threading.Thread(target=fetch, daemon=True).start()

    def _load_forge(self):
        mc_ver = ""
        if hasattr(self, "_forge_mc_entry"):
            mc_ver = self._forge_mc_entry.get().strip()

        if not mc_ver:
            # Mostrar instaladas por defecto
            from core.launcher import get_versions_by_profile
            installed = get_versions_by_profile("Forge")
            if installed:
                self._status_var.set(f"Mostrando {len(installed)} versiones instaladas.")
                self._populate_forge_list([(v, v) for v in installed], set(installed))
            else:
                self._status_var.set("Ingresa una versión de Minecraft base para Forge.")
            return

        self._mc_version_for_forge.set(mc_ver)
        self._clear_list()
        self._status_var.set(f"Obteniendo versiones de Forge para {mc_ver}...")

        def fetch():
            try:
                url = f"https://files.minecraftforge.net/net/minecraftforge/forge/promotions_slim.json"
                resp = requests.get(url, timeout=12)
                resp.raise_for_status()
                data = resp.json()
                promos = data.get("promos", {})
                versions = []
                for key, forge_ver in promos.items():
                    if key.startswith(mc_ver):
                        label = key.replace("-", " ").title()
                        versions.append((f"{mc_ver}-{forge_ver}", label))
            except Exception as e:
                versions = []
                self.after(0, lambda: self._status_var.set(f"Error: {e}"))
            installed = set(get_installed_versions())
            self.after(0, lambda: self._populate_forge_list(versions, installed))

        threading.Thread(target=fetch, daemon=True).start()

    # ── Populate ───────────────────────────────────────────────────────────────

    def _populate_list(self, versions, installed, loader_type, mc_ver=None):
        self._clear_list()
        if not versions:
            self._status_var.set("No se encontraron versiones.")
            return

        self._status_var.set(f"{len(versions)} versiones · {len([v for v in versions if v in installed])} instaladas")
        color = TAB_COLORS.get(loader_type, Colors.PANEL_DARK)

        for version in versions:
            self._add_version_row(version, version in installed, loader_type, mc_ver, color)

    def _populate_forge_list(self, versions, installed):
        self._clear_list()
        if not versions:
            self._status_var.set("No se encontraron versiones de Forge.")
            return
        self._status_var.set(f"{len(versions)} versiones de Forge disponibles")
        color = TAB_COLORS["Forge"]
        for version_id, label in versions:
            self._add_version_row(version_id, version_id in installed, "Forge", None, color, display=label)

    def _add_version_row(self, version_id, is_installed, loader_type, mc_ver, color, display=None):
        row = tk.Frame(self._list_frame, bg=color,
                        highlightthickness=1, highlightbackground=Colors.PANEL_BORDER)
        row.pack(fill="x", pady=2)

        # Left accent bar
        tk.Frame(row, bg=Colors.PANEL_BORDER if not is_installed else Colors.PREMIUM_GREEN,
                  width=4).pack(side="left", fill="y")

        lbl_color = Colors.PREMIUM_GREEN if is_installed else Colors.WHITE
        tk.Label(row, text=display or version_id, fg=lbl_color, bg=color,
                 font=mc_font(10), width=40, anchor="w").pack(side="left", padx=10, pady=7)

        status_text = "[OK] Instalado" if is_installed else ""
        self._prog_vars = getattr(self, "_prog_vars", {})
        prog_var = tk.StringVar(value=status_text)
        self._prog_vars[version_id] = prog_var
        tk.Label(row, textvariable=prog_var,
                 fg=Colors.PREMIUM_GREEN if is_installed else Colors.YELLOW,
                 bg=color, font=mc_font(9), width=24).pack(side="left")

        btn_text = "Reinstalar" if is_installed else "Instalar"
        inst_btn = MinecraftButton(row, text=btn_text, width=110, height=28, font_size=9)
        inst_btn.pack(side="right", padx=10, pady=5)
        inst_btn.bind("<ButtonRelease-1>",
                       lambda e, v=version_id, b=inst_btn, pv=prog_var,
                              lt=loader_type, mcv=mc_ver: self._install(v, b, pv, lt, mcv))

    # ── Install ────────────────────────────────────────────────────────────────

    def _install(self, version_id, btn, prog_var, loader_type, mc_ver):
        if self._installing.get(version_id):
            return
        self._installing[version_id] = True
        btn.configure_state(True)
        prog_var.set("Preparando...")

        def do_install():
            callbacks = {
                "setStatus":   lambda msg: self.after(0, lambda m=msg: prog_var.set(m[:40])),
                "setProgress": lambda cur: None,
                "setMax":      lambda mx: None,
            }
            try:
                if loader_type == "Vanilla":
                    install_vanilla_version(version_id, callbacks)
                elif loader_type == "Fabric":
                    self._install_fabric(version_id, mc_ver, callbacks)
                elif loader_type == "Forge":
                    self._install_forge(version_id, callbacks)
                self.after(0, lambda: self._on_done(version_id, btn, prog_var, True))
            except Exception as e:
                self.after(0, lambda err=str(e): self._on_done(version_id, btn, prog_var, False, err))

        threading.Thread(target=do_install, daemon=True).start()

    def _install_fabric(self, version_id, mc_ver, callbacks):
        import minecraft_launcher_lib
        # version_id = "fabric-loader-{loader}-{mc_ver}"
        # Extract loader version from the string
        parts = version_id.split("-")
        loader_ver = None
        mc_v = mc_ver or config.get("selected_version") or ""
        # fabric-loader-0.16.0-1.21.1 → loader = 0.16.0, mc = last part
        if "fabric-loader-" in version_id:
            rest = version_id.replace("fabric-loader-", "")
            # rest = "0.16.0-1.21.1"
            mc_v = rest.rsplit("-", 3)[-1] if rest.count("-") >= 3 else mc_v
            loader_ver = rest.replace(f"-{mc_v}", "")

        if callbacks and "setStatus" in callbacks:
            callbacks["setStatus"]("Instalando Fabric...")

        minecraft_launcher_lib.fabric.install_fabric(
            minecraft_version=mc_v,
            minecraft_directory=config.get("minecraft_dir"),
            loader_version=loader_ver,
            callback=callbacks,
        )

    def _install_forge(self, version_id, callbacks):
        import minecraft_launcher_lib
        if callbacks and "setStatus" in callbacks:
            callbacks["setStatus"](f"Instalando Forge {version_id}...")
        minecraft_launcher_lib.forge.install_forge_version(
            versionid=version_id,
            path=config.get("minecraft_dir"),
            callback=callbacks,
        )

    def _on_done(self, version_id, btn, prog_var, success, err=""):
        self._installing[version_id] = False
        btn.configure_state(False)
        if success:
            prog_var.set("[OK] Instalado")
            btn.set_text("Reinstalar")
            if self.on_download_complete:
                self.on_download_complete()
        else:
            prog_var.set(f"Error: {err[:36]}")

    def _go_home(self):
        if self.app:
            self.app.show_home_view()
