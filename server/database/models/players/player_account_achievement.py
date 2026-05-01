from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from database.models.base import Base
import datetime

class PlayerAccountAchievement(Base):
    """Logros globales (cross-server) del jugador."""
    __tablename__ = "player_account_achievements"

    id = Column(Integer, primary_key=True, autoincrement=True)
    account_id = Column(Integer, ForeignKey("player_accounts.id"), nullable=False)

    achievement_key = Column(String, nullable=False)   # e.g. "first_kill", "100_blocks"
    name = Column(String, nullable=True)
    description = Column(String, nullable=True)
    icon = Column(String, nullable=True)               # emoji or icon name
    unlocked_at = Column(DateTime, default=datetime.datetime.utcnow)
    server_name = Column(String, nullable=True)        # en qué servidor se desbloqueó

    account = relationship("PlayerAccount", back_populates="achievements")
