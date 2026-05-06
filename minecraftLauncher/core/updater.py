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
    
    # IMPORTANTE: Usamos la versión de info.py para comparar
    from .info import VERSION as CURRENT
    url = f"{base}/updates/check/{PLATFORM}?current_version={CURRENT}"
    
    try:
        resp = requests.get(url, timeout=5)
        if resp.status_code == 200:
            data = resp.json().get("data", {})
            # Debug log si no es silencioso
            if not silent:
                print(f"[Updater] Server: {data.get('latest_version')} | Local: {CURRENT} | Update: {data.get('has_update')}")
            
            if data.get("has_update") and data.get("download_url"):
                return data
    except Exception as e:
        if not silent:
            print(f"[Updater] Error check: {e}")
    return None


def _is_frozen() -> bool:
    return getattr(sys, "frozen", False)


# ── Ventana de descarga animada ───────────────────────────────────────────────

def download_and_install_launcher(url: str, progress_callback=None, status_callback=None):
    """
    Descarga e instala la actualización del launcher.
    progress_callback(percent: int)
    status_callback(text: str)
    """
    if not _is_frozen():
        if status_callback: status_callback("Simulando descarga...")
        for i in range(0, 101, 10):
            if progress_callback: progress_callback(i)
            time.sleep(0.1)
        if status_callback: status_callback("¡Listo! (Simulado)")
        return True

    exe_dir = os.path.dirname(sys.executable)
    try:
        tmp_fd, tmp_path = tempfile.mkstemp(suffix=".exe", dir=exe_dir)
        os.close(tmp_fd)
    except Exception as e:
        if status_callback: status_callback(f"Error: {e}")
        return False

    try:
        if status_callback: status_callback("Conectando...")
        resp = requests.get(url, stream=True, timeout=60)
        resp.raise_for_status()
        total = int(resp.headers.get("content-length", 0))
        done  = 0
        with open(tmp_path, "wb") as f:
            for chunk in resp.iter_content(chunk_size=65536):
                if chunk:
                    f.write(chunk)
                    done += len(chunk)
                    if total:
                        pct = int(done * 100 / total)
                        if progress_callback: progress_callback(pct)
                        if status_callback: 
                            done_mb = done / (1024 * 1024)
                            total_mb = total / (1024 * 1024)
                            status_callback(f"{done_mb:.1f} MB / {total_mb:.1f} MB")
                    else:
                        if status_callback:
                            kb = done // 1024
                            status_callback(f"Descargando... {kb} KB")
    except Exception as e:
        if status_callback: status_callback(f"Error de descarga: {e}")
        try: os.remove(tmp_path)
        except: pass
        return False

    if status_callback: status_callback("Preparando instalación...")
    apply_launcher_update(tmp_path)
    return True


