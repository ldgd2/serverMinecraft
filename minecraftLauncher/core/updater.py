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

# ── Versión actual (se lee desde core/info.py) ──
from .info import VERSION as LAUNCHER_VERSION
PLATFORM = "launcher"

def get_current_version() -> str:
    # Intenta leer de info.py si está disponible (para desarrollo)
    # Si no, usa el valor importado (que PyInstaller incluye en el PYZ)
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
        self._set_status("Iniciando conexión...")
        threading.Thread(target=self._download_worker, daemon=True).start()

    def _download_worker(self):
        try:
            self._do_download()
        except Exception as e:
            import traceback
            traceback.print_exc()
            self.win.after(0, lambda: self._show_error(f"Error fatal: {e}"))

    def _show_error(self, msg: str):
        from tkinter import messagebox
        self._set_status(f"Error: {msg}")
        messagebox.showerror("Error de actualización", msg, parent=self.win)
        self.dl_btn.config(state="normal", text="Reintentar")

    def _do_download(self):
        if not _is_frozen():
            # En modo desarrollo simular
            for i in range(0, 101, 10):
                if self._cancelled: return
                self.win.after(0, lambda v=i: self.progress.config(value=v))
                self.win.after(0, lambda v=i: self._set_status(f"Simulando descarga... {v}%"))
                time.sleep(0.1)
            self.win.after(0, lambda: self._set_status("(Modo desarrollo — simulado)"))
            self.win.after(1000, self.win.destroy)
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
            self.win.after(0, lambda: self._show_error(f"Error de descarga: {e}"))
            try: os.remove(tmp_path)
            except: pass
            return

        self.win.after(0, lambda: self._set_status("Instalando actualización..."))
        self.win.after(500, lambda: self._apply(tmp_path))

    def _apply(self, tmp_path: str):
        import shutil
        
        # Determinar ruta destino: C:/Games/minecraftLauncher/launcher.exe
        # Usamos la unidad del sistema (normalmente C:)
        system_drive = os.environ.get("SystemDrive", "C:")
        target_dir = os.path.join(system_drive, "\\Games", "minecraftLauncher")
        target_exe = os.path.join(target_dir, "launcher.exe")
        
        current_exe = sys.executable
        pid = os.getpid()
        
        try:
            os.makedirs(target_dir, exist_ok=True)
        except:
            pass # Fallback if no permissions to create C:/Games (unlikely on home PC)

        # El .bat espera a que el proceso muera, mueve el temporal a la carpeta Games y relanza
        bat_content = f"""@echo off
title Actualizador Minecraft
echo Finalizando actualizacion...
:wait_process
tasklist /FI "PID eq {pid}" 2>NUL | find /I /N "{pid}">NUL
if "%ERRORLEVEL%"=="0" (
    timeout /t 1 /nobreak >nul
    goto wait_process
)
timeout /t 1 /nobreak >nul

:: Intentar mover al destino final
move /Y "{tmp_path}" "{target_exe}"
if %ERRORLEVEL% NEQ 0 (
    echo [!] No se pudo mover a {target_exe}. Intentando en la ruta original...
    move /Y "{tmp_path}" "{current_exe}"
    set "FINAL_EXE={current_exe}"
) else (
    set "FINAL_EXE={target_exe}"
)

:: Relanzar desde la carpeta correcta para evitar errores de DLL
echo [✓] Relanzando...
start "" "%FINAL_EXE%"
del "%~f0"
"""
        # Guardar .bat en temp para no dejar basura en la carpeta original
        bat_path = os.path.join(tempfile.gettempdir(), "_mc_updater.bat")
        with open(bat_path, "w") as f:
            f.write(bat_content)
            
        self.win.after(0, lambda: self._set_status("¡Listo! Relanzando..."))
        self.win.after(500, lambda: self._relaunch_final(bat_path))

    def _relaunch_final(self, bat_path: str):
        # Usar Popen con CREATE_NEW_CONSOLE para que el .bat siga vivo tras cerrar python
        subprocess.Popen(["cmd.exe", "/c", bat_path], 
                         creationflags=subprocess.CREATE_NEW_CONSOLE if os.name == 'nt' else 0)
        sys.exit(0)

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
    """Descarga el mod (o pack de mods en .zip) y lo instala en todos los perfiles."""
    import shutil
    import zipfile
    import minecraft_launcher_lib
    
    print(f"[Updater] Descargando mod/pack v{latest_version}...")
    tmp_path = None
    try:
        resp = requests.get(download_url, timeout=60)
        resp.raise_for_status()
        
        # Detectar si es zip por la URL o por el contenido
        is_zip = download_url.lower().endswith(".zip") or resp.content.startswith(b'PK\x03\x04')
        
        fd, tmp_path = tempfile.mkstemp(suffix=".zip" if is_zip else ".jar")
        with os.fdopen(fd, 'wb') as f:
            f.write(resp.content)
            
        base_dir = config.get("minecraft_dir") or minecraft_launcher_lib.utils.get_minecraft_directory()
        master_mod_dir = os.path.join(base_dir, "launcher_data", "mods")
        
        # Limpiar almacén maestro antes de la nueva versión
        if os.path.exists(master_mod_dir):
            shutil.rmtree(master_mod_dir)
        os.makedirs(master_mod_dir, exist_ok=True)
        
        if is_zip:
            print("[Updater] Extrayendo pack de mods (.zip)...")
            with zipfile.ZipFile(tmp_path, 'r') as zip_ref:
                # Extraer solo archivos .jar (seguridad y limpieza)
                for member in zip_ref.namelist():
                    if member.lower().endswith(".jar"):
                        zip_ref.extract(member, master_mod_dir)
        else:
            # Es un solo .jar (el mod base)
            shutil.copy2(tmp_path, os.path.join(master_mod_dir, "minebridge-client.jar"))
        
        # ── 2. Instalar/Sincronizar en todos los perfiles existentes ──
        profiles_dir = os.path.join(base_dir, "profiles")
        if os.path.exists(profiles_dir):
            for prof in os.listdir(profiles_dir):
                prof_path = os.path.join(profiles_dir, prof)
                if os.path.isdir(prof_path):
                    inject_mod_to_profile(prof_path)

        config.set("minebridge_mod_version", latest_version)
        print(f"[Updater] Mod/Pack instalado correctamente (v{latest_version})")

    except Exception as e:
        print(f"[Updater] Error instalando actualización de mods: {e}")
    finally:
        if tmp_path and os.path.exists(tmp_path):
            try: os.remove(tmp_path)
            except: pass

