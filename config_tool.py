import os
import sys

def load_env(filepath):
    env = {}
    if os.path.exists(filepath):
        with open(filepath, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                if '=' in line:
                    parts = line.split('=', 1)
                    if len(parts) == 2:
                        key, value = parts
                        env[key.strip()] = value.strip()
    return env

def save_env(filepath, env, title="Configuration"):
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(f"# {title} - Auto-generated\n")
        f.write("# Do NOT commit this file to version control\n\n")
        for key, value in env.items():
            f.write(f"{key}={value}\n")

def ask_value(prompt, current_value, default_value):
    # Si hay un valor actual, ese es el default. Si no, usamos el default_value.
    val = current_value if current_value is not None else default_value
    display_val = f" [{val}]" if val else ""
    user_input = input(f"{prompt}{display_val}: ").strip()
    return user_input if user_input else val

def configure_server():
    print("\n--- CONFIGURACION DEL SERVIDOR ---")
    path = "server/.env"
    current = load_env(path)
    
    defaults = {
        "SECRET_KEY": "supersecretkeychangeit",
        "DB_ENGINE": "postgresql",
        "DB_HOST": "127.0.0.1",
        "DB_PORT": "5432",
        "DB_NAME": "mine_db",
        "DB_USER": "postgres",
        "DB_PASSWORD": "postgres",
        "API_HOST": "0.0.0.0",
        "API_PORT": "8000",
        "DEFAULT_MINECRAFT_RAM": "4096M",
        "APP_URL": "" # Importante para las skins
    }
    
    new_env = {}
    for key, default in defaults.items():
        new_env[key] = ask_value(f"Configurar {key}", current.get(key), default)
    
    # Mantener variables extra que no estén en defaults
    for k, v in current.items():
        if k not in new_env:
            new_env[k] = v
            
    save_env(path, new_env, "Minecraft Server")
    print(f"\n[OK] Configuración del servidor guardada en {path}")

def configure_launcher():
    print("\n--- CONFIGURACION DEL LAUNCHER ---")
    path = "minecraftLauncher/.env"
    current = load_env(path)
    
    # El launcher deduce la API_URL automáticamente basándose en la IP del servidor que el usuario
    # configura dentro de la interfaz gráfica. No se necesitan variables de entorno obligatorias aquí.
    defaults = {}
    
    new_env = {}
    for key, default in defaults.items():
        new_env[key] = ask_value(f"Configurar {key}", current.get(key), default)
    
    # Mantener variables extra
    for k, v in current.items():
        if k not in new_env:
            new_env[k] = v
            
    save_env(path, new_env, "Minecraft Launcher")
    print(f"\n[OK] Configuración del launcher guardada en {path}")

def main():
    print("\n" + "="*40)
    print("   CONFIGURADOR UNIVERSAL .ENV v1.0")
    print("="*40)
    print("1. Configurar Servidor (Backend)")
    print("2. Configurar Launcher (Escritorio)")
    print("3. Configurar Todo")
    print("4. Salir")
    
    choice = input("\nSeleccione una opción: ").strip()
    
    if choice == "1":
        configure_server()
    elif choice == "2":
        configure_launcher()
    elif choice == "3":
        configure_server()
        configure_launcher()
    elif choice == "4":
        sys.exit(0)
    else:
        print("\n[!] Opción no válida.")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n[!] Operación cancelada por el usuario.")
        sys.exit(1)
