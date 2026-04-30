from sqlalchemy import Column, Integer, String, Boolean, DateTime
from database.models.base import Base
import datetime

class ModLoader(Base):
    __tablename__ = "mod_loaders"

    id = Column(Integer, primary_key=True, index=True)
    type = Column(String, nullable=False)  # FORGE, FABRIC, PAPER, VANILLA
    minecraft_version = Column(String, nullable=False)
    loader_version = Column(String, nullable=True)
    download_url = Column(String, nullable=True)
    local_path = Column(String, nullable=True)  # e.g. source/forge/1.20.4/forge-installer.jar
    downloaded = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
