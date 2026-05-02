#!/usr/bin/env python3
"""
setup_rcon.py — Configurador automático de RCON para Minecraft Server Manager
Ejecutar UNA VEZ en el servidor VPS:
  python setup_rcon.py

Qué hace:
  1. Genera una contraseña segura aleatoria (o usa la existente si ya está configurada)
  2. Actualiza todos los server.properties encontrados con enable-rcon=true
  3. Escribe RCON_PASSWORD / RCON_PORT / RCON_HOST en el .env del backend
"""
import os
import secrets
import string
import glob
import sys

# ─── Configuración base ───────────────────────────────────────────────────────

SCRIPT_DIR   = os.path.dirname(os.path.abspath(__file__))
ENV_FILE     = os.path.join(SCRIPT_DIR, ".env")
SERVERS_DIR  = os.path.join(SCRIPT_DIR, "servers")   # donde viven los mundos
RCON_PORT    = 25575                                   # puerto estándar de Minecraft RCON
RCON_HOST    = "127.0.0.1"                            # siempre local — el backend y el MC están en el mismo VPS

# ─── Helpers ──────────────────────────────────────────────────────────────────

def generate_password(length: int = 24) -> str:
    alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
    return ''.join(secrets.choice(alphabet) for _ in range(length))

def read_env(path: str) -> dict:
    env = {}
    if not os.path.exists(path):
        return env
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, val = line.partition("=")
            env[key.strip()] = val.strip()
    return env

def write_env(path: str, env: dict):
    lines = []
    for k, v in env.items():
        lines.append(f"{k}={v}\n")
    with open(path, "w", encoding="utf-8") as f:
        f.writelines(lines)

def patch_server_properties(props_path: str, password: str, port: int):
    """Activa RCON en un server.properties dado."""
    if not os.path.exists(props_path):
        print(f"  ⚠  No encontrado: {props_path}")
        return False

    with open(props_path, "r", encoding="utf-8", errors="replace") as f:
        content = f.read()

    lines = content.splitlines(keepends=True)
    new_lines = []
    found = {"enable-rcon": False, "rcon.port": False, "rcon.password": False}

    for line in lines:
        stripped = line.strip()
        if stripped.startswith("enable-rcon"):
            new_lines.append(f"enable-rcon=true\n")
            found["enable-rcon"] = True
        elif stripped.startswith("rcon.port"):
            new_lines.append(f"rcon.port={port}\n")
            found["rcon.port"] = True
        elif stripped.startswith("rcon.password"):
            new_lines.append(f"rcon.password={password}\n")
            found["rcon.password"] = True
        else:
            new_lines.append(line)

    # Añadir las que no existían
    if not found["enable-rcon"]:
        new_lines.append(f"\nenable-rcon=true\n")
    if not found["rcon.port"]:
        new_lines.append(f"rcon.port={port}\n")
    if not found["rcon.password"]:
        new_lines.append(f"rcon.password={password}\n")

    with open(props_path, "w", encoding="utf-8") as f:
        f.writelines(new_lines)

    return True

# ─── Main ─────────────────────────────────────────────────────────────────────

def main():
    print("=" * 60)
    print("  RCON Auto-Configurator — Minecraft Server Manager")
    print("=" * 60)

    # 1. Leer .env existente
    env = read_env(ENV_FILE)

    # 2. Determinar contraseña (reutilizar si ya existe)
    existing_pw = env.get("RCON_PASSWORD", "")
    if existing_pw:
        print(f"\n✅ RCON ya configurado. Usando contraseña existente.")
        password = existing_pw
    else:
        password = generate_password(24)
        print(f"\n🔑 Contraseña generada automáticamente (guárdala si la necesitas).")

    print(f"   Host:     {RCON_HOST}")
    print(f"   Puerto:   {RCON_PORT}")
    print(f"   Password: {'*' * len(password)} (oculta por seguridad)\n")

    # 3. Actualizar .env del backend
    env["RCON_HOST"]     = RCON_HOST
    env["RCON_PORT"]     = str(RCON_PORT)
    env["RCON_PASSWORD"] = password
    write_env(ENV_FILE, env)
    print(f"✅ .env actualizado: {ENV_FILE}")

    # 4. Encontrar todos los server.properties
    patterns = [
        os.path.join(SERVERS_DIR, "*", "server.properties"),
        os.path.join(SERVERS_DIR, "server.properties"),
    ]
    props_files = []
    for pattern in patterns:
        props_files.extend(glob.glob(pattern))

    if not props_files:
        print(f"\n⚠  No se encontraron archivos server.properties en: {SERVERS_DIR}")
        print("   Parchea manualmente o asegúrate de que la ruta sea correcta.")
    else:
        print(f"\n🔍 Encontrados {len(props_files)} server.properties:")
        for props in props_files:
            server_name = os.path.basename(os.path.dirname(props))
            ok = patch_server_properties(props, password, RCON_PORT)
            status = "✅ Configurado" if ok else "❌ Error"
            print(f"   [{status}] {server_name}  →  {props}")

    print("\n" + "=" * 60)
    print("  ¡HECHO! Próximos pasos:")
    print("  1. Reinicia el servidor de Minecraft (para que lea los nuevos")
    print("     valores de server.properties)")
    print("  2. Reinicia el backend Python (python main.py)")
    print("  3. Envía un mensaje desde la App — ya no habrá warning")
    print("=" * 60)

if __name__ == "__main__":
    main()
