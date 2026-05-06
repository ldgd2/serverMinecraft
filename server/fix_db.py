import os
import sys
from sqlalchemy import text
from database.connection import get_engine

def fix_database():
    print("🚀 Inciando reparación de la base de datos...")
    engine = get_engine()
    
    # Lista de columnas a añadir
    columns_to_add = [
        ("masterbridge_enabled", "BOOLEAN DEFAULT TRUE"),
        ("masterbridge_ip", "VARCHAR DEFAULT '127.0.0.1'"),
        ("masterbridge_port", "INTEGER DEFAULT 8081")
    ]
    
    with engine.connect() as conn:
        for col_name, col_type in columns_to_add:
            print(f"  [>] Verificando columna '{col_name}'...")
            try:
                # Intentar añadir la columna
                conn.execute(text(f"ALTER TABLE servers ADD COLUMN {col_name} {col_type}"))
                conn.commit()
                print(f"  [✓] Columna '{col_name}' añadida con éxito.")
            except Exception as e:
                # Si ya existe, ignoramos el error
                if "already exists" in str(e).lower() or "duplicate column" in str(e).lower():
                    print(f"  [!] La columna '{col_name}' ya existe. Saltando...")
                else:
                    print(f"  [X] Error al añadir '{col_name}': {e}")
        
        print("\n✅ Reparación completada. Reinicia el servicio para aplicar los cambios.")

if __name__ == "__main__":
    # Asegurarnos de estar en el directorio correcto para cargar .env
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    fix_database()
