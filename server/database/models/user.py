from sqlalchemy import Column, Integer, String, Boolean
from database.models.base import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    is_admin = Column(Boolean, default=True)
    api_key_encrypted = Column(String, nullable=True) # Para verla desde consola
    api_key_hashed = Column(String, nullable=True, index=True) # Para validación rápida de la API
