from fastapi import APIRouter, Header, HTTPException, Depends, status
from pydantic import BaseModel
from typing import Optional, List
import logging
import hashlib
from sqlalchemy.orm import Session
from database.connection import get_db
from database.models.user import User
from fastapi import WebSocket, WebSocketDisconnect

router = APIRouter(prefix="/api/v1/bridge", tags=["Minecraft Bridge"])
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

class BridgeStat(BaseModel):
    player: str
    stat: str
    value: str
    amount: int = 1

class BridgeChat(BaseModel):
    player: str
    message: str

class BridgeStatus(BaseModel):
    state: str # STARTED, STOPPING

class PlayerState(BaseModel):
    player: str
    health: float
    food: int
    pos_x: float
    pos_y: float
    pos_z: float
    world: str

# --- Endpoints ---

@router.get("/test")
async def test_connection(user: User = Depends(verify_api_key)):
    return {"status": "success", "message": f"Conexion exitosa. Vinculado a: {user.username}"}

@router.post("/events")
async def receive_event(event: BridgeEvent, user: User = Depends(verify_api_key)):
    logger.info(f"[MineBridge] Evento de {user.username}: {event.player} -> {event.type}")
    return {"status": "ok"}

@router.post("/stats")
async def receive_stat(stat: BridgeStat, user: User = Depends(verify_api_key)):
    # logger.info(f"[MineBridge] Stats ({user.username}): {stat.player} {stat.stat}")
    return {"status": "ok"}

@router.post("/chat")
async def receive_chat(chat: BridgeChat, user: User = Depends(verify_api_key)):
    logger.info(f"[MineBridge] Chat sync for {user.username}: <{chat.player}> {chat.message}")
    return {"status": "ok"}

@router.post("/status")
async def receive_status(status: BridgeStatus, user: User = Depends(verify_api_key)):
    logger.info(f"[MineBridge] Server {user.username} Status: {status.state}")
    return {"status": "ok"}

@router.post("/status/player")
async def receive_player_state(state: PlayerState, user: User = Depends(verify_api_key)):
    return {"status": "ok"}

# --- WebSocket Bridge (Comandos en Tiempo Real) ---

@router.websocket("/ws")
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
