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
from jose import jwt, JWTError
from app.services.auth_service import SECRET_KEY, ALGORITHM
from database.models.players.player_account import PlayerAccount

router = APIRouter(prefix="/bridge", tags=["Minecraft Bridge"])
logger = logging.getLogger("uvicorn")

# --- Modelos de Datos ---

class BridgeEvent(BaseModel):
    player: str
    type: str # join, leave, achievement, etc.
    uuid: Optional[str] = None
    achievement_id: Optional[str] = None
    increment: Optional[int] = 1
    server_name: Optional[str] = None
    class Config:
        extra = "allow"

# --- Caché de Jugadores ---

server_player_cache = PlayerManager._global_online_players

def cache_player_join(server_name: str, username: str, uuid: str = "unknown", ip: str = "unknown"):
    if server_name not in server_player_cache:
        server_player_cache[server_name] = {}
    server_player_cache[server_name][username] = {
        "uuid": uuid,
        "ip": ip,
        "joined_at": datetime.datetime.utcnow().isoformat()
    }

def cache_player_leave(server_name: str, username: str):
    if server_name in server_player_cache:
        server_player_cache[server_name].pop(username, None)

# --- Dependencias ---

async def verify_bridge_auth(
    x_api_key: Optional[str] = Header(None),
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db)
):
    """
    Verifica la autenticación del 'puente'. 
    Acepta:
    1. X-API-KEY (Admin/Servidor Mod)
    2. Authorization: Bearer <token> (Launcher/Jugador)
    """
    # 1. Intentar con API Key (Hash SHA256)
    if x_api_key:
        hashed_received = hashlib.sha256(x_api_key.encode()).hexdigest()
        user = db.query(User).filter(User.api_key_hashed == hashed_received).first()
        if user:
            return user

    # 2. Intentar con JWT de Jugador
    if authorization and authorization.startswith("Bearer "):
        token = authorization.split(" ")[1]
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            player_id: int = payload.get("player_id")
            if player_id:
                account = db.query(PlayerAccount).filter(PlayerAccount.id == player_id).first()
                if account:
                    # Si es un jugador válido, permitimos la acción.
                    # Retornamos el dueño de su primer servidor como 'User' para no romper
                    # la lógica que espera un objeto User administrador.
                    player_link = db.query(Player).filter(Player.uuid == account.uuid).first()
                    if player_link:
                        server = db.query(Server).filter(Server.id == player_link.server_id).first()
                        if server:
                            admin = db.query(User).filter(User.id == server.user_id).first()
                            if admin: return admin
                    
                    # Fallback al primer admin si no se encuentra relación directa
                    return db.query(User).first()
        except JWTError:
            pass

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Unauthorized: Invalid API Key or Player Token"
    )

# --- Handlers ---

@router.post("/events")
async def receive_event(event: dict, request: Request, user: User = Depends(verify_bridge_auth)):
    player_name = event.get("player", "Unknown")
    player_uuid = event.get("uuid") or event.get("player_uuid")
    event_type = event.get("type", "unknown")
    server_name = event.get("server_name")
    
    with SessionLocal() as db:
        server = db.query(Server).filter(Server.name == server_name).first()
        if not server:
            server = db.query(Server).filter(Server.user_id == user.id).first()
            if not server: server = db.query(Server).first()

        if server:
            # 1. Resolve player (Prefer UUID)
            player_obj = None
            if player_uuid:
                player_obj = PlayerService.get_player_by_uuid(db, server, player_uuid)
            
            if not player_obj and player_name != "Server":
                player_obj = PlayerService.get_player_by_name(db, server, player_name)
            
            if not player_obj:
                return {"status": "ignored", "reason": "player_not_found"}

            # 2. Handle Logic
            if event_type == "achievement":
                achievement_id = event.get("achievement_id") or event.get("message")
                increment = event.get("increment", 1)
                
                if achievement_id:
                    # Is it a counter stat?
                    stat_keys = ["total_kills", "session_kills", "hostile_kills", "totem_used", "block_broken", "item_enchanted", "chat_message"]
                    if achievement_id in stat_keys:
                        AchievementService.process_stat_update(db, player_obj, achievement_id, increment, server_name=server.name)
                    else:
                        # It's a direct achievement unlock
                        AchievementService.unlock_achievement(db, player_obj, achievement_id, server_name=server.name)
            
            elif event_type == "join":
                player_ip = event.get("ip") or "unknown"
                cache_player_join(server.name, player_name, player_uuid or "unknown", ip=player_ip)
            elif event_type == "leave":
                cache_player_leave(server.name, player_name)
            elif event_type == "player_state":
                # Información extendida desde el Launcher
                player_ip = event.get("ip")
                player_country = event.get("country")
                skin_b64 = event.get("skin_base64")
                os_info = event.get("os")
                
                if not player_obj.detail:
                    player_obj.detail = PlayerDetail(player_id=player_obj.id)
                    db.add(player_obj.detail)
                
                if player_ip: player_obj.detail.last_ip = player_ip
                if player_country: player_obj.detail.country = player_country
                if os_info: player_obj.detail.os = os_info
                
                if skin_b64:
                    # Solo procesar si la skin es nueva o ha cambiado
                    old_skin = player_obj.detail.skin_base64
                    if skin_b64 != old_skin:
                        logger.info(f"[Bridge] Nueva skin detectada para {player_name}. Sincronizando...")
                        
                        player_obj.detail.skin_base64 = skin_b64
                        player_obj.detail.skin_last_update = datetime.datetime.utcnow()
                        
                        # 1. Identificar si es PNG crudo o Textura firmada
                        # El PNG crudo empieza con 'iVBOR' (base64 de \x89PNG)
                        is_raw_png = skin_b64.startswith("iVBOR")
                        
                        final_value = skin_b64
                        final_signature = ""
                        
                        if is_raw_png:
                            # Necesitamos firmarla para que Minecraft la acepte
                            from core.skin_utils import upload_to_mineskin
                            signed_data = upload_to_mineskin(skin_b64)
                            if signed_data:
                                final_value = signed_data['value']
                                final_signature = signed_data['signature']
                            else:
                                logger.warning(f"[Bridge] No se pudo firmar la skin de {player_name} via MineSkin")

                        # 2. Guardar los valores firmados
                        player_obj.detail.skin_value = final_value
                        player_obj.detail.skin_signature = final_signature
                        
                        # 3. Sincronizar con SkinRestorer
                        from core.skinrestorer_bridge import set_skin_in_skinrestorer
                        set_skin_in_skinrestorer(db, player_obj.name, final_value, final_signature)
                        
                        # 4. Notificar al Mod por WebSocket para refresco en tiempo real
                        asyncio.create_task(manager.send_sync_skin(user.username, player_obj.name))
                    else:
                        # Si es la misma, solo actualizamos el timestamp de "visto"
                        player_obj.detail.skin_last_update = datetime.datetime.utcnow()
                
                db.commit()
    return {"status": "ok"}


