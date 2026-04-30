from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from database.models.base import Base

class PlayerStat(Base):
    __tablename__ = "player_stats"

    id = Column(Integer, primary_key=True, index=True)
    player_id = Column(Integer, ForeignKey("players.id"), nullable=False)
    
    stat_key = Column(String, index=True)
    stat_value = Column(Integer, default=0)

    player = relationship("Player", back_populates="stats")