def inject_mod_to_profile(profile_path: str):
    """Copia TODOS los mods maestros al perfil indicado."""
    import shutil
    import minecraft_launcher_lib
    
    base_dir = config.get("minecraft_dir") or minecraft_launcher_lib.utils.get_minecraft_directory()
    master_mod_dir = os.path.join(base_dir, "launcher_data", "mods")
    
    if not os.path.exists(master_mod_dir) or not os.listdir(master_mod_dir):
        return
        
    mods_dir = os.path.join(profile_path, "mods")
    os.makedirs(mods_dir, exist_ok=True)
    
    # 1. Limpiar mods previos que sean gestionados por el launcher 
    # (Borramos todos los .jar para asegurar sincronización total con el pack del servidor)
    # Si el usuario quiere mods personales, debería ponerlos en una carpeta aparte o el launcher
    # debería tener una lista blanca. Por ahora, para simplificar: sincronización total.
    for f in os.listdir(mods_dir):
        if f.lower().endswith(".jar"):
            # Opcional: Solo borrar si "minebridge" está en el nombre o si queremos sync total
            # El usuario pidió "distribuirlo", así que asumimos sync de la carpeta mods.
            try: os.remove(os.path.join(mods_dir, f))
            except: pass
            
    # 2. Copiar todos los del almacén maestro
    for mod_file in os.listdir(master_mod_dir):
        if mod_file.lower().endswith(".jar"):
            src = os.path.join(master_mod_dir, mod_file)
            dst = os.path.join(mods_dir, mod_file)
            try:
                shutil.copy2(src, dst)
            except Exception as e:
                print(f"[Updater] Error copiando {mod_file}: {e}")


def check_and_prompt(root_window=None, log_cb=None):
    """
    Comprueba actualizaciones en background.
    1. Si hay update del modclient, lo descarga e instala en los perfiles silenciosamente.
    2. Si hay update del launcher, abre la ventana animada de descarga.
    Llamar desde main.py después de crear la instancia de LauncherApp.
    """
    def _worker():
        # 1. Check launcher update FIRST (it's the most important)
        info = check_for_update(silent=True)
        if info:
            latest = info.get("latest_version", "?")
            url    = info.get("download_url", "")
            if url and root_window:
                # Al toque
                root_window.after(0, lambda: _open_window(latest, url))
                return # Don't check mods if we are updating the whole launcher

        # 2. Check mod update silently
        mod_info = check_for_mod_update(silent=True)
        if mod_info:
            latest_mod = mod_info.get("latest_version")
            url_mod = mod_info.get("download_url")
            if latest_mod and url_mod:
                install_mod_update(url_mod, latest_mod)

    def _open_window(latest, url):
        _UpdateWindow(root_window, latest, url,
                      on_complete=None,
                      on_cancel=None)

    threading.Thread(target=_worker, daemon=True).start()
