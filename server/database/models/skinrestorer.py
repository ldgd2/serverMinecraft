from sqlalchemy import Column, Integer, String, Text
from . import Base

class SkinRestorerSkin(Base):
    """Modelo compatible con la tabla 'Skins' de SkinRestorer"""
    __tablename__ = 'Skins'
    __table_args__ = {'quote': True} # Para asegurar mayúsculas en Postgres
    
    ID = Column(Integer, primary_key=True, autoincrement=True)
    Name = Column(String(255), unique=True, nullable=False)
    Value = Column(Text, nullable=False)
    Signature = Column(Text, nullable=False)
    Timestamp = Column(String(255), nullable=False)

class SkinRestorerPlayer(Base):
    """Modelo compatible con la tabla 'Players' de SkinRestorer"""
    __tablename__ = 'Players'
    __table_args__ = {'quote': True}
    
    ID = Column(Integer, primary_key=True, autoincrement=True)
    Nick = Column(String(255), unique=True, nullable=False)
    Skin = Column(String(255), nullable=False)
