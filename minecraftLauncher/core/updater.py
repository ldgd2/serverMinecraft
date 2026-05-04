"""
Auto-updater para el Minecraft Launcher.

Flujo:
  1. Consulta /api/v1/updates/check/launcher?current_version=X.Y.Z
  2. Si versión servidor > versión local: muestra ventana animada de descarga
  3. Descarga el .exe a un temporal en la misma carpeta
  4. Crea un .bat que espera a que muera el proceso, reemplaza el exe y relanza
  5. Lanza el .bat y termina

Para uso en PyInstaller: sys.frozen == True cuando está empaquetado.
"""
import os
import sys
import time
import threading
import tempfile
import subprocess
import requests
from config.manager import config

# ── Versión actual (se lee desde core/info.py, el empaquetador la mantiene) ──
PLATFORM = "launcher"

def _read_version_from_info() -> str:
    """Lee VERSION desde core/info.py para que el empaquetador sea la fuente de verdad."""
    try:
        import importlib.util, os
        info_path = os.path.join(os.path.dirname(__file__), "info.py")
        spec = importlib.util.spec_from_file_location("launcher_info", info_path)
        mod  = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return getattr(mod, "VERSION", "1.0.0")
    except Exception:
        return "1.0.0"

LAUNCHER_VERSION = _read_version_from_info()

def get_current_version() -> str:
    return LAUNCHER_VERSION


def _get_api_base() -> str:
    base = (config.get("api_url") or "").rstrip("/")
    if not base:
        ip   = config.get("server_ip")
        port = config.get("server_port") or 8000
        if ip:
            base = f"http://{ip}:{port}/api/v1"
    return base


def _version_tuple(v: str):
    try:
        return tuple(int(x) for x in str(v).strip().split("."))
    except Exception:
        return (0, 0, 0)


def check_for_update(silent: bool = True) -> dict | None:
    """
    Consulta el backend.
    Retorna el dict data{} si hay update disponible, None si no.
    """
    base = _get_api_base()
    if not base:
        return None
    url = f"{base}/updates/check/{PLATFORM}?current_version={LAUNCHER_VERSION}"
    try:
        resp = requests.get(url, timeout=5)
        if resp.status_code == 200:
            data = resp.json().get("data", {})
            if data.get("has_update") and data.get("download_url"):
                return data
    except Exception as e:
        if not silent:
            print(f"[Updater] {e}")
    return None


def _is_frozen() -> bool:
    return getattr(sys, "frozen", False)


# ── Ventana de descarga animada ───────────────────────────────────────────────

