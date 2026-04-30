"""
Bitacora Seeder
Seeds sample log entries into the database
"""
from database.connection import SessionLocal
from database.models.bitacora import Bitacora
import datetime


def seed_bitacora():
    """Seed the bitacora table with sample data"""
    db = SessionLocal()
    
    try:
        if not db.query(Bitacora).first():
            print("Seeding Bitacora...")
            
            logs = [
                Bitacora(
                    timestamp=datetime.datetime.utcnow(),
                    username="system",
                    action="SYSTEM_INIT",
                    details="Sistema inicializado correctamente"
                ),
                Bitacora(
                    timestamp=datetime.datetime.utcnow(),
                    username="admin",
                    action="USER_LOGIN",
                    details="Usuario admin inicio sesion"
                ),
                Bitacora(
                    timestamp=datetime.datetime.utcnow(),
                    username="admin",
                    action="SERVER_CREATE",
                    details="Servidor 'Survival' creado exitosamente"
                )
            ]
            
            for log in logs:
                db.add(log)
            
            db.commit()
            print(f"Seeded {len(logs)} log entries successfully.")
        else:
            print("Bitacora already has entries. Skipping seed.")
    except Exception as e:
        print(f"Error seeding bitacora: {e}")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    seed_bitacora()