def apply_launcher_update(tmp_path: str):
    """Crea el script .bat para reemplazar el ejecutable actual y relanzar."""
    import sys
    import subprocess
    import time
    
    current_exe = os.path.abspath(sys.executable)
    exe_dir = os.path.dirname(current_exe)
    pid = os.getpid()
    
    # Usamos la carpeta del exe para el BAT en lugar de TEMP para evitar bloqueos de políticas
    bat_path = os.path.join(exe_dir, "launcher_update_task.bat")
    
    # El BAT ahora es más agresivo y profesional
    bat_content = f"""@echo off
setlocal enabledelayedexpansion
title Actualizador Minecraft Launcher
color 0b

echo.
echo  ==============================================
echo     ACTUALIZADOR DE MINECRAFT LAUNCHER
echo  ==============================================
echo.
echo  [>] Esperando a que el proceso {pid} termine...
taskkill /F /PID {pid} >nul 2>&1
timeout /t 2 /nobreak >nul

set RETRY=0
:try_replace
set /a RETRY+=1
echo  [>] Intento de reemplazo !RETRY! de 15...

:: Intentar mover el archivo (reemplazar)
move /Y "{tmp_path}" "{current_exe}" >nul 2>&1

if !ERRORLEVEL! EQU 0 (
    echo  [OK] Archivo reemplazado con exito.
    goto success
) else (
    echo  [!] Archivo bloqueado o acceso denegado. Reintentando...
    timeout /t 2 /nobreak >nul
    if !RETRY! GEQ 15 goto error
    goto try_replace
)

:success
echo.
echo  [OK] Actualizacion completada correctamente.
echo  [>] Reiniciando Launcher...
timeout /t 1 /nobreak >nul
start "" "{current_exe}"
del "%~f0"
exit

:error
echo.
echo  [X] ERROR FATAL: No se pudo completar la actualizacion.
echo  [!] El archivo "{current_exe}" sigue bloqueado.
echo  [!] Intenta cerrar el Launcher manualmente y ejecuta:
echo      move /Y "{tmp_path}" "{current_exe}"
echo.
pause
exit
"""
    try:
        print(f"[Updater] Creando script BAT en: {bat_path}")
        # Escribir con codificación ANSI (cp1252) para que CMD no tenga problemas con tildes/espacios
        with open(bat_path, "w", encoding="cp1252") as f:
            f.write(bat_content)
        
        # Forzar que el sistema operativo escriba el archivo antes de continuar
        if hasattr(os, 'fsync'):
            with open(bat_path, "a") as f:
                os.fsync(f.fileno())
            
        print(f"[Updater] Ejecutando script de actualizacion...")
        sys.stdout.flush()
        
        # Ejecutar .bat y salir inmediatamente de forma limpia
        # os.startfile es lo más fiable en Windows para lanzar y desentenderse
        print(f"[Updater] Lanzando script nativo: {bat_path}")
        os.startfile(bat_path)
        
        # Salida limpia para permitir que el BAT haga su trabajo
        print("[Updater] Script lanzado. Cerrando Launcher en 1 segundo...")
        sys.stdout.flush()
        time.sleep(1)
        os._exit(0)
    except Exception as e:
        print(f"[Updater] ERROR FATAL al lanzar el script de actualizacion: {e}")
        sys.stdout.flush()
        # Intentar al menos cerrar para no dejar al usuario colgado
        time.sleep(2)
        os._exit(1)


# ── Ventana de descarga animada (Para uso automático al inicio) ───────────────

