from sqlalchemy import Column, Integer, String, ForeignKeyConstraint
from sqlalchemy.orm import relationship
from database.models.base import Base

class PlayerStat(Base):
    __tablename__ = "player_stats"

    id = Column(Integer, primary_key=True, index=True)
    
    player_uuid = Column(String, nullable=False)
    server_id = Column(Integer, nullable=False)
    
    stat_key = Column(String, index=True) # e.g. "jumps", "mined.stone"
    stat_value = Column(Integer, default=0)

    __table_args__ = (
        ForeignKeyConstraint(
            ['player_uuid', 'server_id'], 
            ['players.uuid', 'players.server_id'],
            name='fk_player_stats_player'
        ),
    )

    player = relationship("Player", back_populates="stats")