@router.post("/status/player")
async def receive_player_status(event: dict, request: Request, user: User = Depends(verify_bridge_auth)):
    """
    Endpoint usado por el Launcher para reportar que el jugador está activo,
    su IP actual y su Skin.
    """
    # Reutilizamos la lógica de receive_event
    return await receive_event(event, request, user)


@router.post("/chat")
async def receive_chat(chat: dict, db: Session = Depends(get_db), user: User = Depends(verify_bridge_auth)):
    player_name = chat.get("player", "Unknown")
    player_uuid = chat.get("uuid") or chat.get("player_uuid")
    message = chat.get("message", "")
    server_name = chat.get("server_name")
    chat_type = chat.get("type", "chat")
    
    server = db.query(Server).filter(Server.name == server_name).first()
    if not server:
        server = db.query(Server).filter(Server.user_id == user.id).first()
        if not server: server = db.query(Server).first()

    if server:
        player_obj = None
        if player_uuid:
            player_obj = PlayerService.get_player_by_uuid(db, server, player_uuid)
        if not player_obj and player_name != "Server":
            player_obj = PlayerService.get_player_by_name(db, server, player_name)
            
        if player_obj:
            # Stats for chat
            if chat_type == "chat":
                AchievementService.process_stat_update(db, player_obj, "chat_message", 1, server_name=server.name)
            
            # Broadcast to App
            asyncio.create_task(broadcaster.broadcast_chat(
                server.name,
                player_obj.name,
                message,
                is_system=(chat_type != "chat"),
                chat_type=chat_type
            ))
            
    return {"status": "ok"}

@router.post("/batch")
async def receive_batch(batch: dict, request: Request, db: Session = Depends(get_db), user: User = Depends(verify_bridge_auth)):
    events = batch.get("events", [])
    chats = batch.get("chats", [])
    server_name = batch.get("server_name") or batch.get("server")

    # Inyectar server_name si falta en los hijos
    if server_name:
        for e in events: e.setdefault("server_name", server_name)
        for c in chats: c.setdefault("server_name", server_name)

    # 1. Procesar Eventos (Logros, Joins)
    for event in events:
        await receive_event(event, request, user)

    # 2. Procesar Chat
    for chat in chats:
        await receive_chat(chat, db, user)

    return {
        "status": "ok", 
        "processed": {
            "events": len(events),
            "chats": len(chats)
        }
    }

@router.get("/players/{server_name}")
async def get_cached_players(server_name: str, user: User = Depends(verify_bridge_auth)):
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
            for ws in disconnected:
                self.disconnect(username, ws)

    async def send_sync_skin(self, username: str, player: str):
        if username in self.active_connections:
            disconnected = []
            for ws in self.active_connections[username]:
                try:
                    await ws.send_json({
                        "action": "sync-skin", 
                        "player": player
                    })
                except:
                    disconnected.append(ws)
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
