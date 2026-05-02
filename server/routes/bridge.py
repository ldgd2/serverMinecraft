from fastapi import APIRouter, Header, HTTPException, Depends, status
from pydantic import BaseModel
from typing import Optional, List
import logging
import hashlib
from sqlalchemy.orm import Session
from database.connection import get_db
from database.models.user import User
from fastapi import WebSocket, WebSocketDisconnect, Request
from core.broadcaster import broadcaster

router = APIRouter(prefix="/bridge", tags=["Minecraft Bridge"])
ws_router = APIRouter(prefix="/ws", tags=["Minecraft Bridge WS"])
logger = logging.getLogger("uvicorn")

# --- Gestión de Conexiones Activas ---
class ConnectionManager:
    def __init__(self):
        self.active_connections: dict[str, WebSocket] = {} # username -> socket

    async def connect(self, username: str, websocket: WebSocket):
        await websocket.accept()
        self.active_connections[username] = websocket

    def disconnect(self, username: str):
        if username in self.active_connections:
            del self.active_connections[username]

    async def send_command(self, username: str, command: str):
        if username in self.active_connections:
            await self.active_connections[username].send_json({
                "action": "command",
                "command": command
            })

    async def send_kick(self, username: str, target: str, reason: str):
        if username in self.active_connections:
            await self.active_connections[username].send_json({
                "action": "kick",
                "player": target,
                "reason": reason
            })

    async def send_ban(self, username: str, target: str, reason: str):
        if username in self.active_connections:
            await self.active_connections[username].send_json({
                "action": "ban",
                "player": target,
                "reason": reason
            })

    async def send_unban(self, username: str, target: str):
        if username in self.active_connections:
            await self.active_connections[username].send_json({
                "action": "unban",
                "player": target
            })

manager = ConnectionManager()

async def verify_api_key(x_api_key: str = Header(...), db: Session = Depends(get_db)):
    # Sacar hash de la llave recibida
    hashed_received = hashlib.sha256(x_api_key.encode()).hexdigest()
    
    # Buscar usuario que tenga ese hash
    user = db.query(User).filter(User.api_key_hashed == hashed_received).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API Key"
        )
    return user

# --- Modelos de Datos ---

class BridgeEvent(BaseModel):
    player: str
    type: str # join, leave, death, etc.
    uuid: Optional[str] = None
    cause: Optional[str] = None
    killer: Optional[str] = None
    # Catch-all for extra fields
    class Config:
        extra = "allow"

class BridgeStat(BaseModel):
    player: str
    stat: str
    value: str
    amount: int = 1
    type: Optional[str] = "stat_update"
    class Config:
        extra = "allow"

class BridgeChat(BaseModel):
    player: str
    message: str
    type: Optional[str] = "chat"
    class Config:
        extra = "allow"

class BridgeStatus(BaseModel):
    state: str # STARTED, STOPPING
    class Config:
        extra = "allow"

class PlayerState(BaseModel):
    player: str
    health: float
    food: int
    pos_x: float
    pos_y: float
    pos_z: float
    world: str
    class Config:
        extra = "allow"

async def log_request(request: Request):
    body = await request.body()
    print(f"--- INCOMING BRIDGE REQUEST ---")
    print(f"URL: {request.url}")
    print(f"Headers: {dict(request.headers)}")
    print(f"Body: {body.decode(errors='replace')}")
    print(f"-------------------------------")

@router.get("/test")
async def test_connection(user: User = Depends(verify_api_key)):
    return {"status": "success", "message": f"Conexion exitosa. Vinculado a: {user.username}"}

