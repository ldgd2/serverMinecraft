"""
Server Seeder
Seeds sample Minecraft servers into the database
"""
from database.connection import SessionLocal
from database.models.server import Server
import datetime


def seed_servers():
    """Seed the servers table with sample data"""
    db = SessionLocal()
    
    try:
        if not db.query(Server).first():
            print("Seeding Servers...")
            
            servers = [
                Server(
                    name="Survival",
                    version="1.20.4",
                    port=25565,
                    ram_mb=2048,
                    status="OFFLINE",
                    created_at=datetime.datetime.utcnow(),
                    online_mode=True,
                    motd="§a§lSurvival Server §7- §eBienvenido!",
                    max_players=20
                ),
                Server(
                    name="Creative",
                    version="1.20.4",
                    port=25566,
                    ram_mb=1024,
                    status="OFFLINE",
                    created_at=datetime.datetime.utcnow(),
                    online_mode=False,
                    motd="§b§lCreative Mode §7- §eConstruye sin limites!",
                    max_players=10
                ),
                Server(
                    name="Minigames",
                    version="1.20.4",
                    port=25567,
                    ram_mb=4096,
                    status="OFFLINE",
                    created_at=datetime.datetime.utcnow(),
                    online_mode=True,
                    motd="§6§lMinigames §7- §eDiversion garantizada!",
                    max_players=50
                )
            ]
            
            for server in servers:
                db.add(server)
            
            db.commit()
            print(f"Seeded {len(servers)} servers successfully.")
        else:
            print("Servers already exist. Skipping seed.")
    except Exception as e:
        print(f"Error seeding servers: {e}")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    seed_servers()
