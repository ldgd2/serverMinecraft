import os
import re
import sys
import subprocess
import urllib.request
import urllib.error
import json
import mimetypes
import uuid
import zipfile
import requests
import time

# ── Rutas ─────────────────────────────────────────────────────────────
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
LAUNCHER_DIR = os.path.join(ROOT_DIR, 'minecraftLauncher')
APP_DIR = os.path.join(ROOT_DIR, 'appserve')
MOD_DIR = os.path.join(ROOT_DIR, 'mod')
SERVER_ENV = os.path.join(ROOT_DIR, 'server', '.env')

LAUNCHER_INFO = os.path.join(LAUNCHER_DIR, 'core', 'info.py')
LAUNCHER_SPEC = os.path.join(LAUNCHER_DIR, 'main.spec')
LAUNCHER_REQS = os.path.join(LAUNCHER_DIR, 'requirements.txt')
APP_PUBSPEC = os.path.join(APP_DIR, 'pubspec.yaml')

CLIENT_DIR = os.path.join(MOD_DIR, 'clientmod')
SERVER_DIR = os.path.join(MOD_DIR, 'servermod')

_API_CFG_FILE = os.path.join(ROOT_DIR, '.packager_config')

def _load_env_url() -> str:
    host = "0.0.0.0"
    port = "8000"
    if os.path.exists(SERVER_ENV):
        with open(SERVER_ENV, "r", encoding="utf-8") as f:
            for line in f:
                if line.startswith("API_HOST="):
                    host = line.split("=", 1)[1].strip()
                elif line.startswith("API_PORT="):
                    port = line.split("=", 1)[1].strip()
    
    local_url = f"http://127.0.0.1:{port}"

    if host == "0.0.0.0":
        host = "127.0.0.1"
            
    remote_url = f"http://{host}:{port}"
    return remote_url, local_url

def _load_api_config() -> dict:
    remote_url, local_url = _load_env_url()
    cfg = {
        "api_url": remote_url,
        "local_url": local_url
    } # Default from env
    if os.path.exists(_API_CFG_FILE):
        for line in open(_API_CFG_FILE, encoding='utf-8').readlines():
            if '=' in line:
                k, v = line.strip().split('=', 1)
                cfg[k] = v
    
    # Overwrite derived values if explicitly saved
    if cfg.get('target_ip') and cfg.get('target_port'):
        target_ip = cfg['target_ip']
        port = cfg['target_port']
        
        # IP for the packager to connect to the backend
        connect_ip = target_ip if target_ip != "0.0.0.0" else "127.0.0.1"
        cfg['api_url'] = f"http://{connect_ip}:{port}"
        
        # IP to be injected into the mod as "Public/Remote"
        # If 0.0.0.0, we try to find the real IP for the mod, or fallback to 127.0.0.1
        mod_ip = target_ip
        if mod_ip == "0.0.0.0":
            try:
                import urllib.request
                mod_ip = urllib.request.urlopen('https://api.ipify.org', timeout=3).read().decode('utf8')
            except:
                mod_ip = "127.0.0.1"
        
        cfg['mod_public_url'] = f"http://{mod_ip}:{port}"
        cfg['local_url'] = f"http://127.0.0.1:{port}"
        
    return cfg

