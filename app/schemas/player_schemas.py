from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum

# ==================== Enums ====================

class BanDurationTypeEnum(str, Enum):
    """Tipos de duración de ban"""
    PERMANENT = "permanent"
    HOURS = "hours"
    DAYS = "days"
    WEEKS = "weeks"
    MONTHS = "months"

# ==================== Ban Requests ====================

class BanPlayerRequest(BaseModel):
    """Solicitud para banear a un jugador"""
    player_identifier: str = Field(..., description="UUID o nombre del jugador")
    reason: str = Field(..., description="Razón del ban")
    duration_type: str = Field(
        default="permanent",
        description="Tipo de duración: permanent, hours, days, weeks, months"
    )
    duration_value: int = Field(
        default=0,
        description="Valor numérico de la duración (ignorado si es permanent)"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "player_identifier": "Steve",
                "reason": "Hacking",
                "duration_type": "permanent",
                "duration_value": 0
            }
        }

class KickPlayerRequest(BaseModel):
    """Solicitud para expulsar a un jugador"""
    player_identifier: str = Field(..., description="UUID o nombre del jugador")
    reason: str = Field(
        default="You have been kicked from the server",
        description="Razón de la expulsión"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "player_identifier": "Steve",
                "reason": "Spam warning"
            }
        }

class UnbanPlayerRequest(BaseModel):
    """Solicitud para desbanear a un jugador"""
    player_identifier: str = Field(..., description="UUID o nombre del jugador")

    class Config:
        json_schema_extra = {
            "example": {
                "player_identifier": "Steve"
            }
        }

class BanIPRequest(BaseModel):
    """Solicitud para banear una IP"""
    ip_address: str = Field(..., description="Dirección IP a banear")
    reason: str = Field(..., description="Razón del ban de IP")
    duration_type: str = Field(
        default="permanent",
        description="Tipo de duración: permanent, hours, days, weeks, months"
    )
    duration_value: int = Field(
        default=0,
        description="Valor numérico de la duración"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "ip_address": "192.168.1.100",
                "reason": "Multiple compromised accounts",
                "duration_type": "permanent",
                "duration_value": 0
            }
        }

class UnbanIPRequest(BaseModel):
    """Solicitud para desbanear una IP"""
    ip_address: str = Field(..., description="Dirección IP a desbanear")

    class Config:
        json_schema_extra = {
            "example": {
                "ip_address": "192.168.1.100"
            }
        }

# ==================== Ban Responses ====================

class BanDetailResponse(BaseModel):
    """Detalles de un ban"""
    id: int
    reason: str
    issued_by: str
    issued_at: datetime
    is_active: bool
    expires_at: Optional[datetime] = None
    is_permanent: bool

class PlayerBanInfo(BaseModel):
    """Información de ban de un jugador"""
    uuid: str
    name: str
    ban: dict  # Detalles del ban

class PlayerInfo(BaseModel):
    """Información básica de un jugador"""
    uuid: str
    name: str
    is_online: bool
    last_played: Optional[datetime] = None
    total_playtime: str
    ip: Optional[str] = None
    avatar_url: str
    is_banned: bool = False

class PlayerDetailResponse(BaseModel):
    """Respuesta con detalles completos de un jugador"""
    uuid: str
    name: str
    is_online: bool
    first_seen: datetime
    last_seen: Optional[datetime] = None
    playtime: str
    playtime_seconds: int
    last_ip: Optional[str] = None

class PlayerListResponse(BaseModel):
    """Respuesta con lista de jugadores"""
    server: str
    online_count: int
    total_unique: int
    players: List[PlayerInfo]

class OnlinePlayersResponse(BaseModel):
    """Respuesta con jugadores en línea"""
    server: str
    online_count: int
    players: list

class ActiveBansResponse(BaseModel):
    """Respuesta con bans activos del servidor"""
    server: str
    active_bans_count: int
    bans: list

class BanStatusResponse(BaseModel):
    """Respuesta con estado de ban"""
    banned: bool
    player: Optional[dict] = None
    ban: Optional[dict] = None

# ==================== Operation Responses ====================

class OperationSuccessResponse(BaseModel):
    """Respuesta genérica de operación exitosa"""
    success: bool
    message: str
    data: Optional[dict] = None

class BanOperationResponse(BaseModel):
    """Respuesta de operación de ban"""
    success: bool
    message: str
    player: Optional[PlayerBanInfo] = None

class KickOperationResponse(BaseModel):
    """Respuesta de operación de kick"""
    success: bool
    message: str
    player: Optional[dict] = None

class IPOperationResponse(BaseModel):
    """Respuesta de operación con IP"""
    success: bool
    message: str
    ip: Optional[dict] = None

# ==================== Error Responses ====================

class ErrorResponse(BaseModel):
    """Respuesta de error"""
    status: str = "error"
    message: str
    error: Optional[str] = None
    details: Optional[dict] = None

class ValidationErrorResponse(BaseModel):
    """Respuesta de error de validación"""
    status: str = "error"
    message: str
    errors: List[dict]
