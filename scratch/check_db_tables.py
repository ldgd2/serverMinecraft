import sqlite3
import os

db_path = r"c:\Users\ldgd2\OneDrive\Documentos\Proyectos_lider\python\minecraft_server_manager\server\database\minecraft.db"
if not os.path.exists(db_path):
    print(f"DB not found at {db_path}")
else:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        rows = cursor.fetchall()
        print(f"Tables found: {rows}")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        conn.close()
