from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class ServerCreate(BaseModel):
    name: str
    version: str
    ram_mb: Optional[int] = 4096  # Default 4GB for 8GB RAM system
    port: Optional[int] = 25565   # Default port (will auto-assign if taken)
    online_mode: bool = False
    mod_loader: Optional[str] = "vanilla"
    cpu_cores: Optional[float] = 6.0
    disk_mb: Optional[int] = 10000
    max_players: Optional[int] = 20
    motd: Optional[str] = "A Minecraft Server"

class ServerUpdate(BaseModel):
    version: Optional[str] = None
    ram_mb: Optional[int] = None
    port: Optional[int] = None
    online_mode: Optional[bool] = None
    mod_loader: Optional[str] = None
    cpu_cores: Optional[float] = None
    disk_mb: Optional[int] = None
    max_players: Optional[int] = None
    motd: Optional[str] = None
    
    # MasterBridge compatibility (Restored for App UI)
    masterbridge_enabled: Optional[bool] = True
    masterbridge_ip: Optional[str] = "127.0.0.1"
    masterbridge_port: Optional[int] = 8081

class ServerResponse(ServerCreate):
    id: int
    status: str
    created_at: Optional[datetime]
    # Runtime metrics (from model - injected by controller from process stats)
    cpu_usage: Optional[float] = 0.0
    ram_usage: Optional[int] = 0  # Match model field name
    current_players: Optional[int] = 0  # Match model field name
    disk_usage: Optional[int] = 0
    
    # MasterBridge compatibility (Restored for App UI)
    masterbridge_enabled: Optional[bool] = True
    masterbridge_ip: Optional[str] = "127.0.0.1"
    masterbridge_port: Optional[int] = 8081
    
    class Config:
        from_attributes = True

class ServerStats(BaseModel):
    status: str
    cpu: float
    ram: float

class UserResponse(BaseModel):
    id: int
    username: str
    is_admin: bool
    is_active: bool

class Token(BaseModel):
    access_token: str
    token_type: str
    user: Optional[UserResponse] = None

class UserLogin(BaseModel):
    username: str
    password: str

class ModSearchConnect(BaseModel):
    query: str
    version: str

class RegisterRequest(BaseModel):
    username: str
    password: str

class SystemInfo(BaseModel):
    os: str
    cpu_count: int
    cpu_percent: float
    ram_total_mb: int
    ram_used_mb: int
    ram_available_mb: int
    disk_total_mb: int
    disk_used_mb: int
    disk_available_mb: int

class BitacoraEntry(BaseModel):
    id: int
    timestamp: datetime
    username: str
    action: str
    ip_address: Optional[str]
    details: Optional[str]
    severity: Optional[str]

    class Config:
        from_attributes = True

class VersionResponse(BaseModel):
    id: int
    name: Optional[str]
    loader_type: str
    mc_version: str
    loader_version: Optional[str]
    local_path: Optional[str]
    downloaded: bool

    class Config:
        from_attributes = True

class WorldCreate(BaseModel):
    name: str
    seed: Optional[str] = None
    original_version: Optional[str] = None

class WorldResponse(BaseModel):
    id: int
    name: str
    seed: Optional[str]
    original_version: Optional[str]
    last_used_version: Optional[str]
    size_mb: Optional[int]
    created_at: datetime
    
    class Config:
        from_attributes = True

class WorldAssignRequest(BaseModel):
    server_ids: List[int]

class ServerCommandRequest(BaseModel):
    command: str

class BanRequest(BaseModel):
    mode: str = "username"
    reason: str = "Banned by admin"
    expires: str = "forever"

class UpdateBanRequest(BaseModel):
    reason: Optional[str] = None
    expires: Optional[str] = None

class ChatRequest(BaseModel):
    text: str
    formatted: bool = False

class EventRequest(BaseModel):
    type: str
    data: Optional[dict] = None

class CinematicRequest(BaseModel):
    type: str
    target: Optional[str] = None
    difficulty: int = 1

class ParanoiaRequest(BaseModel):
    target: Optional[str] = None
    duration: int = 60

class SpecialEventRequest(BaseModel):
    type: str
    target: Optional[str] = None

class TeleportRequest(BaseModel):
    mode: str # "player_to_player", "player_to_coords", "players_to_player"
    username: Optional[str] = None # For player_to_player or player_to_coords
    target_username: Optional[str] = None # For player_to_player or players_to_player
    x: Optional[float] = None
    y: Optional[float] = None
    z: Optional[float] = None
    players: Optional[List[str]] = None # For players_to_player (can be ["@a"])

