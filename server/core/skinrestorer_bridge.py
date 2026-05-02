from sqlalchemy.orm import Session
from typing import Optional

# Import robusto: funciona tanto con 'server/' como entry point como con el proyecto raíz
try:
    from database.models.skinrestorer import SkinRestorerSkin, SkinRestorerPlayer
except ImportError:
    from server.database.models.skinrestorer import SkinRestorerSkin, SkinRestorerPlayer


def get_skin_base64_from_skinrestorer(db: Session, player_name: str) -> Optional[str]:
    """
    Consulta la skin usando SQLAlchemy ORM.
    """
    try:
        player_skin = db.query(SkinRestorerPlayer).filter(SkinRestorerPlayer.Nick == player_name).first()
        if not player_skin:
            return None
        skin = db.query(SkinRestorerSkin).filter(SkinRestorerSkin.Name == player_skin.Skin).first()
        return skin.Value if skin else None
    except Exception as e:
        print(f"Error consultando SkinRestorer ORM: {e}")
        return None


def set_skin_in_skinrestorer(db: Session, player_name: str, skin_value: str, signature: str = "") -> bool:
    """
    Actualiza la skin usando SQLAlchemy ORM y la sesion actual.
    """
    try:
        skin_name = f"custom_{player_name}"

        # 1. Upsert Skin
        skin = db.query(SkinRestorerSkin).filter(SkinRestorerSkin.Name == skin_name).first()
        if not skin:
            skin = SkinRestorerSkin(Name=skin_name)
            db.add(skin)

        skin.Value = skin_value
        skin.Signature = signature
        skin.Timestamp = "none"

        # 2. Upsert Player mapping
        player_map = db.query(SkinRestorerPlayer).filter(SkinRestorerPlayer.Nick == player_name).first()
        if not player_map:
            player_map = SkinRestorerPlayer(Nick=player_name)
            db.add(player_map)

        player_map.Skin = skin_name
        db.flush()  # Sincronizar con la DB sin cerrar la transaccion principal
        return True
    except Exception as e:
        print(f"Error actualizando SkinRestorer ORM: {e}")
        return False


class SkinRestorerBridge:
    """Wrapper de clase para compatibilidad con bridge.py."""
    def __init__(self, db: Session):
        self.db = db

    def save_skin(self, player_name: str, value: str, signature: str) -> bool:
        return set_skin_in_skinrestorer(self.db, player_name, value, signature)

    def get_skin(self, player_name: str) -> Optional[str]:
        return get_skin_base64_from_skinrestorer(self.db, player_name)
