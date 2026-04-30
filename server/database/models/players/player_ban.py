from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from database.models.base import Base
import datetime

class PlayerBan(Base):
    __tablename__ = "player_bans"

    id = Column(Integer, primary_key=True, index=True)
    player_id = Column(Integer, ForeignKey("players.id"), nullable=False)
    
    is_active = Column(Boolean, default=True)
    reason = Column(String)
    source = Column(String, default="Console")
    issued_at = Column(DateTime, default=datetime.datetime.utcnow)
    expires_at = Column(DateTime, nullable=True)

    player = relationship("Player", back_populates="bans")