@router.post("/events")
async def receive_event(event: dict, user: User = Depends(verify_api_key)):
    print(f"DEBUG: Received Bridge Event: {event}")
    player = event.get("player", "Unknown")
    event_type = event.get("type", "unknown")
    logger.info(f"[MineBridge] Evento de {user.username}: {player} -> {event_type}")
    
    # Notificar a la App (Chat de sistema)
    msg = f"{player} {event_type.replace('_', ' ')}"
    if event_type == "death" and event.get("cause"):
        msg = f"{player} murió por {event.get('cause')}"
        
    await broadcaster.broadcast_chat(user.username, "System", msg, is_system=True)

    # Procesar logros de inicio de sesion (Login Count)
    if event_type == "join":
        from app.services.player_service import PlayerService
        from app.services.achievements import AchievementService
        from database.models import Server
        from database.connection import SessionLocal
        
        # Usamos una sesion nueva para evitar conflictos con el request principal si fuera necesario
        with SessionLocal() as db:
            # Intentar encontrar por server_name si viniera en el payload (no viene en el mod actual pero lo preparamos)
            server_name = event.get("server_name")
            if server_name:
                server = db.query(Server).filter(Server.name == server_name).first()
            else:
                # Fallback al primer servidor del usuario o el primero global
                server = db.query(Server).filter(Server.user_id == user.id).first()
                if not server:
                    server = db.query(Server).first()

            if server:
                player_obj = PlayerService.get_player_by_name(db, server, player)
                if player_obj:
                    AchievementService.process_stat_update(db, player_obj, "login_count", 1)

    return {"status": "ok"}

@router.post("/stats")
async def receive_stat(stat: dict, db: Session = Depends(get_db), user: User = Depends(verify_api_key)):
    # print(f"DEBUG: Received Bridge Stat: {stat}")
    player_name = stat.get("player")
    stat_key = stat.get("stat")
    value = stat.get("value")
    amount = stat.get("amount", 1)
    
    if player_name and stat_key:
        from app.services.achievements import AchievementService
        from app.services.player_service import PlayerService
        
        # Obtener el primer servidor del usuario (o el que corresponda)
        # En una arquitectura multi-servidor real, el Mod debería enviar su ID o nombre de instancia
        # Por ahora, buscamos al jugador en los servidores de este administrador
        # Obtener el servidor (priorizar server_name si el mod lo envía)
        server_name = stat.get("server_name")
        if server_name:
            server = db.query(Server).filter(Server.name == server_name).first()
        else:
            # Fallback al primero del usuario o primero global
            server = db.query(Server).filter(Server.user_id == user.id).first()
            if not server:
                server = db.query(Server).first()

        if server:
            player = PlayerService.get_player_by_name(db, server, player_name)
            if player:
                AchievementService.process_stat_update(db, player, stat_key, amount, value=value)

    return {"status": "ok"}

@router.post("/chat")
async def receive_chat(chat: dict, user: User = Depends(verify_api_key)):
    print(f"DEBUG: Received Bridge Chat: {chat}")
    player = chat.get("player", "Unknown")
    message = chat.get("message", "")
    logger.info(f"[MineBridge] Chat sync for {user.username}: <{player}> {message}")
    
    # Retransmitir a la App en tiempo real
    await broadcaster.broadcast_chat(user.username, player, message)
    return {"status": "ok"}

@router.post("/status")
async def receive_status(status: dict, user: User = Depends(verify_api_key)):
    state = status.get("state", "UNKNOWN")
    logger.info(f"[MineBridge] Server {user.username} Status: {state}")
    return {"status": "ok"}

@router.post("/status/player")
async def receive_player_state(state: dict, user: User = Depends(verify_api_key)):
    return {"status": "ok"}

# --- WebSocket Bridge (Comandos en Tiempo Real) ---

@ws_router.websocket("/bridge")
async def websocket_bridge(websocket: WebSocket, db: Session = Depends(get_db)):
    # Extraer API Key del Header (en Java Mod se puede enviar)
    api_key = websocket.headers.get("x-api-key")
    
    if not api_key:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    hashed_received = hashlib.sha256(api_key.encode()).hexdigest()
    user = db.query(User).filter(User.api_key_hashed == hashed_received).first()

    if not user:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    await manager.connect(user.username, websocket)
    logger.info(f"[MineBridge] WebSocket conectado para administrador: {user.username}")
    
    try:
        while True:
            # Mantener conexión abierta y escuchar latidos si es necesario
            data = await websocket.receive_text()
            # Podríamos procesar respuestas del mod aquí
    except WebSocketDisconnect:
        manager.disconnect(user.username)
        logger.info(f"[MineBridge] WebSocket desconectado para: {user.username}")
