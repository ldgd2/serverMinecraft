from sqlalchemy import Column, Integer, String, DateTime, Text
from database.models.base import Base
import datetime

class Bitacora(Base):
    __tablename__ = "bitacora"

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
    username = Column(String)
    action = Column(String)
    ip_address = Column(String)
    details = Column(Text)
    severity = Column(String, default="COMMON") # COMMON, CRITICAL, VERY_CRITICAL
