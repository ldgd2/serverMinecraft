import sys
import os

# Añadir el directorio raíz al path para importar modelos
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.connection import SessionLocal
from database.models.players.player_achievement import PlayerAchievement
from app.services.achievements.registry import ACHIEVEMENTS_REGISTRY

def cleanup():
    db = SessionLocal()
    try:
        # 1. Obtener todos los IDs de logros válidos
        valid_ids = [ach.id for ach in ACHIEVEMENTS_REGISTRY]
        print(f"Valid IDs: {len(valid_ids)}")

        total_count = db.query(PlayerAchievement).count()
        print(f"Total achievements in database: {total_count}")
        # Estos suelen ser códigos técnicos como "block_broken:..." o basura de debug
        to_delete = db.query(PlayerAchievement).filter(
            ~PlayerAchievement.achievement_id.in_(valid_ids)
        ).all()

        count = len(to_delete)
        if count == 0:
            print("No irrelevant achievements found. Database is clean!")
            return

        print(f"Found {count} irrelevant achievements to delete.")
        
        # Opcional: mostrar algunos ejemplos antes de borrar
        for ach in to_delete[:5]:
            print(f"  - Removing: {ach.achievement_id} ('{ach.name}') for player ID {ach.player_id}")

        # 3. Proceder al borrado
        db.query(PlayerAchievement).filter(
            ~PlayerAchievement.achievement_id.in_(valid_ids)
        ).delete(synchronize_session=False)
        
        db.commit()
        print(f"Successfully deleted {count} achievements.")

    except Exception as e:
        db.rollback()
        print(f"Error during cleanup: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    cleanup()
