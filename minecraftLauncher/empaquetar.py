"""
EMPAQUETADOR UNIFICADO — Minecraft Launcher + App Flutter
=========================================================
• Instala automáticamente las dependencias antes de compilar
• Incrementa la versión automáticamente
• Compila el ejecutable (PyInstaller) y/o el APK (flutter build apk)
• Copia los artefactos a server/static/versions/{platform}/{version}/
• Actualiza el puntero en server/static/versions.json
• NO hace operaciones de git (eso queda a cargo del usuario)
"""
import os
import re
import sys
import shutil
import json
import subprocess

# ── Rutas ────────────────────────────────────────────────────────────────────
LAUNCHER_DIR  = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT  = os.path.abspath(os.path.join(LAUNCHER_DIR, '..'))
APP_DIR       = os.path.join(PROJECT_ROOT, 'appserve')
VERSIONS_DIR  = os.path.join(PROJECT_ROOT, 'server', 'static', 'versions')
VERSIONS_JSON = os.path.join(PROJECT_ROOT, 'server', 'static', 'versions.json')

LAUNCHER_INFO = os.path.join(LAUNCHER_DIR, 'core', 'info.py')
LAUNCHER_SPEC = os.path.join(LAUNCHER_DIR, 'main.spec')
LAUNCHER_REQS = os.path.join(LAUNCHER_DIR, 'requirements.txt')
APP_PUBSPEC   = os.path.join(APP_DIR, 'pubspec.yaml')

# ── Instalación de dependencias ───────────────────────────────────────────────

def _install_launcher_deps():
    """Instala requirements.txt del launcher en el Python actual (pip install -r)."""
    print("  [>] Verificando dependencias del launcher...")
    if not os.path.exists(LAUNCHER_REQS):
        print(f"  [!] No se encontró {LAUNCHER_REQS}. Saltando.")
        return
    result = subprocess.run(
        [sys.executable, "-m", "pip", "install", "-r", LAUNCHER_REQS, "--quiet"],
        cwd=LAUNCHER_DIR
    )
    if result.returncode != 0:
        print("  [X] pip install falló. Instala las dependencias manualmente:")
        print(f"      pip install -r {LAUNCHER_REQS}")
        sys.exit(1)
    print("  [✓] Dependencias del launcher OK")

def _check_flutter():
    """Verifica que flutter esté disponible en PATH (usa shell=True en Windows)."""
    print("  [>] Verificando Flutter...")
    result = subprocess.run(
        "flutter --version",
        capture_output=True, text=True, shell=True
    )
    if result.returncode != 0:
        print("  [X] Flutter no encontrado en PATH. Instálalo desde https://flutter.dev")
        print(f"      Asegúrate de que 'flutter' esté en tu variable PATH.")
        sys.exit(1)
    first_line = result.stdout.strip().splitlines()[0] if result.stdout else "?"
    print(f"  [✓] {first_line}")


def _bump(version: str, tipo: str) -> str:
    parts = [int(x) for x in version.split('.')]
    if tipo == '1':   # Grande
        parts[0] += 1; parts[1:] = [0] * len(parts[1:])
    elif tipo == '2': # Mediana
        parts[1] += 1; parts[2:] = [0] * len(parts[2:])
    elif tipo == '3': # Parche
        parts[-1] += 1
    # '4' = mantener
    return '.'.join(str(p) for p in parts)

def _ask_bump(current: str) -> tuple[str, str]:
    """Pregunta tipo de bump. Devuelve (nueva_versión, tipo_label)."""
    print(f"\n  Versión actual: {current}")
    print("  [1] Grande   (X.0.0  — resetea todo)")
    print("  [2] Mediana  (x.Y.0  — resetea parche)")
    print("  [3] Parche   (x.y.Z)")
    print("  [4] Mantener (misma versión)")
    choice = input("  Selecciona [1-4]: ").strip()
    labels = {'1': 'GRANDE', '2': 'MEDIANA', '3': 'PARCHE', '4': 'MANTENER'}
    if choice not in labels:
        print("  [X] Opción inválida"); sys.exit(1)
    return _bump(current, choice), labels[choice]

# ── Gestión de versions.json ──────────────────────────────────────────────────

def _load_json() -> dict:
    if os.path.exists(VERSIONS_JSON):
        with open(VERSIONS_JSON) as f:
            return json.load(f)
    return {}

def _save_json(data: dict):
    os.makedirs(os.path.dirname(VERSIONS_JSON), exist_ok=True)
    with open(VERSIONS_JSON, 'w') as f:
        json.dump(data, f, indent=2)

# ═══════════════════════════════════════════════════════════════════════════════
# LAUNCHER
# ═══════════════════════════════════════════════════════════════════════════════

