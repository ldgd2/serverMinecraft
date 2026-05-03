"""
EMPAQUETADOR UNIFICADO — Minecraft Launcher + App Flutter
=========================================================
• Instala dependencias automáticamente antes de compilar
• Incrementa la versión automáticamente en core/info.py y pubspec.yaml
• Compila el ejecutable (PyInstaller) y/o el APK (flutter build apk)
• Sube el binario al backend vía POST /api/v1/updates/upload/{platform}/{version}
  → El servidor guarda el archivo y actualiza el puntero automáticamente
• NO toca git, NO copia nada localmente al servidor
"""
import os
import re
import sys
import subprocess

# ── Rutas locales ─────────────────────────────────────────────────────────────
LAUNCHER_DIR  = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT  = os.path.abspath(os.path.join(LAUNCHER_DIR, '..'))
APP_DIR       = os.path.join(PROJECT_ROOT, 'appserve')
LAUNCHER_INFO = os.path.join(LAUNCHER_DIR, 'core', 'info.py')
LAUNCHER_SPEC = os.path.join(LAUNCHER_DIR, 'main.spec')
LAUNCHER_REQS = os.path.join(LAUNCHER_DIR, 'requirements.txt')
APP_PUBSPEC   = os.path.join(APP_DIR, 'pubspec.yaml')

# ── Config de API (se pide al inicio si no está configurada) ──────────────────
_API_CFG_FILE = os.path.join(LAUNCHER_DIR, '.packager_config')

def _load_api_config() -> dict:
    cfg = {}
    if os.path.exists(_API_CFG_FILE):
        for line in open(_API_CFG_FILE).readlines():
            if '=' in line:
                k, v = line.strip().split('=', 1)
                cfg[k] = v
    return cfg

def _save_api_config(cfg: dict):
    with open(_API_CFG_FILE, 'w') as f:
        for k, v in cfg.items():
            f.write(f"{k}={v}\n")

def _get_api_config() -> dict:
    """Carga o solicita la URL del backend y credenciales admin."""
    cfg = _load_api_config()
    changed = False

    if not cfg.get('api_url'):
        print("\n  ┌─ Configuración del backend ─────────────────────────")
        print("  │ Primera vez: ingresa la URL base del servidor.")
        print("  │ Ejemplo: http://vps.tudominio.com:8000")
        cfg['api_url'] = input("  │ API URL: ").strip().rstrip('/')
        changed = True

    if not cfg.get('username'):
        cfg['username'] = input("  │ Usuario admin: ").strip()
        changed = True

    if not cfg.get('password'):
        import getpass
        cfg['password'] = getpass.getpass("  │ Contraseña: ")
        changed = True

    if changed:
        save = input("  └ ¿Guardar credenciales para próximas veces? [s/N]: ").strip().lower()
        if save in ('s', 'si', 'y', 'yes'):
            _save_api_config(cfg)
            print("  [✓] Guardado en .packager_config (no lo subas a git)")

    return cfg

def _get_token(cfg: dict) -> str:
    """Obtiene JWT token del backend."""
    import urllib.request, urllib.error, json
    url = f"{cfg['api_url']}/api/v1/auth/login"
    payload = json.dumps({"username": cfg['username'], "password": cfg['password']}).encode()
    req = urllib.request.Request(url, data=payload,
                                 headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            resp = json.loads(r.read())
            # Soporta tanto {'access_token': '...'} como {'data': {'access_token': '...'}}
            token = (
                resp.get('access_token')
                or resp.get('token')
                or (resp.get('data') or {}).get('access_token')
                or (resp.get('data') or {}).get('token')
            )
            if not token:
                raise RuntimeError(f"No se encontró token en la respuesta: {resp}")
            return token
    except urllib.error.HTTPError as e:
        raise RuntimeError(f"Login falló ({e.code}): {e.read().decode()}")

def _upload_binary(cfg: dict, token: str, platform: str, version: str, filepath: str):
    """Sube el binario al backend vía multipart/form-data con urllib."""
    import urllib.request, urllib.error
    import mimetypes, uuid

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
    ).encode() + file_data + f"\r\n--{boundary}--\r\n".encode()

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
            import json
            resp = json.loads(r.read())
            print(f"  [✓] {resp.get('message', 'Subido OK')}")
            return resp
    except urllib.error.HTTPError as e:
        body_err = e.read().decode()
        raise RuntimeError(f"Upload falló ({e.code}): {body_err}")

# ── Dependencias ─────────────────────────────────────────────────────────────

