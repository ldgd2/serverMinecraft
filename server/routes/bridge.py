from fastapi import APIRouter, Header, HTTPException, Depends, status, WebSocket, WebSocketDisconnect, Request
from pydantic import BaseModel
from typing import Optional, List
import logging
import hashlib
import asyncio
import aiohttp
import os
import sys
import json
import asyncio
import datetime
from sqlalchemy.orm import Session
from database.connection import get_db, SessionLocal
from database.models.user import User
from database.models import Server
from database.models.players.player import Player
from database.models.players.player_detail import PlayerDetail
from core.broadcaster import broadcaster
from app.services.player_service import PlayerService
from app.services.achievements import AchievementService
from app.services.minecraft.player_manager import PlayerManager

router = APIRouter(prefix="/bridge", tags=["Minecraft Bridge"])
logger = logging.getLogger("uvicorn")

# --- Modelos de Datos ---

class BridgeEvent(BaseModel):
    player: str
    type: str # join, leave, death, etc.
    uuid: Optional[str] = None
    cause: Optional[str] = None
    killer: Optional[str] = None
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

# --- Caché de Jugadores ---

server_player_cache = PlayerManager._global_online_players

def cache_player_join(server_name: str, username: str, uuid: str = "unknown"):
    if server_name not in server_player_cache:
        server_player_cache[server_name] = {}
    server_player_cache[server_name][username] = {
        "uuid": uuid,
        "joined_at": datetime.datetime.utcnow().isoformat()
    }

def cache_player_leave(server_name: str, username: str):
    if server_name in server_player_cache:
        server_player_cache[server_name].pop(username, None)

# --- Dependencias ---

async def verify_api_key(x_api_key: str = Header(...), db: Session = Depends(get_db)):
    hashed_received = hashlib.sha256(x_api_key.encode()).hexdigest()
    user = db.query(User).filter(User.api_key_hashed == hashed_received).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API Key"
        )
    return user

# --- Handlers Individuales (Definidos antes de Batch para seguridad) ---

@router.post("/events")
async def receive_event(event: dict, request: Request, user: User = Depends(verify_api_key)):
    player = event.get("player", "Unknown")
    event_type = event.get("type", "unknown")
    
    with SessionLocal() as db:
        server = db.query(Server).filter(Server.name == event.get("server_name")).first()
        if not server:
            server = db.query(Server).filter(Server.user_id == user.id).first()
            if not server: server = db.query(Server).first()

        if server and event_type in ["join", "leave", "achievement"]:
            player_obj = PlayerService.get_player_by_name(db, server, player)
            if player_obj:
                if event_type == "achievement":
                    achievement_id = event.get("achievement_id") or event.get("message")
                    if achievement_id:
                        AchievementService.unlock_achievement(db, player_obj, achievement_id, server_name=server.name)
                elif event_type == "join":
                    cache_player_join(server.name, player, event.get("uuid", "unknown"))
                elif event_type == "leave":
                    cache_player_leave(server.name, player)
    return {"status": "ok"}


@router.post("/chat")
async def receive_chat(chat: dict, db: Session = Depends(get_db), user: User = Depends(verify_api_key)):
    player_name = chat.get("player", "Unknown")
    message = chat.get("message", "")
    server_name = chat.get("server_name")
    
    server = db.query(Server).filter(Server.name == server_name).first()
    if not server:
        server = db.query(Server).filter(Server.user_id == user.id).first()
        if not server: server = db.query(Server).first()

    if server:
        player = PlayerService.get_player_by_name(db, server, player_name)
        if player:
            AchievementService.process_stat_update(db, player, "chat_message", 1, server_name=server.name)
    return {"status": "ok"}

# --- Lote (Batch) ---

@router.post("/batch")
async def receive_batch(batch: dict, request: Request, db: Session = Depends(get_db), user: User = Depends(verify_api_key)):
    events = batch.get("events", [])
    stats = batch.get("stats", [])
    chats = batch.get("chats", [])
    server_name = batch.get("server_name")

    # Procesar solo eventos de conexión y logros
    for event in events:
        await receive_event(event, request, user)

    # 3. Procesar Chat
    for chat in chats:
        await receive_chat(chat, db, user)

    return {
        "status": "ok", 
        "processed": {
            "events": len(events),
            "stats": len(stats),
            "chats": len(chats)
        }
    }

# --- Legacy & WebSocket ---


@router.get("/players/{server_name}")
async def get_cached_players(server_name: str, user: User = Depends(verify_api_key)):
    players = server_player_cache.get(server_name, {})
    return {
        "server": server_name,
        "online": len(players),
        "players": [{"username": name, **data} for name, data in players.items()]
    }

ws_router = APIRouter(prefix="/ws", tags=["Minecraft Bridge WS"])

class ConnectionManager:
    def __init__(self):
        self.active_connections: dict[str, List[WebSocket]] = {}

    async def connect(self, username: str, websocket: WebSocket):
        await websocket.accept()
        if username not in self.active_connections:
            self.active_connections[username] = []
        self.active_connections[username].append(websocket)

    def disconnect(self, username: str, websocket: WebSocket):
        if username in self.active_connections:
            if websocket in self.active_connections[username]:
                self.active_connections[username].remove(websocket)
            if not self.active_connections[username]:
                del self.active_connections[username]

    async def send_achievement(self, username: str, player: str, title: str, desc: str):
        if username in self.active_connections:
            disconnected = []
            for ws in self.active_connections[username]:
                try:
                    await ws.send_json({
                        "action": "achievement", 
                        "player": player, 
                        "title": title, 
                        "desc": desc
                    })
                except:
                    disconnected.append(ws)
            
            # Limpiar desconectados
            for ws in disconnected:
                self.disconnect(username, ws)

manager = ConnectionManager()

@ws_router.websocket("/bridge")
async def websocket_bridge(websocket: WebSocket, db: Session = Depends(get_db)):
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
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(user.username, websocket)
        logger.info(f"[MineBridge] WebSocket desconectado para: {user.username}")
