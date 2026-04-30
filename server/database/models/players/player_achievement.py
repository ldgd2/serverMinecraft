from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from database.models.base import Base
import datetime

class PlayerAchievement(Base):
    __tablename__ = "player_achievements"

    id = Column(Integer, primary_key=True, index=True)
    player_id = Column(Integer, ForeignKey("players.id"), nullable=False)
    
    achievement_id = Column(String)
    name = Column(String, nullable=True)
    description = Column(String, nullable=True)
    unlocked_at = Column(DateTime, default=datetime.datetime.utcnow)

    player = relationship("Player", back_populates="achievements")
