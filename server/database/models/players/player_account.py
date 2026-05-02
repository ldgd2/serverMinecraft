from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from database.models.base import Base
import datetime

class PlayerAccount(Base):
    """
    Cuenta de autenticación para jugadores del launcher.
    Separada del modelo User (admins) para no mezclar roles.
    Un jugador puede estar asociado a múltiples servidores (Player).
    """
    __tablename__ = "player_accounts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String, unique=True, nullable=False, index=True)
    hashed_password = Column(String, nullable=True)  # Null si es cuenta premium (Microsoft)
    
    # Identidad Minecraft
    uuid = Column(String, nullable=True, unique=True, index=True)  # UUID oficial de Mojang (premium)
    account_type = Column(String, default="nopremium")  # "nopremium", "premium", "guest"
    
    # Estadísticas globales (cross-server)
    total_playtime_seconds = Column(Integer, default=0)
    total_kills = Column(Integer, default=0)
    total_deaths = Column(Integer, default=0)
    total_blocks_broken = Column(Integer, default=0)
    total_blocks_placed = Column(Integer, default=0)
    best_kill_streak = Column(Integer, default=0)
    
    # Nuevas estadísticas detalladas
    total_player_kills = Column(Integer, default=0)
    total_hostile_kills = Column(Integer, default=0)
    total_genocide_score = Column(Integer, default=0)
    
    highlights = Column(JSON, default=[]) 
    
    # Tokens para premium
    microsoft_refresh_token = Column(String, nullable=True)
    minecraft_access_token = Column(String, nullable=True)
    
    is_active = Column(Boolean, default=True)
    is_banned = Column(Boolean, default=False)
    ban_reason = Column(String, nullable=True)
    
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    last_login_at = Column(DateTime, nullable=True)
    
    # Relationships
    achievements = relationship("PlayerAccountAchievement", back_populates="account", cascade="all, delete-orphan")
