from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from database.models.base import Base

class ServerChat(Base):
    __tablename__ = "server_chat"

    id = Column(Integer, primary_key=True, index=True)
    server_id = Column(Integer, ForeignKey("servers.id"), nullable=False, index=True)
    username = Column(String(50), nullable=False)
    message = Column(Text, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    # type: "sent" (by admin), "received" (from game/player - optional for future)
    type = Column(String(20), default="sent") 

    server = relationship("Server", back_populates="chat_history")
    
    def to_dict(self):
        return {
            "id": self.id,
            "user": self.username,
            "text": self.message,
            "time": int(self.timestamp.timestamp() * 1000), # MasterBridge uses ms timestamp
            "type": self.type
        }
