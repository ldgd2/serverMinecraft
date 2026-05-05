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
    url = "http://127.0.0.1:8000"
    if os.path.exists(SERVER_ENV):
        with open(SERVER_ENV, "r", encoding="utf-8") as f:
            for line in f:
                if line.startswith("APP_URL="):
                    url = line.split("=", 1)[1].strip().rstrip('/')
                    break
    return url

def _load_api_config() -> dict:
    cfg = {"api_url": _load_env_url()} # Default from env
    if os.path.exists(_API_CFG_FILE):
        for line in open(_API_CFG_FILE).readlines():
            if '=' in line:
                k, v = line.strip().split('=', 1)
                cfg[k] = v
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

    if changed:
        save = input("  └ ¿Guardar credenciales para próximas veces? [s/N]: ").strip().lower()
        if save in ('s', 'si', 'y', 'yes'):
            _save_api_config(cfg)
            print("  [✓] Guardado en .packager_config (no lo subas a git)")

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
    file_size = os.path.getsize(filepath) / 1_048_576

    print(f"  [>] Subiendo {filename} ({file_size:.1f} MB) → {url}")

    boundary = uuid.uuid4().hex
    ctype, _ = mimetypes.guess_type(filepath)
    ctype = ctype or 'application/octet-stream'

    with open(filepath, 'rb') as f:
        file_data = f.read()

    body = (
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="file"; filename="{filename}"\r\n'
        f"Content-Type: {ctype}\r\n\r\n"
    ).encode('utf-8') + file_data + f"\r\n--{boundary}--\r\n".encode('utf-8')

    req = urllib.request.Request(
        url, data=body,
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type":  f"multipart/form-data; boundary={boundary}",
        },
        method="POST"
    )

    try:
        with urllib.request.urlopen(req, timeout=300) as r:
            resp = json.loads(r.read())
            print(f"  [✓] {resp.get('message', 'Subido OK')}")
            return resp
    except urllib.error.HTTPError as e:
        body_err = e.read().decode('utf-8')
        raise RuntimeError(f"Upload falló ({e.code}): {body_err}")

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
    
    try:
        current, c_content = _mod_current_version(c_props)
        _, s_content = _mod_current_version(s_props)
    except Exception as e:
        print(f"  [X] Error: {e}"); return
    
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
    
    # A veces el jar sale sin versión
    if not os.path.exists(c_jar): c_jar = os.path.join(CLIENT_DIR, 'build', 'libs', f'minebridge-client.jar')
    if not os.path.exists(s_jar): s_jar = os.path.join(SERVER_DIR, 'build', 'libs', f'minebridge-server.jar')
    if not os.path.exists(c_jar): c_jar = os.path.join(CLIENT_DIR, 'build', 'libs', f'minebridge-{new_v}.jar')
    if not os.path.exists(s_jar): s_jar = os.path.join(SERVER_DIR, 'build', 'libs', f'minebridge-{new_v}.jar')

    import glob
    if not os.path.exists(c_jar):
        jars = glob.glob(os.path.join(CLIENT_DIR, 'build', 'libs', '*.jar'))
        c_jar = jars[0] if jars else None
    if not os.path.exists(s_jar):
        jars = glob.glob(os.path.join(SERVER_DIR, 'build', 'libs', '*.jar'))
        s_jar = jars[0] if jars else None

    if not c_jar or not s_jar:
         print("  [X] No se encontraron los .jar compilados.")
         return

    print("\n  [>] Publicando en el servidor...")
    try:
        # ── Empaquetado Especial del Cliente (Soporte para mods adicionales) ──
        mods_add_dir = os.path.join(MOD_DIR, 'modsaddclient')
        if os.path.isdir(mods_add_dir) and os.listdir(mods_add_dir):
            print(f"  [>] Detectados mods adicionales en {mods_add_dir}. Empaquetando ZIP...")
            client_package = os.path.join(ROOT_DIR, f'minebridge-client-pack-{new_v}.zip')
            with zipfile.ZipFile(client_package, 'w') as zipf:
                # 1. Agregar el mod principal
                print(f"      + {os.path.basename(c_jar)} (Base)")
                zipf.write(c_jar, os.path.basename(c_jar))
                # 2. Agregar extras
                for root, dirs, files in os.walk(mods_add_dir):
                    for file in files:
                        full_path = os.path.join(root, file)
                        rel_path = os.path.relpath(full_path, mods_add_dir)
                        print(f"      + {rel_path} (Extra)")
                        zipf.write(full_path, rel_path)
            print(f"  [✓] ZIP creado con {len(zipf.namelist())} archivos.")
            
            # Subir el ZIP en lugar del JAR
            _upload_binary(cfg, token, "modclient", new_v, client_package)
        else:
            # Subida normal (solo el JAR)
            _upload_binary(cfg, token, "modclient", new_v, c_jar)
            
        _force_set_version(cfg, token, "modclient", new_v)
        
        # El server mod siempre es un JAR (por ahora)
        _upload_binary(cfg, token, "modserver", new_v, s_jar)
        _force_set_version(cfg, token, "modserver", new_v)
        
    except Exception as e:
        print(f"  [X] Falló la subida de mods: {e}")

# --- Main ---
def main():
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
    print("  [5] Re-configurar credenciales")
    print("  [0] Cancelar")

    choice = input("\n  Selecciona [0-5]: ").strip()
    if choice == '0': sys.exit(0)

    cfg = {}
    if choice == '5':
        if os.path.exists(_API_CFG_FILE): os.remove(_API_CFG_FILE)
        print("  [✓] Credenciales locales eliminadas.")
        cfg = _get_api_config()
        choice = input("\n  ¿Qué compilar? [1] Launcher  [2] App  [3] Mods  [4] Todo: ").strip()

    if choice not in ('1', '2', '3', '4'):
        print("  [X] Opción inválida"); sys.exit(1)

    print(f"\n  ── Conectando a {_load_env_url()} ──")
    if not cfg: cfg = _get_api_config()
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
