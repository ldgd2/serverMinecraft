import os
import sys

# Add the server directory to the path so we can import database modules
sys.path.append(os.path.join(os.getcwd(), "server"))

from database.connection import get_engine
from sqlalchemy import text

def fix_schema():
    engine = get_engine()
    print(f"Connecting to database to fix schema...")
    
    queries = [
        "ALTER TABLE player_accounts ADD COLUMN IF NOT EXISTS total_player_kills INTEGER DEFAULT 0;",
        "ALTER TABLE player_accounts ADD COLUMN IF NOT EXISTS total_hostile_kills INTEGER DEFAULT 0;",
        "ALTER TABLE player_accounts ADD COLUMN IF NOT EXISTS total_genocide_score INTEGER DEFAULT 0;"
    ]
    
    with engine.connect() as conn:
        for query in queries:
            try:
                print(f"Executing: {query}")
                conn.execute(text(query))
                conn.commit()
                print("Success.")
            except Exception as e:
                print(f"Error executing query: {e}")

if __name__ == "__main__":
    fix_schema()
