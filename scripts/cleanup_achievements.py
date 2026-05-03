import os
import sys
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Add server directory to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'server')))

from database.models.players.player_achievement import PlayerAchievement
from database.connection import get_connection_url

def cleanup():
    db_url = get_connection_url()
    engine = create_engine(db_url)
    Session = sessionmaker(bind=engine)
    session = Session()

    print("[Cleanup] Buscando logros basura...")

    # Logros basura son aquellos que:
    # 1. Tienen IDs técnicos (minecraft:..., item_acquired:..., etc)
    # 2. No tienen nombre legible o tienen el mismo ID como nombre
    # 3. Son logros automáticos de estadísticas (block_broken, chat_message)
    
    technical_prefixes = [
        "minecraft:", 
        "item_acquired:", 
        "block_broken:", 
        "kill:", 
        "death:", 
        "chat_message",
        "stat:",
        "entity_killed:",
        "block_placed:"
    ]

    total_deleted = 0
    
    achievements = session.query(PlayerAchievement).all()
    for ach in achievements:
        is_trash = False
        
        # Regla 1: Prefijos técnicos
        if any(ach.achievement_id.startswith(p) for p in technical_prefixes) if ach.achievement_id else False:
            is_trash = True
            
        # Regla 2: Sin nombre real o nombre = ID
        if not ach.name or ach.name == ach.achievement_id:
            is_trash = True
            
        if is_trash:
            print(f"[-] Eliminando: {ach.achievement_id} ({ach.name})")
            session.delete(ach)
            total_deleted += 1

    session.commit()
    print(f"\n[Cleanup] ¡Limpieza completa! Se eliminaron {total_deleted} registros basura.")
    session.close()

if __name__ == "__main__":
    cleanup()