class _UpdateWindow:
    """Ventana tkinter con barra de progreso y animación para la descarga."""

    def __init__(self, root, latest_version: str, download_url: str, on_complete, on_cancel):
        import tkinter as tk
        from tkinter import ttk

        self.root         = root
        self.download_url = download_url
        self.on_complete  = on_complete
        self.on_cancel    = on_cancel
        self._cancelled   = False

        win = tk.Toplevel(root)
        self.win = win
        win.title("Actualización disponible")
        win.geometry("460x280")
        win.resizable(False, False)
        win.configure(bg="#1e2028")
        win.transient(root)
        win.grab_set()

        # Centrar
        win.update_idletasks()
        x = root.winfo_rootx() + (root.winfo_width()  // 2) - 230
        y = root.winfo_rooty() + (root.winfo_height() // 2) - 140
        win.geometry(f"+{x}+{y}")

        # ── Header ──
        tk.Label(win, text="⬆  Nueva versión disponible",
                 fg="#7CBF52", bg="#1e2028",
                 font=("Segoe UI", 14, "bold")).pack(pady=(24, 4))

        tk.Label(win,
                 text=f"Versión actual: {LAUNCHER_VERSION}  →  Nueva: {latest_version}",
                 fg="#8B949E", bg="#1e2028",
                 font=("Segoe UI", 10)).pack()

        # ── Barra de progreso ──
        prog_frame = tk.Frame(win, bg="#1e2028")
        prog_frame.pack(fill="x", padx=30, pady=(24, 6))

        style = ttk.Style()
        style.theme_use("default")
        style.configure("MC.Horizontal.TProgressbar",
                         troughcolor="#2d333b",
                         background="#5D8A3C",
                         thickness=18)

        self.progress = ttk.Progressbar(prog_frame, style="MC.Horizontal.TProgressbar",
                                         orient="horizontal", length=400, mode="determinate")
        self.progress.pack(fill="x")

        self.status_label = tk.Label(win, text="Listo para descargar...",
                                     fg="#8B949E", bg="#1e2028",
                                     font=("Segoe UI", 9))
        self.status_label.pack()

        # ── Botones ──
        btn_frame = tk.Frame(win, bg="#1e2028")
        btn_frame.pack(pady=20)

        self.dl_btn = tk.Button(btn_frame,
                                text="Descargar e instalar",
                                bg="#5D8A3C", fg="white",
                                font=("Segoe UI", 10, "bold"),
                                relief="flat", cursor="hand2",
                                padx=18, pady=8,
                                command=self._start_download)
        self.dl_btn.pack(side="left", padx=8)

        tk.Button(btn_frame,
                  text="Más tarde",
                  bg="#2d333b", fg="#8B949E",
                  font=("Segoe UI", 10),
                  relief="flat", cursor="hand2",
                  padx=18, pady=8,
                  command=self._cancel).pack(side="left", padx=8)

    def _set_status(self, text: str):
        self.status_label.config(text=text)
        self.win.update_idletasks()

    def _start_download(self):
        self.dl_btn.config(state="disabled", text="Descargando...")
        threading.Thread(target=self._download_worker, daemon=True).start()

    def _download_worker(self):
        if not _is_frozen():
            # En modo desarrollo simular
            for i in range(0, 101, 5):
                if self._cancelled: return
                self.win.after(0, lambda v=i: self.progress.config(value=v))
                self.win.after(0, lambda v=i: self._set_status(f"Simulando descarga... {v}%"))
                time.sleep(0.05)
            self.win.after(0, lambda: self._set_status("(Modo desarrollo — no se reemplaza el exe)"))
            self.win.after(1500, self.win.destroy)
            return

        # Descarga real
        exe_dir = os.path.dirname(sys.executable)
        try:
            tmp_fd, tmp_path = tempfile.mkstemp(suffix=".exe", dir=exe_dir)
            os.close(tmp_fd)
        except Exception as e:
            self.win.after(0, lambda: self._set_status(f"Error: {e}"))
            return

        try:
            resp = requests.get(self.download_url, stream=True, timeout=60)
            resp.raise_for_status()
            total = int(resp.headers.get("content-length", 0))
            done  = 0
            with open(tmp_path, "wb") as f:
                for chunk in resp.iter_content(chunk_size=65536):
                    if self._cancelled:
                        f.close()
                        os.remove(tmp_path)
                        return
                    if chunk:
                        f.write(chunk)
                        done += len(chunk)
                        if total:
                            pct = int(done * 100 / total)
                            kb  = done // 1024
                            self.win.after(0, lambda p=pct, k=kb: (
                                self.progress.config(value=p),
                                self._set_status(f"Descargando... {k} KB  ({p}%)")
                            ))
        except Exception as e:
            self.win.after(0, lambda: self._set_status(f"Error de descarga: {e}"))
            try: os.remove(tmp_path)
            except: pass
            return

        self.win.after(0, lambda: self._set_status("Instalando actualización..."))
        self.win.after(500, lambda: self._apply(tmp_path))

    def _apply(self, tmp_path: str):
        current_exe = sys.executable
        bat_content = f"""@echo off
timeout /t 2 /nobreak >nul
move /Y "{tmp_path}" "{current_exe}"
start "" "{current_exe}"
del "%~f0"
"""
        bat_path = os.path.join(os.path.dirname(current_exe), "_updater.bat")
        with open(bat_path, "w") as f:
            f.write(bat_content)
        self.win.after(0, lambda: self._set_status("¡Listo! Relanzando..."))
        self.win.after(800, self._relaunch)

    def _relaunch(self):
        bat_path = os.path.join(os.path.dirname(sys.executable), "_updater.bat")
        subprocess.Popen(["cmd.exe", "/c", bat_path],
                         creationflags=subprocess.CREATE_NEW_CONSOLE,
                         close_fds=True)
        time.sleep(0.3)
        sys.exit(0)

    def _cancel(self):
        self._cancelled = True
        if self.on_cancel:
            self.on_cancel()
        self.win.destroy()


# ── API pública ───────────────────────────────────────────────────────────────

def check_for_mod_update(silent: bool = True) -> dict | None:
    """Consulta si hay una actualización del mod cliente."""
    current_mod_version = config.get("minebridge_mod_version", "0.0.0")
    base = _get_api_base()
    if not base:
        return None
    url = f"{base}/updates/check/modclient?current_version={current_mod_version}"
    try:
        resp = requests.get(url, timeout=5)
        if resp.status_code == 200:
            data = resp.json().get("data", {})
            if data.get("has_update") and data.get("download_url"):
                return data
    except Exception as e:
        if not silent:
            print(f"[Updater] Error comprobando mod: {e}")
    return None


def install_mod_update(download_url: str, latest_version: str):
    """Descarga el mod y lo instala en todos los perfiles configurados."""
    import shutil
    import minecraft_launcher_lib
    
    print(f"[Updater] Descargando modclient v{latest_version}...")
    tmp_path = None
    try:
        resp = requests.get(download_url, timeout=60)
        resp.raise_for_status()
        
        fd, tmp_path = tempfile.mkstemp(suffix=".jar")
        with os.fdopen(fd, 'wb') as f:
            f.write(resp.content)
            
        base_dir = config.get("minecraft_dir") or minecraft_launcher_lib.utils.get_minecraft_directory()
        
        # 1. Instalar en todos los perfiles aislados
        profiles_dir = os.path.join(base_dir, "profiles")
        if os.path.exists(profiles_dir):
            for prof in os.listdir(profiles_dir):
                mods_dir = os.path.join(profiles_dir, prof, "mods")
                if os.path.exists(mods_dir):
                    # Borrar versiones anteriores
                    for m in os.listdir(mods_dir):
                        if "minebridge" in m.lower() and m.endswith(".jar"):
                            try: os.remove(os.path.join(mods_dir, m))
                            except: pass
                    # Copiar nueva versión
                    shutil.copy2(tmp_path, os.path.join(mods_dir, "minebridge-client.jar"))
                    print(f"[Updater] Mod instalado en perfil: {prof}")
                    
        # 2. Instalar en el directorio mods global por si acaso
        global_mods = os.path.join(base_dir, "mods")
        os.makedirs(global_mods, exist_ok=True)
        for m in os.listdir(global_mods):
            if "minebridge" in m.lower() and m.endswith(".jar"):
                try: os.remove(os.path.join(global_mods, m))
                except: pass
        shutil.copy2(tmp_path, os.path.join(global_mods, "minebridge-client.jar"))
        
        config.set("minebridge_mod_version", latest_version)
        print(f"[Updater] Modclient actualizado exitosamente a v{latest_version}.")
        
    except Exception as e:
        print(f"[Updater] Error instalando mod: {e}")
    finally:
        if tmp_path and os.path.exists(tmp_path):
            try: os.remove(tmp_path)
            except: pass


def check_and_prompt(root_window=None, log_cb=None):
    """
    Comprueba actualizaciones en background.
    1. Si hay update del modclient, lo descarga e instala en los perfiles silenciosamente.
    2. Si hay update del launcher, abre la ventana animada de descarga.
    Llamar desde main.py después de crear la instancia de LauncherApp.
    """
    def _worker():
        # Check mod update silently first
        mod_info = check_for_mod_update(silent=True)
        if mod_info:
            latest_mod = mod_info.get("latest_version")
            url_mod = mod_info.get("download_url")
            if latest_mod and url_mod:
                install_mod_update(url_mod, latest_mod)

        # Check launcher update
        info = check_for_update(silent=True)
        if not info:
            return
        latest = info.get("latest_version", "?")
        url    = info.get("download_url", "")
        if not url:
            return
        if root_window:
            root_window.after(600, lambda: _open_window(latest, url))

    def _open_window(latest, url):
        _UpdateWindow(root_window, latest, url,
                      on_complete=None,
                      on_cancel=None)

    threading.Thread(target=_worker, daemon=True).start()
