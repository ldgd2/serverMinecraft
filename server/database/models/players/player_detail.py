from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from database.models.base import Base
import datetime

class PlayerDetail(Base):
    __tablename__ = "player_details"

    player_id = Column(Integer, ForeignKey("players.id"), primary_key=True)

    total_playtime_seconds = Column(Integer, default=0)
    last_joined_at = Column(DateTime)
    last_ip = Column(String, nullable=True)
    country = Column(String, nullable=True)
    os = Column(String, nullable=True)
    skin_url = Column(String, nullable=True)          # URL pública de la cabeza
    skin_base64 = Column(String, nullable=True)       # PNG raw del launcher
    skin_value = Column(Text, nullable=True)          # Base64 textura firmada (Mojang/MineSkin)
    skin_signature = Column(Text, nullable=True)      # Firma criptográfica de la textura
    skin_last_update = Column(DateTime, nullable=True)
    birthday = Column(String, nullable=True)

    health = Column(Integer, default=20)
    xp_level = Column(Integer, default=0)
    position_x = Column(Integer, default=0)
    position_y = Column(Integer, default=0)
    position_z = Column(Integer, default=0)

    player = relationship("Player", back_populates="detail")
