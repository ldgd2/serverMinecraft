from sqlalchemy import Column, Integer, String, DateTime, ForeignKeyConstraint
from sqlalchemy.orm import relationship
from database.models.base import Base
import datetime

class PlayerAchievement(Base):
    __tablename__ = "player_achievements"

    id = Column(Integer, primary_key=True, index=True)
    
    player_uuid = Column(String, nullable=False)
    server_id = Column(Integer, nullable=False)
    
    achievement_id = Column(String) # e.g. "story/mine_stone"
    name = Column(String, nullable=True) # Display name if available
    description = Column(String, nullable=True)
    unlocked_at = Column(DateTime, default=datetime.datetime.utcnow)

    __table_args__ = (
        ForeignKeyConstraint(
            ['player_uuid', 'server_id'], 
            ['players.uuid', 'players.server_id'],
            name='fk_player_achievements_player'
        ),
    )

    player = relationship("Player", back_populates="achievements")
