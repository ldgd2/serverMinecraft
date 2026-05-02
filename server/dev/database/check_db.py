import sys
import os
from sqlalchemy import create_engine, text

# Add the server directory to the path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

try:
    from database.connection import get_connection_url
except ImportError:
    print("Error: Could not import database configuration.")
    sys.exit(1)

def check_servers():
    engine = create_engine(get_connection_url())
    with engine.connect() as conn:
        result = conn.execute(text("SELECT id, name, status FROM servers"))
        rows = result.fetchall()
        print(f"Total servers found: {len(rows)}")
        for row in rows:
            print(f"ID: {row[0]} | Name: '{row[1]}' | Status: {row[2]}")
            # Check for hidden characters or case
            if row[1] != row[1].strip():
                print(f"  WARNING: Name '{row[1]}' has leading/trailing spaces!")

if __name__ == "__main__":
    check_servers()
