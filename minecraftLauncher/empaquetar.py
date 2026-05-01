import os
import re
import sys

SPEC_FILE = 'main.spec'
INFO_FILE = os.path.join('core', 'info.py')

def load_version():
    if not os.path.exists(INFO_FILE):
        return None, None
    with open(INFO_FILE, 'r', encoding='utf-8') as f:
        content = f.read()
    match = re.search(r"VERSION\s*=\s*'([^']+)'", content)
    if match:
        return match.group(1), content
    return None, content

def save_version(content, old_v, new_v):
    # Update core/info.py
    new_info = content.replace(f"VERSION = '{old_v}'", f"VERSION = '{new_v}'")
    with open(INFO_FILE, 'w', encoding='utf-8') as f:
        f.write(new_info)
    
    # Also update VERSION in main.spec for PyInstaller name mapping
    if os.path.exists(SPEC_FILE):
        with open(SPEC_FILE, 'r', encoding='utf-8') as f:
            spec_content = f.read()
        new_spec = spec_content.replace(f"VERSION = '{old_v}'", f"VERSION = '{new_v}'")
        with open(SPEC_FILE, 'w', encoding='utf-8') as f:
            f.write(new_spec)

def main():
    print("====================================")
    print(" EMPAQUETADOR DE MINECRAFT LAUNCHER ")
    print("====================================\n")
    
    current_version, content = load_version()
    
    if content is None:
        print(f"[X] Error: No se encontró el archivo '{SPEC_FILE}'. Asegúrate de ejecutar este script desde la raíz del proyecto.")
        sys.exit(1)
        
    if not current_version:
        print(f"[X] Error: No se encontró la variable VERSION='...' en {SPEC_FILE}")
        sys.exit(1)
        
    print(f"Versión Actual: {current_version}")
    parts = current_version.split('.')
    
    # Adaptive padding detection
    paddings = [len(p) for p in parts]
    
    print("\n¿Qué tipo de actualización vas a empaquetar hoy?")
    print(" [1] Actualización Grande   (Sube X, resetea el resto)")
    print(" [2] Actualización Mediana  (Sube Y, resetea parches)")
    print(" [3] Parche / Fix           (Sube Z)")
    print(" [4] Mantener Versión       (Empaquetar con la misma versión)")
    print(" [0] Cancelar y Salir")
    
    try:
        choice = input("\nSelecciona una opción [0-4]: ").strip()
        
        if choice == '0':
            print("\nProceso cancelado.")
            sys.exit(0)
            
        new_parts = [int(p) for p in parts]
        tipo = "MANUAL/MISMA"
        
        if choice == '1':
            new_parts[0] += 1
            for i in range(1, len(new_parts)): new_parts[i] = 0
            tipo = "GRANDE"
        elif choice == '2':
            if len(new_parts) > 1:
                new_parts[1] += 1
                for i in range(2, len(new_parts)): new_parts[i] = 0
            tipo = "MEDIANA"
        elif choice == '3':
            new_parts[-1] += 1
            tipo = "PARCHE"
        elif choice == '4':
            tipo = "MANTENER"
        else:
            print("\n[X] Opción no válida.")
            sys.exit(1)
            
        # Reconstruct with simple x.x.x format (no padding as requested)
        new_version = ".".join(str(p) for p in new_parts)
        
        tipo_str = f"Actualización {tipo}" if choice != '4' else "Mantenimiento"
        print(f"\nGenerando {tipo_str} -> Versión de Compilación: {new_version}")

        # Ejecutar PyInstaller usando el mismo intérprete de Python
        exe_name = f"MinecraftLauncher_v{new_version}.exe"
        print(f"\n[>] Iniciando PyInstaller para generar: {exe_name}")
        print("--------------------------------------------------\n")
        
        # Pasamos la versión por variable de entorno para que el .spec la lea
        env = os.environ.copy()
        env["BUILD_VERSION"] = new_version
        
        import subprocess
        py_path = sys.executable
        # Usamos subprocess para manejar mejor el entorno y la captura
        process = subprocess.Popen(
            [py_path, "-m", "PyInstaller", SPEC_FILE, "-y"],
            env=env
        )
        exit_code = process.wait()
        
        if exit_code == 0:
            if choice != '4':
                save_version(content, current_version, new_version)
                print(f"\n[✓] Versión '{new_version}' guardada en core/info.py.")
            
            print("\n====================================")
            print(f"¡EMPAQUETADO FINALIZADO CON ÉXITO!")
            print(f"Tu ejecutable está ubicado en la carpeta 'dist/'")
            print(f"Archivo: {exe_name}")
            print("====================================")
        else:
            print(f"\n[X] Hubo un error durante la compilación ({exit_code}).")
            print("LA VERSIÓN NO HA SIDO ACTUALIZADA debído al fallo.")
            
    except KeyboardInterrupt:
        print("\n\nOperación cancelada por teclado.")
        sys.exit(0)
    except Exception as e:
        print(f"\n[X] Error fatal: {e}")

if __name__ == '__main__':
    main()
