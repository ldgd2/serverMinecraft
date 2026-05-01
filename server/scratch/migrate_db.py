import sys
import os
import psycopg2

# Añadir el directorio actual al path
sys.path.append(os.getcwd())

from dotenv import load_dotenv
load_dotenv()

def migrate():
    print("Iniciando migracion (sin tildes)...")
    
    # Obtener credenciales del .env
    db_name = os.getenv("DB_NAME")
    db_user = os.getenv("DB_USER")
    db_pass = os.getenv("DB_PASSWORD")
    db_host = os.getenv("DB_HOST")
    db_port = os.getenv("DB_PORT")

    try:
        # Conexión directa con psycopg2
        conn = psycopg2.connect(
            dbname=db_name,
            user=db_user,
            password=db_pass,
            host=db_host,
            port=db_port
        )
        conn.autocommit = True
        cur = conn.cursor()

        print("Conectado a la base de datos.")
        
        # Ejecutar comandos SQL directamente
        try:
            cur.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS api_key_encrypted VARCHAR;")
            print("Columna api_key_encrypted verificada/añadida.")
        except Exception as e:
            print(f"Error en api_key_encrypted: {e}")

        try:
            cur.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS api_key_hashed VARCHAR;")
            print("Columna api_key_hashed verificada/añadida.")
        except Exception as e:
            print(f"Error en api_key_hashed: {e}")

        cur.close()
        conn.close()
        print("✅ Migracion completada exitosamente.")
        
    except Exception as e:
        print(f"❌ Error de conexion: {e}")

if __name__ == "__main__":
    migrate()