def _install_launcher_deps():
    print("  [>] Verificando dependencias del launcher...")
    if not os.path.exists(LAUNCHER_REQS):
        print("  [!] No se encontró requirements.txt. Saltando."); return
    result = subprocess.run(
        [sys.executable, "-m", "pip", "install", "-r", LAUNCHER_REQS, "--quiet"],
        cwd=LAUNCHER_DIR
    )
    if result.returncode != 0:
        print(f"  [X] pip install falló. Ejecuta: pip install -r {LAUNCHER_REQS}")
        sys.exit(1)
    print("  [✓] Dependencias OK")

def _check_flutter():
    print("  [>] Verificando Flutter...")
    result = subprocess.run("flutter --version", capture_output=True, text=True, shell=True)
    if result.returncode != 0:
        print("  [X] Flutter no encontrado en PATH. Instálalo desde https://flutter.dev")
        sys.exit(1)
    first = result.stdout.strip().splitlines()[0] if result.stdout else "?"
    print(f"  [✓] {first}")

# ── Versiones ─────────────────────────────────────────────────────────────────

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

# ═══════════════════════════════════════════════════════════════════════════════
# LAUNCHER
# ═══════════════════════════════════════════════════════════════════════════════

def _launcher_current_version() -> tuple[str, str]:
    with open(LAUNCHER_INFO, encoding='utf-8') as f:
        content = f.read()
    m = re.search(r"VERSION\s*=\s*'([^']+)'", content)
    if not m:
        print(f"[X] No se encontró VERSION en {LAUNCHER_INFO}"); sys.exit(1)
    return m.group(1), content

def _launcher_save_version(content: str, old_v: str, new_v: str):
    with open(LAUNCHER_INFO, 'w', encoding='utf-8') as f:
        f.write(content.replace(f"VERSION = '{old_v}'", f"VERSION = '{new_v}'"))
    if os.path.exists(LAUNCHER_SPEC):
        with open(LAUNCHER_SPEC, encoding='utf-8') as f:
            spec = f.read()
        with open(LAUNCHER_SPEC, 'w', encoding='utf-8') as f:
            f.write(spec.replace(f"VERSION = '{old_v}'", f"VERSION = '{new_v}'"))
    print(f"  [✓] core/info.py → VERSION = '{new_v}'")

def _launcher_compile(version: str) -> str:
    exe_name = f"MinecraftLauncher_v{version}.exe"
    print(f"\n  [>] PyInstaller → {exe_name}")
    env = os.environ.copy()
    env["BUILD_VERSION"] = version
    proc = subprocess.Popen(
        [sys.executable, "-m", "PyInstaller", LAUNCHER_SPEC, "-y"],
        cwd=LAUNCHER_DIR, env=env
    )
    if proc.wait() != 0:
        print("  [X] PyInstaller falló. Versión NO guardada."); sys.exit(1)
    return exe_name

def build_launcher(cfg: dict, token: str):
    print("\n╔══════════════════════════════════════╗")
    print("║        COMPILAR LAUNCHER             ║")
    print("╚══════════════════════════════════════╝")
    current, content = _launcher_current_version()
    new_v, label = _ask_bump(current)
    print(f"\n  → {current}  →  {new_v}  [{label}]")
    if input("  ¿Continuar? [s/N]: ").strip().lower() not in ('s', 'si', 'y', 'yes'):
        print("  Cancelado."); return

    if new_v != current:
        _launcher_save_version(content, current, new_v)

    _install_launcher_deps()
    exe_name = _launcher_compile(new_v)

    exe_path = os.path.join(LAUNCHER_DIR, 'dist', exe_name)
    if not os.path.exists(exe_path):
        print(f"  [X] No se encontró el exe: {exe_path}"); return

    print("\n  [>] Publicando en el servidor...")
    try:
        _upload_binary(cfg, token, "launcher", new_v, exe_path)
        print(f"\n  ✅ Launcher v{new_v} publicado en el servidor.")
        print(f"     Los usuarios recibirán la actualización automáticamente.")
    except RuntimeError as e:
        print(f"\n  [X] Error al subir: {e}")
        print(f"     El exe está en: dist/{exe_name}")

# ═══════════════════════════════════════════════════════════════════════════════
# APP FLUTTER
# ═══════════════════════════════════════════════════════════════════════════════

def _app_current_version() -> tuple[str, int, str]:
    with open(APP_PUBSPEC, encoding='utf-8') as f:
        content = f.read()
    m = re.search(r'^version:\s*(\d+\.\d+\.\d+)\+(\d+)', content, re.MULTILINE)
    if not m:
        print(f"[X] No se encontró version en {APP_PUBSPEC}"); sys.exit(1)
    return m.group(1), int(m.group(2)), content

def _app_save_version(content: str, old_s: str, old_b: int, new_s: str, new_b: int):
    with open(APP_PUBSPEC, 'w', encoding='utf-8') as f:
        f.write(content.replace(f"version: {old_s}+{old_b}", f"version: {new_s}+{new_b}"))
    print(f"  [✓] pubspec.yaml → version: {new_s}+{new_b}")

