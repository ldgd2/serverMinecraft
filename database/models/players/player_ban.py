from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKeyConstraint
from sqlalchemy.orm import relationship
from database.models.base import Base
import datetime

class PlayerBan(Base):
    __tablename__ = "player_bans"

    id = Column(Integer, primary_key=True, index=True)
    
    player_uuid = Column(String, nullable=False)
    server_id = Column(Integer, nullable=False)
    
    is_active = Column(Boolean, default=True)
    reason = Column(String)
    source = Column(String, default="Console")
    issued_at = Column(DateTime, default=datetime.datetime.utcnow)
    expires_at = Column(DateTime, nullable=True) # Null = Permanent

    __table_args__ = (
        ForeignKeyConstraint(
            ['player_uuid', 'server_id'], 
            ['players.uuid', 'players.server_id'],
            name='fk_player_bans_player'
        ),
    )

    player = relationship("Player", back_populates="bans")
