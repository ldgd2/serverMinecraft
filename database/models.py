from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text, MetaData
from sqlalchemy.orm import declarative_base
import datetime
import enum

# NAMING CONVENTION: The key to cross-database generic migrations
# This ensures constraints (FKs, PKs, Checks) have deterministic names.
convention = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}

metadata = MetaData(naming_convention=convention)
Base = declarative_base(metadata=metadata)

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    is_admin = Column(Boolean, default=True)

class Server(Base):
    __tablename__ = "servers"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    version = Column(String)
    port = Column(Integer, unique=True)
    ram_mb = Column(Integer)
    status = Column(String, default="OFFLINE") # OFFLINE, STARTING, ONLINE, STOPPING
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    
    # Configuration for offline mode, etc. stored as JSON or separate fields?
    # Simple separate fields for key configs
    online_mode = Column(Boolean, default=False) 
    motd = Column(String, default="A Minecraft Server")
    max_players = Column(Integer, default=20)

class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
    username = Column(String)
    action = Column(String) # e.g., "START_SERVER", "EDIT_FILE"
    details = Column(Text)