def _launcher_current_version() -> tuple[str, str]:
    """Lee VERSION desde core/info.py. Retorna (version, contenido_raw)."""
    with open(LAUNCHER_INFO, encoding='utf-8') as f:
        content = f.read()
    m = re.search(r"VERSION\s*=\s*'([^']+)'", content)
    if not m:
        print(f"[X] No se encontró VERSION en {LAUNCHER_INFO}"); sys.exit(1)
    return m.group(1), content

def _launcher_save_version(content: str, old_v: str, new_v: str):
    """Actualiza VERSION en core/info.py y main.spec."""
    new_info = content.replace(f"VERSION = '{old_v}'", f"VERSION = '{new_v}'")
    with open(LAUNCHER_INFO, 'w', encoding='utf-8') as f:
        f.write(new_info)
    if os.path.exists(LAUNCHER_SPEC):
        with open(LAUNCHER_SPEC, encoding='utf-8') as f:
            spec = f.read()
        with open(LAUNCHER_SPEC, 'w', encoding='utf-8') as f:
            f.write(spec.replace(f"VERSION = '{old_v}'", f"VERSION = '{new_v}'"))
    print(f"  [✓] core/info.py  →  VERSION = '{new_v}'")

def _launcher_compile(new_version: str):
    """Compila el .exe con PyInstaller."""
    exe_name = f"MinecraftLauncher_v{new_version}.exe"
    print(f"\n  [>] PyInstaller → {exe_name}")
    env = os.environ.copy()
    env["BUILD_VERSION"] = new_version
    proc = subprocess.Popen(
        [sys.executable, "-m", "PyInstaller", LAUNCHER_SPEC, "-y"],
        cwd=LAUNCHER_DIR, env=env
    )
    if proc.wait() != 0:
        print("  [X] PyInstaller falló. La versión NO se ha guardado."); sys.exit(1)
    return exe_name

def _launcher_copy(exe_name: str, version: str):
    """Copia el exe a server/static/versions/launcher/{version}/launcher.exe"""
    src = os.path.join(LAUNCHER_DIR, 'dist', exe_name)
    if not os.path.exists(src):
        print(f"  [!] No encontrado: {src}"); return False
    dest_dir = os.path.join(VERSIONS_DIR, 'launcher', version)
    os.makedirs(dest_dir, exist_ok=True)
    dest = os.path.join(dest_dir, 'launcher.exe')
    shutil.copy2(src, dest)
    size_mb = os.path.getsize(dest) / 1_048_576
    print(f"  [✓] Copiado → versions/launcher/{version}/launcher.exe  ({size_mb:.1f} MB)")
    return True

def build_launcher():
    print("\n╔══════════════════════════════════════╗")
    print("║        COMPILAR LAUNCHER             ║")
    print("╚══════════════════════════════════════╝")
    current, content = _launcher_current_version()
    new_v, label = _ask_bump(current)
    print(f"\n  → Versión: {current}  →  {new_v}  [{label}]")
    confirm = input("  ¿Continuar? [s/N]: ").strip().lower()
    if confirm not in ('s', 'si', 'y', 'yes'):
        print("  Cancelado."); return

    # 1. Guardar versión ANTES de compilar (info.py la lee en runtime)
    if new_v != current:
        _launcher_save_version(content, current, new_v)

    # 2. Instalar dependencias
    _install_launcher_deps()

    # 3. Compilar
    exe_name = _launcher_compile(new_v)

    # 3. Copiar a versiones
    ok = _launcher_copy(exe_name, new_v)

    # 4. Actualizar puntero JSON
    if ok:
        data = _load_json()
        data['launcher'] = new_v
        _save_json(data)
        print(f"  [✓] versions.json  →  launcher: {new_v}")

    print(f"\n  ✅ Launcher v{new_v} listo.")
    print(f"     Archivo: dist/{exe_name}")
    print(f"     Servidor: server/static/versions/launcher/{new_v}/launcher.exe")
    print(f"\n     Para publicar en el VPS:")
    print(f"       git push → git pull en VPS → mine.py opción 17 → launcher → {new_v}")

# ═══════════════════════════════════════════════════════════════════════════════
# APP FLUTTER
# ═══════════════════════════════════════════════════════════════════════════════

def _app_current_version() -> tuple[str, int, str]:
    """Lee versión del pubspec.yaml. Retorna (semver, build_number, contenido_raw)."""
    with open(APP_PUBSPEC, encoding='utf-8') as f:
        content = f.read()
    m = re.search(r'^version:\s*(\d+\.\d+\.\d+)\+(\d+)', content, re.MULTILINE)
    if not m:
        print(f"[X] No se encontró 'version: X.Y.Z+N' en {APP_PUBSPEC}"); sys.exit(1)
    return m.group(1), int(m.group(2)), content

