import os
import sys

# Añadir el directorio actual al path
sys.path.append(os.getcwd())

from sqlalchemy.orm import Session
from database.connection import SessionLocal
from database.models.players.player_achievement import PlayerAchievement

def cleanup():
    db = SessionLocal()
    try:
        # WHITELIST: Solo permitimos estos prefijos de logros especiales/sociales
        valid_prefixes = [
            "LOGIN_", "STREAK_", "NIGHT_OWL", "EARLY_BIRD", "FOUNDER",
            "SESSION_", "TOTEM_", "RAID_", "AFK_", "TRADER_", "MAINTENANCE_",
            "DRAGON_EGG", "GOD_OF_WAR", "MOUNT_MASTER", "HUNGER_GAMES",
            "WHAT_NOW", "WTF_IS_THAT", "YOU_ARE_GOOD", "EVEREST", "FEAR_PARALYSIS",
            "GHAST_RETURN", "CLUTCH_SURVIVAL", "NETHER_SLEEP", "STRIDER_TAXI",
            "MANY_EFFECTS", "SNIPER_DUEL", "CACTUS_FAIL", "VANDALISM",
            "MEME_", "GAIN_FIRST_XP", "DIST_", "TIME_", "PHILO_"
        ]
        
        print("Iniciando purga agresiva de logros intrusivos...")

        # Buscar todos los logros
        query = db.query(PlayerAchievement)
        to_delete = []
        
        for ach in query.all():
            is_valid = False
            for prefix in valid_prefixes:
                if ach.achievement_id.startswith(prefix):
                    is_valid = True
                    break
            
            # Si no está en la whitelist, es basura intrusiva
            if not is_valid:
                to_delete.append(ach)

        if not to_delete:
            print("Base de datos ya esta limpia y solo contiene logros especiales.")
            return

        print(f"Se eliminaran {len(to_delete)} logros irrelevantes o intrusivos.")
        
        for ach in to_delete:
            print(f"  - Borrando: {ach.achievement_id}")
            db.delete(ach)
        
        db.commit()
        print(f"Limpieza agresiva completada! Tu servidor ahora solo procesa logros de alto valor.")

    except Exception as e:
        print(f"Error: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    cleanup()
