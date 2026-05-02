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

def check_achievements():
    engine = create_engine(get_connection_url())
    with engine.connect() as conn:
        print("--- Global Achievements (PlayerAccountAchievement) ---")
        res = conn.execute(text("SELECT id, account_id, achievement_key, name FROM player_account_achievements"))
        for row in res:
            print(f"ID: {row[0]} | Account: {row[1]} | Key: {row[2]} | Name: {row[3]}")
            
        print("\n--- Server Achievements (PlayerAchievement) ---")
        res = conn.execute(text("SELECT id, player_id, achievement_id, name FROM player_achievements"))
        for row in res:
            print(f"ID: {row[0]} | Player: {row[1]} | ID: {row[2]} | Name: {row[3]}")

        print("\n--- Players (Player) ---")
        res = conn.execute(text("SELECT id, name, uuid FROM players"))
        for row in res:
            print(f"ID: {row[0]} | Name: '{row[1]}' | UUID: {row[2]}")

if __name__ == "__main__":
    check_achievements()
