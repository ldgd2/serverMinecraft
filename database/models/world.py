from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from database.models.base import Base
import datetime

class World(Base):
    __tablename__ = "worlds"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    seed = Column(String, nullable=True)
    original_version = Column(String, nullable=True)  # Version when world was created
    last_used_version = Column(String, nullable=True)  # Last version used to play
    local_path = Column(String, nullable=True)  # Path in source/worlds/
    size_mb = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    
    # Relationship to servers through junction table
    servers = relationship("ServerWorld", back_populates="world")


class ServerWorld(Base):
    """Junction table for many-to-many relationship between servers and worlds"""
    __tablename__ = "server_worlds"

    id = Column(Integer, primary_key=True)
    server_id = Column(Integer, ForeignKey('servers.id'), nullable=False)
    world_id = Column(Integer, ForeignKey('worlds.id'), nullable=False)
    copied_at = Column(DateTime, default=datetime.datetime.utcnow)
    
    # Relationships
    world = relationship("World", back_populates="servers")
