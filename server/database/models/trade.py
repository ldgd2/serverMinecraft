from sqlalchemy import Column, Integer, String, JSON, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from . import Base
from datetime import datetime

class Trade(Base):
    __tablename__ = "trades"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=True)
    seller_uuid = Column(String, index=True)
    seller_name = Column(String)
    
    # El item que se vende: {id, count, nbt}
    selling_item = Column(JSON)
    
    # El item que se pide originalmente: {id, count}
    asking_item = Column(JSON)
    
    status = Column(String, default="OPEN") # OPEN, PENDING, COMPLETED, CANCELLED
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relación con las contra-ofertas
    offers = relationship("CounterOffer", back_populates="trade")

class CounterOffer(Base):
    __tablename__ = "counter_offers"
    id = Column(Integer, primary_key=True, index=True)
    trade_id = Column(Integer, ForeignKey("trades.id"))
    buyer_uuid = Column(String)
    buyer_name = Column(String)
    
    # Lista de items ofrecidos: [{id, count, nbt}, ...]
    offered_items = Column(JSON)
    
    status = Column(String, default="PENDING") # PENDING, ACCEPTED, REJECTED
    rejection_reason = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    trade = relationship("Trade", back_populates="offers")
