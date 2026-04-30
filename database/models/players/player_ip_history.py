from sqlalchemy import Column, Integer, String, DateTime, ForeignKeyConstraint
from sqlalchemy.orm import relationship
from database.models.base import Base
import datetime

class PlayerIPHistory(Base):
    __tablename__ = "player_ip_history"

    id = Column(Integer, primary_key=True, index=True)
    player_id = Column(Integer, nullable=False)
    server_id = Column(Integer, nullable=False)
    ip_address = Column(String, nullable=False)
    country = Column(String, nullable=True)
    joined_at = Column(DateTime, default=datetime.datetime.utcnow)

    __table_args__ = (
        ForeignKeyConstraint(
            ['player_id', 'server_id'],
            ['players.id', 'players.server_id'],
            name='fk_player_ip_history_player'
        ),
    )
