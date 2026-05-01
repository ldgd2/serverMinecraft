import os
import sys

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database.connection import get_engine
from database.models import Base

def init_db():
    print("🚀 Initializing Database...")
    engine = get_engine()
    
    # Import all models explicitly to ensure they are registered with Base
    from database.models.user import User
    from database.models.server import Server
    from database.models.players.player_account import PlayerAccount
    from database.models.players.player_stat import PlayerStat
    from database.models.players.player_achievement import PlayerAchievement
    
    print(f"📡 Connecting to: {engine.url.render_as_string(hide_password=True)}")
    
    try:
        # This will create all tables defined in models that don't exist yet
        Base.metadata.create_all(bind=engine)
        print("✅ Database tables synchronized successfully!")
    except Exception as e:
        print(f"❌ Error initializing database: {e}")

if __name__ == "__main__":
    init_db()