def configure_packager():
    """Wizard interactivo para configurar el empaquetador."""
    cfg = _load_api_config()
    print("\n  ╔══════════════════════════════════════╗")
    print("  ║      CONFIGURACIÓN DEL EMPAQUETADOR  ║")
    print("  ╚══════════════════════════════════════╝")
    
    # 1. Red y Host
    # Intentar sacar valores actuales para sugerirlos
    current_ip = cfg.get("target_ip") or "0.0.0.0"
    current_port = cfg.get("target_port") or "8000"
    
    print(f"\n  [1] Red y Servidor Objetivo")
    new_ip = input(f"      IP o Dominio del VPS [{current_ip}]: ").strip()
    cfg['target_ip'] = new_ip if new_ip else current_ip
    
    new_port = input(f"      Puerto del Backend [{current_port}]: ").strip()
    cfg['target_port'] = new_port if new_port else current_port
    
    # Recalcular URLs base
    cfg['api_url'] = f"http://{cfg['target_ip']}:{cfg['target_port']}"
    cfg['local_url'] = f"http://127.0.0.1:{cfg['target_port']}"

    # 2. Credenciales
    print(f"\n  [2] Credenciales de Administrador (API)")
    current_user = cfg.get('username') or 'admin'
    new_user = input(f"      Usuario admin [{current_user}]: ").strip()
    cfg['username'] = new_user if new_user else current_user
    
    import getpass
    print("      Introduce la contraseña (deja vacío para no cambiar)")
    new_pass = getpass.getpass(f"      Contraseña para '{cfg['username']}': ").strip()
    if new_pass:
        cfg['password'] = new_pass
        
    # 3. API Key del Mod
    print(f"\n  [3] Firma y Seguridad del Mod")
    current_key = cfg.get('mod_api_key') or 'PENDING'
    print("      Esta es la API Key que el mod usará para hablar con el backend.")
    new_key = input(f"      API Key del Mod [{current_key}]: ").strip()
    cfg['mod_api_key'] = new_key if new_key else current_key
    
    _save_api_config(cfg)
    print("\n  [✓] Configuración base guardada.")

    # 4. Test de Conexión
    print(f"\n  [>] Verificando Conexión con {cfg['api_url']}...")
    try:
        # Test 1: Credenciales Admin
        token = _get_token(cfg)
        print("      [✓] Conexión y Login Admin: OK")
        
        # Test 2: API Key del Mod (Usando la nueva ruta /bridge/test)
        test_url = f"{cfg['api_url']}/api/v1/bridge/test"
        res = requests.get(test_url, headers={"X-API-Key": cfg['mod_api_key']}, timeout=5)
        if res.status_code == 200:
            data = res.json()
            print(f"      [✓] API Key del Mod: OK (Pertenece a: {data.get('user', 'admin')})")
        elif res.status_code == 401:
            print(f"      [X] API Key del Mod: INVÁLIDA (401 Unauthorized)")
        else:
            print(f"      [X] API Key del Mod: Error {res.status_code}")
            
    except Exception as e:
        print(f"      [X] Fallo de conexión: {e}")
        print("      (Asegúrate de que el backend esté corriendo y sea accesible)")

    print("\n  [✓] Proceso de configuración finalizado.")
    return cfg

def _save_api_config(cfg: dict):
    with open(_API_CFG_FILE, 'w', encoding='utf-8') as f:
        for k, v in cfg.items():
            f.write(f"{k}={v}\n")

def _get_api_config() -> dict:
    cfg = _load_api_config()
    changed = False

    if not cfg.get('username'):
        print("\n  ┌─ Credenciales de Administrador ────────────────")
        cfg['username'] = input("  │ Usuario admin: ").strip()
        changed = True

    if not cfg.get('password'):
        import getpass
        print("\n  ┌─ Credenciales de Administrador ────────────────")
        pwd = ''
        while not pwd:
            pwd = getpass.getpass(f"  │ Contraseña para '{cfg.get('username', 'admin')}': ")
            if not pwd:
                print("  │ [!] La contraseña no puede estar vacía.")
        cfg['password'] = pwd
        changed = True

    if not cfg.get('mod_api_key'):
        print("\n  ┌─ Configuración del MOD (MineBridge) ───────────")
        print("  │ Esta es la 'Firma' o API Key que usará el mod")
        print("  │ para reportar logros y estadísticas al backend.")
        cfg['mod_api_key'] = input("  │ API Key del Mod: ").strip()
        changed = True

    if changed:
        save = input("\n  └ ¿Guardar configuración para próximas veces? [s/N]: ").strip().lower()
        if save in ('s', 'si', 'y', 'yes'):
            _save_api_config(cfg)
            print("  [✓] Guardado en .packager_config (ignorado por git)")

    return cfg

def _get_token(cfg: dict) -> str:
    url = f"{cfg['api_url']}/api/v1/auth/login"
    print(f"  POST {url}")
    payload = json.dumps({"username": cfg['username'], "password": cfg['password']}).encode('utf-8')
    req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            resp = json.loads(r.read())
            token = resp.get('access_token') or resp.get('token') or (resp.get('data') or {}).get('access_token') or (resp.get('data') or {}).get('token')
            if not token:
                raise RuntimeError(f"No se encontró token en la respuesta: {resp}")
            return token
    except urllib.error.HTTPError as e:
        body_err = e.read().decode('utf-8')
        # Clear saved password so user is prompted again next run
        if e.code == 401 and os.path.exists(_API_CFG_FILE):
            os.remove(_API_CFG_FILE)
            print("  [!] Credenciales borradas del caché (.packager_config)")
        raise RuntimeError(f"Login falló ({e.code}): {body_err}")

