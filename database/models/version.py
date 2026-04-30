from sqlalchemy import Column, Integer, String, Boolean
from database.models.base import Base

class Version(Base):
    __tablename__ = "versions"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=True) # Optional display name
    type = Column(String, nullable=True) # Old type field
    url = Column(String, nullable=True) # Old url field
    downloaded = Column(Boolean, default=False)
    
    # New fields
    loader_type = Column(String) # VANILLA, PAPER, FORGE, FABRIC
    mc_version = Column(String) # 1.20.1
    loader_version = Column(String) # Build ID or Loader Version
    local_path = Column(String) # Path to jar
    file_size = Column(Integer)
    sha256 = Column(String)