def _app_compile():
    print(f"\n  [>] flutter build apk --release")
    proc = subprocess.Popen("flutter build apk --release", cwd=APP_DIR, shell=True)
    if proc.wait() != 0:
        print("  [X] Flutter build falló. Versión NO guardada."); sys.exit(1)

def build_app(cfg: dict, token: str):
    print("\n╔══════════════════════════════════════╗")
    print("║        COMPILAR APP FLUTTER          ║")
    print("╚══════════════════════════════════════╝")
    current, build_num, content = _app_current_version()
    new_v, label = _ask_bump(current)
    new_build = build_num + 1
    print(f"\n  → {current}+{build_num}  →  {new_v}+{new_build}  [{label}]")
    if input("  ¿Continuar? [s/N]: ").strip().lower() not in ('s', 'si', 'y', 'yes'):
        print("  Cancelado."); return

    if new_v != current or new_build != build_num:
        _app_save_version(content, current, build_num, new_v, new_build)

    _check_flutter()
    _app_compile()

    apk_path = os.path.join(APP_DIR, 'build', 'app', 'outputs', 'flutter-apk', 'app-release.apk')
    if not os.path.exists(apk_path):
        print(f"  [X] No se encontró el APK: {apk_path}"); return

    print("\n  [>] Publicando en el servidor...")
    try:
        _upload_binary(cfg, token, "app", new_v, apk_path)
        print(f"\n  ✅ App Flutter v{new_v} publicada en el servidor.")
        print(f"     Los usuarios recibirán la actualización automáticamente.")
    except RuntimeError as e:
        print(f"\n  [X] Error al subir: {e}")
        print(f"     El APK está en: {apk_path}")

# ═══════════════════════════════════════════════════════════════════════════════
# MENÚ PRINCIPAL
# ═══════════════════════════════════════════════════════════════════════════════

def main():
    print("╔══════════════════════════════════════════╗")
    print("║   EMPAQUETADOR MINECRAFT MANAGER SUITE  ║")
    print("╚══════════════════════════════════════════╝")

    # Versiones actuales
    print("\n  ── Estado actual ──────────────────────────")
    try:
        lv, _ = _launcher_current_version()
        print(f"  Launcher : v{lv}  (core/info.py)")
    except Exception:
        print("  Launcher : [no encontrado]")
    try:
        av, ab, _ = _app_current_version()
        print(f"  App      : v{av}+{ab}  (pubspec.yaml)")
    except Exception:
        print("  App      : [no encontrado]")
    print("  ────────────────────────────────────────────")

    print("\n  ¿Qué deseas compilar?")
    print("  [1] Launcher (PyInstaller .exe)")
    print("  [2] App Flutter (.apk)")
    print("  [3] Ambos")
    print("  [4] Re-configurar servidor/credenciales")
    print("  [0] Cancelar")

    choice = input("\n  Selecciona [0-4]: ").strip()
    if choice == '0':
        print("\n  Cancelado."); sys.exit(0)
    
    cfg = {}
    if choice == '4':
        if os.path.exists(_API_CFG_FILE):
            os.remove(_API_CFG_FILE)
            print("  [✓] Credenciales eliminadas.")
        print("\n  ── Conexión con el servidor ─────────────────")
        cfg = _get_api_config()
        choice = input("\n  Ahora, ¿qué compilar? [1] Launcher  [2] App  [3] Ambos  [0] Cancelar: ").strip()
        if choice == '0':
            print("  Cancelado."); sys.exit(0)
            
    if choice not in ('1', '2', '3'):
        print("  [X] Opción inválida"); sys.exit(1)

    # Autenticar contra el backend
    print("\n  ── Conexión con el servidor ─────────────────")
    if not cfg:
        cfg = _get_api_config()
    print(f"  [>] Autenticando en {cfg['api_url']}...")
    try:
        token = _get_token(cfg)
        print("  [✓] Autenticado correctamente")
    except RuntimeError as e:
        print(f"  [X] No se pudo autenticar: {e}")
        print("  [i] Usa la opción [4] para cambiar las credenciales.")
        # Limpiar credenciales guardadas si falla
        cfg.pop('password', None)
        sys.exit(1)

    if choice in ('1', '3'):
        build_launcher(cfg, token)
    if choice in ('2', '3'):
        build_app(cfg, token)

    print("\n  ══════════════════════════════════════")
    print("  ¡Listo! El servidor ya sirve la nueva versión.")
    print("  ══════════════════════════════════════")

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n  Operación cancelada.")
        sys.exit(0)
    except Exception as e:
        print(f"\n  [X] Error fatal: {e}")
        raise