def _upload_binary(cfg: dict, token: str, platform: str, version: str, filepath: str):
    url = f"{cfg['api_url']}/api/v1/updates/upload/{platform}/{version}"
    filename = os.path.basename(filepath)
    file_size = os.path.getsize(filepath)
    boundary = uuid.uuid4().hex
    ctype = mimetypes.guess_type(filepath)[0] or 'application/octet-stream'

    print(f"  [>] Subiendo {filename} ({file_size/1024/1024:.1f} MB)...")

    # Partes fijas del multipart para poder calcular el progreso real
    header = (
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="file"; filename="{filename}"\r\n'
        f"Content-Type: {ctype}\r\n\r\n"
    ).encode('utf-8')
    footer = f"\r\n--{boundary}--\r\n".encode('utf-8')
    total_len = len(header) + file_size + len(footer)

    class StreamingBody:
        def __init__(self, header, file_path, footer, total_size):
            self.header = header
            self.file_path = file_path
            self.file = open(file_path, 'rb')
            self.footer = footer
            self.total_size = total_size
            self.sent = 0
            self.stage = 0 # 0: header, 1: file, 2: footer
            self.last_pct = -1

        def read(self, amt=-1):
            if self.stage == 0:
                self.stage = 1
                self.sent += len(self.header)
                return self.header
            if self.stage == 1:
                chunk = self.file.read(amt if amt > 0 else 65536)
                if not chunk:
                    self.stage = 2
                    self.file.close()
                    return self.read(amt)
                self.sent += len(chunk)
                self._update_progress()
                return chunk
            if self.stage == 2:
                self.stage = 3
                self.sent += len(self.footer)
                return self.footer
            return b""

        def _update_progress(self):
            pct = int((self.sent / self.total_size) * 100)
            if pct != self.last_pct:
                bar = '=' * (pct // 5)
                spaces = ' ' * (20 - (pct // 5))
                print(f"\r      Progreso: [{bar}{spaces}] {pct}%", end="", flush=True)
                self.last_pct = pct

        def __len__(self):
            return self.total_size

    body = StreamingBody(header, filepath, footer, total_len)
    
    req = urllib.request.Request(url, data=body, headers={
        "Authorization": f"Bearer {token}",
        "Content-Type": f"multipart/form-data; boundary={boundary}",
        "Content-Length": str(total_len)
    })
    
    try:
        with urllib.request.urlopen(req, timeout=None) as r:
            resp = json.loads(r.read())
            print() # Salto de línea tras la barra
            if resp.get('status') == 'error':
                print(f"  [X] Error: {resp.get('message')}")
                raise RuntimeError(resp.get('message'))
            return resp
    except Exception as e:
        print(f"\n  [X] Fallo de red: {e}")
        raise

def _force_set_version(cfg: dict, token: str, platform: str, version: str):
    """
    Llama a PUT /api/v1/updates/set/{platform} para que el backend apunte a esta versión.
    Si la versión es la misma que la actual, fuerza el apuntado igualmente
    (garantiza que el server sirve lo que acababas de compilar hoy).
    """
    url = f"{cfg['api_url']}/api/v1/updates/set/{platform}"
    payload = json.dumps({"version": version}).encode('utf-8')
    req = urllib.request.Request(
        url, data=payload,
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        },
        method="PUT"
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            resp = json.loads(r.read())
            print(f"  [✓] {platform} apunta ahora a v{version}: {resp.get('message', 'OK')}")
    except urllib.error.HTTPError as e:
        # Si falla por 404 (versión no existía aún), el upload ya lo registró, ignorar
        body_err = e.read().decode('utf-8')
        print(f"  [!] set/{platform} devolvió {e.code}: {body_err[:120]}")


# --- Versiones Helpers ---
def _bump(version: str, tipo: str) -> str:
    parts = [int(x) for x in version.split('.')]
    if tipo == '1':   parts[0] += 1; parts[1:] = [0] * len(parts[1:])
    elif tipo == '2': parts[1] += 1; parts[2:] = [0] * len(parts[2:])
    elif tipo == '3': parts[-1] += 1
    return '.'.join(str(p) for p in parts)

def _ask_bump(current: str) -> tuple[str, str]:
    print(f"\n  Versión actual: {current}")
    print("  [1] Grande   (X.0.0)")
    print("  [2] Mediana  (x.Y.0)")
    print("  [3] Parche   (x.y.Z)")
    print("  [4] Mantener")
    choice = input("  Selecciona [1-4]: ").strip()
    labels = {'1': 'GRANDE', '2': 'MEDIANA', '3': 'PARCHE', '4': 'MANTENER'}
    if choice not in labels:
        print("  [X] Inválido"); sys.exit(1)
    return _bump(current, choice), labels[choice]

# --- 1. Launcher ---
def _launcher_current_version() -> tuple[str, str]:
    with open(LAUNCHER_INFO, encoding='utf-8') as f:
        content = f.read()
    m = re.search(r"VERSION\s*=\s*'([^']+)'", content)
    if not m: raise RuntimeError(f"[X] No se encontró VERSION en {LAUNCHER_INFO}")
    return m.group(1), content

def build_launcher(cfg: dict, token: str):
    print("\n╔══════════════════════════════════════╗")
    print("║        COMPILAR LAUNCHER             ║")
    print("╚══════════════════════════════════════╝")
    try:
        current, content = _launcher_current_version()
    except Exception as e:
        print(f"  [X] Error: {e}"); return
        
    new_v, label = _ask_bump(current)
    print(f"\n  → {current}  →  {new_v}  [{label}]")
    if input("  ¿Continuar? [s/N]: ").strip().lower() not in ('s', 'si', 'y', 'yes'):
        print("  Cancelado."); return

    if new_v != current:
        with open(LAUNCHER_INFO, 'w', encoding='utf-8') as f:
            f.write(content.replace(f"VERSION = '{current}'", f"VERSION = '{new_v}'"))
        if os.path.exists(LAUNCHER_SPEC):
            with open(LAUNCHER_SPEC, encoding='utf-8') as f:
                spec = f.read()
            with open(LAUNCHER_SPEC, 'w', encoding='utf-8') as f:
                f.write(spec.replace(f"VERSION = '{current}'", f"VERSION = '{new_v}'"))
        print(f"  [✓] core/info.py → VERSION = '{new_v}'")

    print("  [>] Verificando dependencias del launcher...")
    if os.path.exists(LAUNCHER_REQS):
        subprocess.run([sys.executable, "-m", "pip", "install", "-r", LAUNCHER_REQS, "--quiet"], cwd=LAUNCHER_DIR)

    exe_name = f"MinecraftLauncher_v{new_v}.exe"
    print(f"\n  [>] PyInstaller → {exe_name}")
    env = os.environ.copy()
    env["BUILD_VERSION"] = new_v
    proc = subprocess.Popen([sys.executable, "-m", "PyInstaller", LAUNCHER_SPEC, "-y"], cwd=LAUNCHER_DIR, env=env)
    if proc.wait() != 0:
        print("  [X] PyInstaller falló."); sys.exit(1)

    exe_path = os.path.join(LAUNCHER_DIR, 'dist', exe_name)
    if not os.path.exists(exe_path):
        print(f"  [X] No se encontró el exe: {exe_path}"); return

    print("\n  [>] Publicando en el servidor...")
    try:
        _upload_binary(cfg, token, "launcher", new_v, exe_path)
        _force_set_version(cfg, token, "launcher", new_v)
    except Exception as e:
        print(f"  [X] Falló la subida: {e}")

# --- 2. App ---
def _app_current_version() -> tuple[str, int, str]:
    if not os.path.exists(APP_PUBSPEC): raise RuntimeError("[X] No se encontró pubspec.yaml")
    with open(APP_PUBSPEC, encoding='utf-8') as f:
        content = f.read()
    m = re.search(r'^version:\s*(\d+\.\d+\.\d+)\+(\d+)', content, re.MULTILINE)
    if not m: raise RuntimeError(f"[X] No se encontró version en {APP_PUBSPEC}")
    return m.group(1), int(m.group(2)), content

def build_app(cfg: dict, token: str):
    print("\n╔══════════════════════════════════════╗")
    print("║        COMPILAR APP FLUTTER          ║")
    print("╚══════════════════════════════════════╝")
    try:
        current, build_num, content = _app_current_version()
    except Exception as e:
        print(f"  [X] Error: {e}"); return
        
    new_v, label = _ask_bump(current)
    new_build = build_num + 1 if new_v != current else build_num
    print(f"\n  → {current}+{build_num}  →  {new_v}+{new_build}  [{label}]")
    if input("  ¿Continuar? [s/N]: ").strip().lower() not in ('s', 'si', 'y', 'yes'):
        print("  Cancelado."); return

    if new_v != current or new_build != build_num:
        with open(APP_PUBSPEC, 'w', encoding='utf-8') as f:
            f.write(content.replace(f"version: {current}+{build_num}", f"version: {new_v}+{new_build}"))

    print(f"\n  [>] flutter build apk --release")
    proc = subprocess.Popen("flutter build apk --release", cwd=APP_DIR, shell=True)
    if proc.wait() != 0:
        print("  [X] Flutter build falló."); sys.exit(1)

    apk_path = os.path.join(APP_DIR, 'build', 'app', 'outputs', 'flutter-apk', 'app-release.apk')
    if not os.path.exists(apk_path):
        # A veces está en otro lado dependiendo de Flutter config
        apk_path_alt = os.path.join(APP_DIR, 'build', 'app', 'outputs', 'apk', 'release', 'app-release.apk')
        if os.path.exists(apk_path_alt):
            apk_path = apk_path_alt
        else:
            print(f"  [X] No se encontró el APK en {apk_path} ni {apk_path_alt}"); return

    print("\n  [>] Publicando en el servidor...")
    try:
        _upload_binary(cfg, token, "app", new_v, apk_path)
        _force_set_version(cfg, token, "app", new_v)
    except Exception as e:
        print(f"  [X] Falló la subida: {e}")

# --- 3. Mods ---
def _download_jdk21():
    jdk_dir = os.path.join(MOD_DIR, '.jdk21')
    if os.path.exists(jdk_dir):
        return jdk_dir
    print("  [>] Descargando JDK 21 Portable (Temurin)...")
    url = "https://github.com/adoptium/temurin21-binaries/releases/download/jdk-21.0.4+7/OpenJDK21U-jdk_x64_windows_hotspot_21.0.4_7.zip"
    zip_path = os.path.join(MOD_DIR, 'jdk21.zip')
    try:
        urllib.request.urlretrieve(url, zip_path)
        print("  [>] Extrayendo JDK...")
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(jdk_dir)
        os.remove(zip_path)
    except Exception as e:
        print(f"  [X] Error descargando JDK: {e}")
        sys.exit(1)
    return jdk_dir

def _mod_current_version(gradle_file: str) -> tuple[str, str]:
    if not os.path.exists(gradle_file): raise RuntimeError(f"[X] No se encontró {gradle_file}")
    with open(gradle_file, encoding='utf-8') as f:
        content = f.read()
    m = re.search(r'^mod_version=(.+)$', content, re.MULTILINE)
    if not m: raise RuntimeError(f"[X] No se encontró mod_version en {gradle_file}")
    return m.group(1).strip(), content

def build_mods(cfg: dict, token: str):
    print("\n╔══════════════════════════════════════╗")
    print("║        COMPILAR MODS (GRADLE)        ║")
    print("╚══════════════════════════════════════╝")
    
    c_props = os.path.join(CLIENT_DIR, 'gradle.properties')
    s_props = os.path.join(SERVER_DIR, 'gradle.properties')
    mod_config_java = os.path.join(SERVER_DIR, 'src', 'main', 'java', 'com', 'lider', 'minebridge', 'config', 'ModConfig.java')
    
    try:
        current, c_content = _mod_current_version(c_props)
        _, s_content = _mod_current_version(s_props)
    except Exception as e:
        print(f"  [X] Error: {e}"); return

    # --- Inyectar configuración en ModConfig.java ---
    original_java_content = None
    if os.path.exists(mod_config_java):
        print("  [>] Inyectando IP y API Key en ModConfig.java...")
        with open(mod_config_java, 'r', encoding='utf-8') as f:
            original_java_content = f.read()
        
        new_java_content = original_java_content
        # Inyectar ambas URLs para que el mod decida cuál usar
        public_url = cfg.get('mod_public_url', cfg['api_url'])
        new_java_content = new_java_content.replace('private static String backendUrl = "PENDING";', f'private static String backendUrl = "{public_url}";')
        new_java_content = new_java_content.replace('private static String localUrl = "PENDING";', f'private static String localUrl = "{cfg["local_url"]}";')
        new_java_content = new_java_content.replace('private static String apiKey = "PENDING";', f'private static String apiKey = "{cfg["mod_api_key"]}";')
        
        with open(mod_config_java, 'w', encoding='utf-8') as f:
            f.write(new_java_content)
    
    try:
        new_v, label = _ask_bump(current)
        print(f"\n  → {current}  →  {new_v}  [{label}]")
        if input("  ¿Continuar? [s/N]: ").strip().lower() not in ('s', 'si', 'y', 'yes'):
            print("  Cancelado."); return

        if new_v != current:
            with open(c_props, 'w', encoding='utf-8') as f:
                f.write(c_content.replace(f"mod_version={current}", f"mod_version={new_v}"))
            with open(s_props, 'w', encoding='utf-8') as f:
                f.write(s_content.replace(f"mod_version={current}", f"mod_version={new_v}"))
            print(f"  [✓] gradle.properties → mod_version={new_v}")

        # Configurar JDK
        jdk_dir = _download_jdk21()
        java_home = None
        for item in os.listdir(jdk_dir):
            if item.startswith("jdk"):
                java_home = os.path.join(jdk_dir, item)
                break
        if not java_home:
            print("  [X] No se pudo encontrar JAVA_HOME en .jdk21"); sys.exit(1)
            
        env = os.environ.copy()
        env["JAVA_HOME"] = java_home
        env["PATH"] = f"{os.path.join(java_home, 'bin')};{env.get('PATH', '')}"
        env["GRADLE_USER_HOME"] = os.path.join(MOD_DIR, '.gradle_home')

        # Compilar Cliente
        print("\n  [>] Compilando CLIENT MOD...")
        proc_c = subprocess.Popen(["cmd.exe", "/c", "gradlew.bat", "clean", "build"], cwd=CLIENT_DIR, env=env)
        if proc_c.wait() != 0:
            print("  [X] Compilación de CLIENT MOD falló."); sys.exit(1)

        # Compilar Server
        print("\n  [>] Compilando SERVER MOD...")
        proc_s = subprocess.Popen(["cmd.exe", "/c", "gradlew.bat", "clean", "build"], cwd=SERVER_DIR, env=env)
        if proc_s.wait() != 0:
            print("  [X] Compilación de SERVER MOD falló."); sys.exit(1)

        c_jar = os.path.join(CLIENT_DIR, 'build', 'libs', f'minebridge-client-{new_v}.jar')
        s_jar = os.path.join(SERVER_DIR, 'build', 'libs', f'minebridge-server-{new_v}.jar')
        
        # Intentar buscar el jar exacto o el más reciente que no sea -sources o -dev
        def find_jar(directory, pattern):
            libs_dir = os.path.join(directory, 'build', 'libs')
            if not os.path.exists(libs_dir): return None
            
            # 1. Intentar el nombre exacto esperado
            exact = os.path.join(libs_dir, pattern)
            if os.path.exists(exact): return exact
            
            # 2. Buscar por versión pero EXCLUIR -sources, -dev, -all
            import glob
            matches = glob.glob(os.path.join(libs_dir, f'*{new_v}*.jar'))
            valid_matches = [m for m in matches if not any(x in os.path.basename(m).lower() for x in ['sources', 'dev', 'all', 'shadow'])]
            
            if valid_matches:
                return sorted(valid_matches, key=os.path.getmtime)[-1]
            
            # 3. Si no hay nada, el más reciente que sea JAR
            matches = glob.glob(os.path.join(libs_dir, '*.jar'))
            if matches:
                return sorted(matches, key=os.path.getmtime)[-1]
            return None

        c_jar = find_jar(CLIENT_DIR, f'minebridge-client-{new_v}.jar')
        s_jar = find_jar(SERVER_DIR, f'minebridge-server-{new_v}.jar')

        if not c_jar or not s_jar:
             print("  [X] No se encontraron los .jar compilados."); return

        print("\n  [>] Publicando en el servidor...")
        client_package = os.path.join(ROOT_DIR, f'minebridge-client-pack-{new_v}.zip')
        try:
            # ── Empaquetado del Cliente (Siempre ZIP para que el Launcher lo extraiga) ──
            print(f"  [>] Creando paquete ZIP para el cliente...")
            with zipfile.ZipFile(client_package, 'w') as zipf:
                # 1. Agregar el mod principal
                print(f"      + {os.path.basename(c_jar)} (Mod Base)")
                zipf.write(c_jar, os.path.basename(c_jar))
                
                # 2. Agregar extras si existen (en la raíz del zip)
                mods_add_dir = os.path.join(MOD_DIR, 'modsaddclient')
                if os.path.isdir(mods_add_dir):
                    for item in os.listdir(mods_add_dir):
                        full_path = os.path.join(mods_add_dir, item)
                        if os.path.isfile(full_path) and item.endswith(".jar"):
                            print(f"      + {item} (Extra)")
                            zipf.write(full_path, item)
            
            # Subir el ZIP como modclient
            _upload_binary(cfg, token, "modclient", new_v, client_package)
            _force_set_version(cfg, token, "modclient", new_v)
            
            # Subir el JAR del servidor como modserver (este no necesita zip por ahora)
            _upload_binary(cfg, token, "modserver", new_v, s_jar)
            _force_set_version(cfg, token, "modserver", new_v)
            
        except Exception as e:
            print(f"  [X] Falló la subida de mods: {e}")
        finally:
            # Limpiar ZIP temporal para no ensuciar el repo
            if client_package and os.path.exists(client_package):
                try: os.remove(client_package)
                except: pass

    except Exception as e:
        print(f"  [X] Falló la compilación o subida: {e}")
    finally:
        # Restaurar ModConfig.java para evitar dejar credenciales en el código fuente
        if original_java_content:
            print("  [>] Restaurando ModConfig.java a su estado original...")
            with open(mod_config_java, 'w', encoding='utf-8') as f:
                f.write(original_java_content)


# --- Main ---
def main():
    remote_url, local_url = _load_env_url()
    print("╔════════════════════════════════════════════════════════╗")
    print("║   EMPAQUETADOR MAESTRO — MINECRAFT MANAGER SUITE       ║")
    print("╚════════════════════════════════════════════════════════╝")

    try:
        lv, _ = _launcher_current_version()
        print(f"  Launcher : v{lv}")
    except: pass
    try:
        av, ab, _ = _app_current_version()
        print(f"  App      : v{av}+{ab}")
    except: pass
    try:
        mv, _ = _mod_current_version(os.path.join(CLIENT_DIR, 'gradle.properties'))
        print(f"  Mods     : v{mv}")
    except: pass
    print("  ────────────────────────────────────────────────────────")

    print("\n  ¿Qué deseas compilar y publicar?")
    print("  [1] Launcher (PyInstaller .exe)")
    print("  [2] App Flutter (.apk)")
    print("  [3] Mods MineBridge (Cliente y Servidor .jar)")
    print("  [4] Compilar Todo")
    print("  [5] CONFIGURACIÓN (IP, Puerto, Credenciales, API Key)")
    print("  [0] Cancelar")

    choice = input("\n  Selecciona [0-5]: ").strip()
    if choice == '0': sys.exit(0)

    cfg = {}
    if choice == '5':
        configure_packager()
        print("\n  Reiniciando con nueva configuración...")
        return main()

    if choice not in ('1', '2', '3', '4'):
        print("  [X] Opción inválida"); sys.exit(1)

    if not cfg: cfg = _load_api_config()
    print(f"\n  ── Conectando a {cfg['api_url']} ──")
    try:
        token = _get_token(cfg)
        print("  [✓] Autenticado correctamente")
    except RuntimeError as e:
        print(f"  [X] Error: {e}")
        sys.exit(1)

    if choice in ('1', '4'): build_launcher(cfg, token)
    if choice in ('2', '4'): build_app(cfg, token)
    if choice in ('3', '4'): build_mods(cfg, token)

    print("\n  ═════════════════════════════════════════════════════════")
    print("  ¡Proceso finalizado! Todo está listo en la nube.")
    print("  ═════════════════════════════════════════════════════════")

if __name__ == '__main__':
    try: main()
    except KeyboardInterrupt: sys.exit(0)
