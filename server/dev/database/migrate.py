import sys
import os
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Add the server directory to the path so we can import models
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

try:
    from database.connection import get_connection_url
    from database.models.server import Server
except ImportError:
    print("Error: Could not import database configuration. Are you running this from the server/dev/database directory?")
    sys.exit(1)

def migrate():
    """Manually add missing columns to the database"""
    print(f"Connecting to database...")
    engine = create_engine(get_connection_url())
    
    with engine.connect() as conn:
        print("Checking for missing columns in 'servers' table...")
        
        # Check if user_id exists
        result = conn.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name='servers' AND column_name='user_id'"))
        if not result.fetchone():
            print("➕ Adding 'user_id' column to 'servers' table...")
            try:
                conn.execute(text("ALTER TABLE servers ADD COLUMN user_id INTEGER REFERENCES users(id)"))
                conn.commit()
                print("Successfully added 'user_id' column.")
            except Exception as e:
                print(f"Failed to add 'user_id': {e}")
        else:
            print("'user_id' column already exists.")

        # Check for other potential missing columns from recent updates
        columns_to_check = [
            ("online_mode", "BOOLEAN DEFAULT FALSE"),
            ("motd", "VARCHAR DEFAULT 'A Minecraft Server'"),
            ("max_players", "INTEGER DEFAULT 20"),
            ("mod_loader", "VARCHAR DEFAULT 'VANILLA'"),
            ("cpu_cores", "FLOAT DEFAULT 1.0"),
            ("disk_mb", "INTEGER DEFAULT 2048"),
            ("current_players", "INTEGER DEFAULT 0"),
            ("cpu_usage", "FLOAT DEFAULT 0.0"),
            ("ram_usage", "INTEGER DEFAULT 0"),
            ("disk_usage", "INTEGER DEFAULT 0"),
        ]

        for col_name, col_type in columns_to_check:
            result = conn.execute(text(f"SELECT column_name FROM information_schema.columns WHERE table_name='servers' AND column_name='{col_name}'"))
            if not result.fetchone():
                print(f"➕ Adding '{col_name}' column to 'servers' table...")
                try:
                    conn.execute(text(f"ALTER TABLE servers ADD COLUMN {col_name} {col_type}"))
                    conn.commit()
                    print(f"Successfully added '{col_name}' column.")
                except Exception as e:
                    print(f"Failed to add '{col_name}': {e}")
            else:
                print(f"'{col_name}' column already exists.")

    print("\nDatabase migration complete!")

if __name__ == "__main__":
    migrate()