def _app_save_version(content: str, old_semver: str, old_build: int,
                      new_semver: str, new_build: int):
    """Actualiza version en pubspec.yaml."""
    old_str = f"version: {old_semver}+{old_build}"
    new_str = f"version: {new_semver}+{new_build}"
    with open(APP_PUBSPEC, 'w', encoding='utf-8') as f:
        f.write(content.replace(old_str, new_str))
    print(f"  [✓] pubspec.yaml  →  version: {new_semver}+{new_build}")

def _app_compile():
    """Compila el APK de release con flutter (shell=True para Windows)."""
    print(f"\n  [>] flutter build apk --release")
    proc = subprocess.Popen(
        "flutter build apk --release",
        cwd=APP_DIR, shell=True
    )
    if proc.wait() != 0:
        print("  [X] Flutter build falló. La versión NO se ha guardado."); sys.exit(1)

def _app_copy(version: str):
    """Copia el APK compilado a server/static/versions/app/{version}/app.apk"""
    src = os.path.join(APP_DIR, 'build', 'app', 'outputs', 'flutter-apk', 'app-release.apk')
    if not os.path.exists(src):
        print(f"  [!] No encontrado: {src}"); return False
    dest_dir = os.path.join(VERSIONS_DIR, 'app', version)
    os.makedirs(dest_dir, exist_ok=True)
    dest = os.path.join(dest_dir, 'app.apk')
    shutil.copy2(src, dest)
    size_mb = os.path.getsize(dest) / 1_048_576
    print(f"  [✓] Copiado → versions/app/{version}/app.apk  ({size_mb:.1f} MB)")
    return True

def build_app():
    print("\n╔══════════════════════════════════════╗")
    print("║        COMPILAR APP FLUTTER          ║")
    print("╚══════════════════════════════════════╝")
    current, build_num, content = _app_current_version()
    new_v, label = _ask_bump(current)
    new_build = build_num + 1
    print(f"\n  → Versión: {current}+{build_num}  →  {new_v}+{new_build}  [{label}]")
    confirm = input("  ¿Continuar? [s/N]: ").strip().lower()
    if confirm not in ('s', 'si', 'y', 'yes'):
        print("  Cancelado."); return

    # 1. Guardar versión
    if new_v != current or new_build != build_num:
        _app_save_version(content, current, build_num, new_v, new_build)

    # 2. Verificar Flutter y compilar
    _check_flutter()
    _app_compile()

    # 3. Copiar a versiones
    ok = _app_copy(new_v)

    # 4. Actualizar puntero JSON
    if ok:
        data = _load_json()
        data['app'] = new_v
        _save_json(data)
        print(f"  [✓] versions.json  →  app: {new_v}")

    print(f"\n  ✅ App Flutter v{new_v} lista.")
    print(f"     Servidor: server/static/versions/app/{new_v}/app.apk")
    print(f"\n     Para publicar en el VPS:")
    print(f"       git push → git pull en VPS → mine.py opción 17 → app → {new_v}")

# ═══════════════════════════════════════════════════════════════════════════════
# MENÚ PRINCIPAL
# ═══════════════════════════════════════════════════════════════════════════════

def main():
    print("╔══════════════════════════════════════════╗")
    print("║   EMPAQUETADOR MINECRAFT MANAGER SUITE  ║")
    print("╚══════════════════════════════════════════╝")

    # ── Preflight: mostrar versiones actuales ────────────────────────────────
    print("\n  ── Estado actual ──────────────────────────")
    try:
        launcher_v, _ = _launcher_current_version()
        print(f"  Launcher : v{launcher_v}  (core/info.py)")
    except Exception:
        launcher_v = "???"
        print(f"  Launcher : [no encontrado]")
    try:
        app_v, app_b, _ = _app_current_version()
        print(f"  App      : v{app_v}+{app_b}  (pubspec.yaml)")
    except Exception:
        app_v = "???"
        print(f"  App      : [no encontrado]")
    print("  ────────────────────────────────────────────")

    print("\n  ¿Qué deseas compilar?")
    print("  [1] Launcher (PyInstaller .exe)")
    print("  [2] App Flutter (.apk)")
    print("  [3] Ambos")
    print("  [0] Cancelar")

    choice = input("\n  Selecciona [0-3]: ").strip()

    if choice == '0':
        print("\n  Cancelado."); sys.exit(0)
    elif choice == '1':
        build_launcher()
    elif choice == '2':
        build_app()
    elif choice == '3':
        build_launcher()
        build_app()
    else:
        print("  [X] Opción inválida"); sys.exit(1)

    print("\n  ══════════════════════════════════════")
    print("  Archivos listos en server/static/versions/")
    print("  Haz git push y en el VPS: git pull + mine.py opción 17")
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


