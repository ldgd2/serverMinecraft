import sqlite3
import os

db_path = os.path.join("database", "instance", "minecraft_manager.db")

print(f"Migrating {db_path}...")
try:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("ALTER TABLE servers ADD COLUMN masterbridge_config TEXT DEFAULT '{}'")
    conn.commit()
    conn.close()
    print("Migration successful: Added masterbridge_config column.")
except sqlite3.OperationalError as e:
    if "duplicate column name" in str(e):
        print("Column masterbridge_config already exists.")
    else:
        print(f"Migration failed: {e}")