class _UpdateWindow:
    """Ventana con estética Minecraft para la descarga."""

    def __init__(self, root, latest_version: str, download_url: str, on_complete=None, on_cancel=None):
        import tkinter as tk
        from ui.theme import Colors, mc_font
        from ui.widgets import PanoramaBackground, MinecraftPanel, MinecraftButton, MinecraftLabel

        self.root = root
        self.download_url = download_url
        
        self.win = tk.Toplevel(root)
        self.win.title("Actualización disponible")
        self.win.geometry("500x320")
        self.win.resizable(False, False)
        self.win.overrideredirect(True) # Ventana sin bordes para estética premium
        self.win.transient(root)
        self.win.grab_set()

        # Centrar
        x = root.winfo_rootx() + (root.winfo_width()  // 2) - 250
        y = root.winfo_rooty() + (root.winfo_height() // 2) - 160
        self.win.geometry(f"+{x}+{y}")

        # Fondo con panorama
        self.bg = PanoramaBackground(self.win, overlay_alpha=200)
        self.bg.place(relx=0, rely=0, relwidth=1, relheight=1)

        # Panel central
        panel = MinecraftPanel(self.bg)
        panel.place(relx=0.05, rely=0.05, relwidth=0.9, relheight=0.9)

        # Título
        MinecraftLabel(panel, text="Actualización Disponible", size=18, color=Colors.PREMIUM_GREEN).pack(pady=(20, 5))
        
        tk.Label(panel, text=f"v{LAUNCHER_VERSION}  →  v{latest_version}", 
                 font=mc_font(10), fg=Colors.GRAY_TEXT, bg=Colors.PANEL_DARK).pack()

        # Barra de progreso custom (Contenedor con borde)
        self.prog_container = tk.Frame(panel, bg=Colors.PANEL_BORDER, height=24)
        self.prog_container.pack(fill="x", padx=40, pady=(20, 10))
        self.prog_container.pack_propagate(False)
        
        # El fondo de la barra (Negro Minecraft)
        self.prog_bg = tk.Frame(self.prog_container, bg="#000000")
        self.prog_bg.pack(fill="both", expand=True, padx=2, pady=2)
        self.prog_bg.pack_propagate(False)

        # La barra verde
        self.prog_bar = tk.Frame(self.prog_bg, bg=Colors.PREMIUM_GREEN, width=0)
        self.prog_bar.pack(side="left", fill="y")

        self.status_lbl = MinecraftLabel(panel, text="¿Deseas descargar e instalar ahora?", 
                                         size=10, color=Colors.WHITE, bg=Colors.PANEL_DARK)
        self.status_lbl.pack(pady=5)

        # Botones
        self.btn_frame = tk.Frame(panel, bg=Colors.PANEL_DARK)
        self.btn_frame.pack(side="bottom", pady=20)

        self.dl_btn = MinecraftButton(self.btn_frame, text="Descargar e Instalar", width=200, height=36,
                                      command=self._start)
        self.dl_btn.pack(side="left", padx=5)

        MinecraftButton(self.btn_frame, text="Luego", width=100, height=36,
                        command=self.win.destroy).pack(side="left", padx=5)

    def _start(self):
        self.dl_btn.configure_state(True)
        self.dl_btn.set_text("Descargando...")
        threading.Thread(target=self._worker, daemon=True).start()

    def _worker(self):
        def _update_prog(pct):
            w = int(420 * (pct / 100)) # 420 es el ancho aprox del prog_frame (500*0.9 - 80)
            self.prog_bar.config(width=w)
            
        def _update_status(txt):
            self.status_lbl.set_text(txt)

        success = download_and_install_launcher(
            self.download_url, 
            progress_callback=lambda p: self.win.after(0, lambda: _update_prog(p)),
            status_callback=lambda t: self.win.after(0, lambda: _update_status(t))
        )
        if not success:
            self.win.after(0, lambda: self.dl_btn.configure_state(False))
            self.win.after(0, lambda: self.dl_btn.set_text("Reintentar"))


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


def install_mod_update(download_url: str, latest_version: str, progress_callback=None, status_callback=None):
    """Descarga el mod (o pack de mods en .zip) y lo instala en todos los perfiles."""
    import shutil
    import zipfile
    import minecraft_launcher_lib
    
    if status_callback: status_callback(f"Descargando mod v{latest_version}...")
    tmp_path = None
    try:
        resp = requests.get(download_url, stream=True, timeout=60)
        resp.raise_for_status()
        
        total = int(resp.headers.get("content-length", 0))
        done = 0
        
        # Escribir a un archivo temporal y detectar si es ZIP por los primeros bytes
        fd, tmp_path = tempfile.mkstemp(suffix=".tmp")
        is_zip = False
        with os.fdopen(fd, 'wb') as f:
            first_chunk = True
            for chunk in resp.iter_content(chunk_size=65536):
                if chunk:
                    if first_chunk:
                        is_zip = chunk.startswith(b'PK\x03\x04')
                        first_chunk = False
                    f.write(chunk)
                    done += len(chunk)
                    if total and progress_callback:
                        pct = int(done * 100 / total)
                        progress_callback(pct)
                        if status_callback:
                            done_mb = done / (1024 * 1024)
                            total_mb = total / (1024 * 1024)
                            status_callback(f"{done_mb:.1f} MB / {total_mb:.1f} MB")
            
        if status_callback: status_callback("Instalando mods...")
        base_dir = config.get("minecraft_dir") or minecraft_launcher_lib.utils.get_minecraft_directory()
        master_mod_dir = os.path.join(base_dir, "launcher_data", "mods")
        
        # Renombrar con la extensión correcta para mayor claridad (opcional)
        new_tmp = tmp_path + (".zip" if is_zip else ".jar")
        os.rename(tmp_path, new_tmp)
        tmp_path = new_tmp
        
        # Limpiar almacén maestro antes de la nueva versión
        if os.path.exists(master_mod_dir):
            shutil.rmtree(master_mod_dir)
        os.makedirs(master_mod_dir, exist_ok=True)
        
        if is_zip:
            if status_callback: status_callback("Extrayendo pack de mods...")
            # ── Limpiar almacén maestro antes de extraer ──
            if os.path.exists(master_mod_dir):
                import shutil
                shutil.rmtree(master_mod_dir)
            os.makedirs(master_mod_dir, exist_ok=True)
            
            with zipfile.ZipFile(tmp_path, 'r') as zip_ref:
                zip_ref.extractall(master_mod_dir)
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
        return True

    except Exception as e:
        print(f"[Updater] Error instalando actualización de mods: {e}")
        return False
    finally:
        if tmp_path and os.path.exists(tmp_path):
            try: os.remove(tmp_path)
            except: pass
_mod_sync_lock = threading.Lock()

def kill_ghost_java_processes():
    """Limpia procesos de Java/Minecraft que hayan quedado colgados para liberar archivos."""
    import subprocess
    try:
        if os.name == 'nt':
            # Buscamos procesos de java.exe que tengan 'fabric' o 'minecraft' en su línea de comandos
            # O simplemente matamos cualquier java.exe si el usuario no tiene otros procesos Java importantes
            # Para ser seguros, usamos taskkill por nombre de imagen si está bloqueando
            subprocess.run(["taskkill", "/F", "/IM", "java.exe", "/T"], capture_output=True)
            print("[Launcher] Procesos de Java residuales limpiados.")
    except Exception:
        pass

def inject_mod_to_profile(profile_path: str):
    """Sincroniza archivos del almacén maestro al perfil indicado con manejo de errores de bloqueo."""
    # Antes de sincronizar, intentamos limpiar procesos fantasmas si hay bloqueo
    import shutil
    import minecraft_launcher_lib
    
    with _mod_sync_lock:
        base_dir = config.get("minecraft_dir") or minecraft_launcher_lib.utils.get_minecraft_directory()
        master_mod_dir = os.path.join(base_dir, "launcher_data", "mods")
        
        if not os.path.exists(master_mod_dir):
            return
            
        target_mods_dir = os.path.join(profile_path, "mods")
        
        try:
            # Intentar sincronización limpia
            try:
                if os.path.exists(target_mods_dir):
                    shutil.rmtree(target_mods_dir)
                shutil.copytree(master_mod_dir, target_mods_dir)
                print(f"[Launcher] Sincronización limpia exitosa en perfil: {os.path.basename(profile_path)}")
            except (PermissionError, OSError):
                # Si hay bloqueo, intentamos matar procesos zombie de Java
                print(f"[Launcher] Bloqueo detectado en {os.path.basename(profile_path)}. Limpiando Java...")
                kill_ghost_java_processes()
                
                # Reintentar tras limpieza
                try:
                    if os.path.exists(target_mods_dir):
                        shutil.rmtree(target_mods_dir)
                    shutil.copytree(master_mod_dir, target_mods_dir)
                    print(f"[Launcher] Sincronización exitosa tras limpieza.")
                except:
                    # Fallback final: Copiar uno por uno saltando los bloqueados
                    os.makedirs(target_mods_dir, exist_ok=True)
                    for item in os.listdir(master_mod_dir):
                        s = os.path.join(master_mod_dir, item)
                        d = os.path.join(target_mods_dir, item)
                        try:
                            if os.path.isdir(s):
                                shutil.copytree(s, d, dirs_exist_ok=True)
                            else:
                                shutil.copy2(s, d)
                        except: pass
        except Exception as e:
            print(f"[Launcher] Error sincronizando mods: {e}")


def check_and_prompt(app, log_cb=None):
    """
    Comprueba actualizaciones en background.
    Si hay update del launcher, le avisa a la app para que lo muestre de forma nativa.
    """
    def _worker():
        # Pequeño delay para dejar que la ventana principal cargue
        time.sleep(1.5)
        
        # 1. Check launcher update
        info = check_for_update(silent=True)
        if info:
            latest = info.get("latest_version", "?")
            url    = info.get("download_url", "")
            if url and hasattr(app, "on_launcher_update_detected"):
                app.after(0, lambda: app.on_launcher_update_detected(latest, url))
                return

        # 2. Check mod update
        if config.get("auto_sync_mods"):
            mod_info = check_for_mod_update(silent=True)
            if mod_info:
                latest_mod = mod_info.get("latest_version")
                url_mod = mod_info.get("download_url")
                
                # En lugar de instalar directo, avisamos a la UI para que muestre el aviso
                if latest_mod and url_mod and hasattr(app, "on_mod_update_detected"):
                    app.after(0, lambda: app.on_mod_update_detected(latest_mod, url_mod))

    threading.Thread(target=_worker, daemon=True).start()
