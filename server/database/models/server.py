from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, Text, DateTime, Float
from sqlalchemy.orm import relationship
from . import Base
import datetime

class Server(Base):
    __tablename__ = "servers"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    version = Column(String)
    port = Column(Integer, unique=True)
    ram_mb = Column(Integer, default=2048)
    status = Column(String, default="OFFLINE")
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True) # Associated admin
    
    # Server settings
    online_mode = Column(Boolean, default=False) 
    motd = Column(String, default="A Minecraft Server")
    max_players = Column(Integer, default=20)
    
    # Mod loader configuration
    mod_loader = Column(String, default="VANILLA")  # VANILLA, FORGE, FABRIC, PAPER
    
    # Resource allocation
    cpu_cores = Column(Float, default=1.0)
    disk_mb = Column(Integer, default=2048)
    
    chat_history = relationship("ServerChat", back_populates="server", cascade="all, delete-orphan")
    # Runtime stats (updated while running)
    current_players = Column(Integer, default=0)
    cpu_usage = Column(Float, default=0.0)
    ram_usage = Column(Integer, default=0)
    disk_usage = Column(Integer, default=0)
    
    # MasterBridge compatibility (Restored for App UI)
    masterbridge_enabled = Column(Boolean, default=True)
    masterbridge_ip = Column(String, default="127.0.0.1")
    masterbridge_port = Column(Integer, default=8081)
