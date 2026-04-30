from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Index, UniqueConstraint
from sqlalchemy.orm import relationship
from database.models.base import Base
import datetime

class Player(Base):
    __tablename__ = "players"

    id = Column(Integer, primary_key=True, autoincrement=True)  # General PK
    server_id = Column(Integer, ForeignKey("servers.id"), nullable=False, index=True)
    uuid = Column(String, nullable=True, index=True)  # Puede ser null para no premium
    name = Column(String, index=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    __table_args__ = (
        UniqueConstraint('id', 'server_id', name='uq_player_id_server'),
    )

    # Relationships
    detail = relationship("PlayerDetail", uselist=False, back_populates="player", cascade="all, delete-orphan")
    stats = relationship("PlayerStat", back_populates="player", cascade="all, delete-orphan")
    bans = relationship("PlayerBan", back_populates="player", cascade="all, delete-orphan")
    achievements = relationship("PlayerAchievement", back_populates="player", cascade="all, delete-orphan")
