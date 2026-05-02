from fastapi import APIRouter, Header, HTTPException, Depends, status, WebSocket, WebSocketDisconnect, Request
from pydantic import BaseModel
from typing import Optional, List
import logging
import hashlib
import asyncio
from sqlalchemy.orm import Session
from database.connection import get_db
from database.models.user import User
from core.broadcaster import broadcaster
import datetime
from app.services.player_service import PlayerService
from app.services.achievements import AchievementService
from database.models import Server
from database.models.players.player import Player
from database.models.players.player_detail import PlayerDetail
from database.connection import SessionLocal

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
async def receive_event(event: dict, request: Request, user: User = Depends(verify_api_key)):
    print(f"DEBUG: Received Bridge Event: {event}")
    player = event.get("player", "Unknown")
    event_type = event.get("type", "unknown")
    logger.info(f"[MineBridge] Evento de {user.username}: {player} -> {event_type}")
    
    # PROCESAR LOGROS Y ESTADO DEL JUGADOR
    with SessionLocal() as db:
        # 1. Obtener el servidor
        server_name = event.get("server_name")
        if server_name:
            server = db.query(Server).filter(Server.name == server_name).first()
        else:
            server = db.query(Server).filter(Server.user_id == user.id).first()
            if not server:
                server = db.query(Server).first()

        if server:
            # 2. Notificar a la App (Chat de sistema) usando el nombre del servidor
            # Solo si NO es join o leave, ya que esos los maneja app/routes/minecraft.py con más detalle
            if event_type not in ["join", "leave"]:
                msg = f"{player} {event_type.replace('_', ' ')}"
                if event_type == "death" and event.get("cause"):
                    msg = f"{player} murió por {event.get('cause')}"
                    
                await broadcaster.broadcast_chat(server.name, "System", msg, is_system=True)
            
            # 3. Procesar logros
            # ... rest of logic
                if player_obj:
                    if event_type == "join":
                        # 1. Incrementar contador de inicios de sesión
                        AchievementService.process_stat_update(db, player_obj, "login_count", 1)
                        
                        # 2. Actualizar fecha de último ingreso
                        if not player_obj.detail:
                            from database.models.players.player_detail import PlayerDetail
                            player_obj.detail = PlayerDetail(player_id=player_obj.id)
                        
                        player_obj.detail.last_joined_at = datetime.datetime.utcnow()
                        db.commit()

                        # --- RE-APPLY SKIN ON JOIN ---
                        try:
                            import os
                            skin_path = f"static/skins/{player}.png"
                            if os.path.exists(skin_path):
                                from app.controllers.server_controller import ServerController
                                sc = ServerController()
                                
                                # Obtener host dinámicamente de la request o env
                                app_url = os.environ.get("APP_URL")
                                if not app_url:
                                    host = request.headers.get("host", "localhost:8000")
                                    protocol = "https" if request.url.scheme == "https" else "http"
                                    app_url = f"{protocol}://{host}"
                                
                                skin_url = f"{app_url}/static/skins/{player}.png"
                                
                                # Re-aplicar comando en la consola
                                import asyncio
                                # Enviar varias versiones del comando para asegurar compatibilidad con diferentes mods
                                asyncio.create_task(sc.send_command(server.name, f"skin set {player} {skin_url}"))
                                asyncio.create_task(sc.send_command(server.name, f"skin url {skin_url}")) # Para SkinRestorer
                                print(f"[MineBridge] Re-aplicando skin para {player} via {skin_url}")
                        except Exception as e:
                            print(f"[MineBridge] Error al re-aplicar skin: {e}")
                
                elif event_type == "leave":
                    # 1. Calcular duración de la sesión si tenemos el join
                    if player_obj.detail and player_obj.detail.last_joined_at:
                        now = datetime.datetime.utcnow()
                        duration = int((now - player_obj.detail.last_joined_at).total_seconds())
                        
                        if duration > 0:
                            # Actualizar tiempo total
                            player_obj.detail.total_playtime_seconds += duration
                            # Registrar para logros (esto se acumula en PlayerStat)
                            AchievementService.process_stat_update(db, player_obj, "session_time_seconds", duration)
                            db.commit()

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
async def receive_chat(chat: dict, db: Session = Depends(get_db), user: User = Depends(verify_api_key)):
    print(f"DEBUG: Received Bridge Chat: {chat}")
    player_name = chat.get("player", "Unknown")
    message = chat.get("message", "")
    logger.info(f"[MineBridge] Chat sync for {user.username}: <{player_name}> {message}")
    
    # 1. Obtener el servidor primero para saber a qué canal de la App transmitir
    server_name = chat.get("server_name")
    server = None
    if server_name:
        server = db.query(Server).filter(Server.name == server_name).first()
    
    if not server:
        # Fallback al primero del usuario o primero global
        server = db.query(Server).filter(Server.user_id == user.id).first()
        if not server:
            server = db.query(Server).first()

    if server:
        # 2. Retransmitir a la App en tiempo real usando el canal del servidor
        # Desactivado aquí para evitar duplicados, ya que app/routes/minecraft.py lo maneja con historial
        # await broadcaster.broadcast_chat(server.name, player_name, message)

        # 3. --- PROCESAR LOGROS DE CHAT ---
        player = PlayerService.get_player_by_name(db, server, player_name)
        if player:
            AchievementService.process_stat_update(db, player, "chat_message", 1)

    return {"status": "ok"}

@router.post("/status")
async def receive_status(status: dict, user: User = Depends(verify_api_key)):
    state = status.get("state", "UNKNOWN")
    logger.info(f"[MineBridge] Server {user.username} Status: {state}")
    return {"status": "ok"}

@router.post("/status/player")
async def receive_player_state(request: Request, state: dict, db: Session = Depends(get_db)):
    # print(f"DEBUG: Received Bridge Player State: {state}")
    player_name = state.get("player")
    if not player_name:
        return {"error": "no player"}

    # 1. Obtener el servidor usando el server_id o server_name del payload
    server = None
    server_id = state.get("server_id")
    server_name = state.get("server_name")
    
    if server_id:
        server = db.query(Server).filter(Server.id == server_id).first()
    elif server_name:
        server = db.query(Server).filter(Server.name == server_name).first()
        
    if not server:
        # Fallback al primer servidor existente si no se especifica
        server = db.query(Server).first()
        if not server:
            server = db.query(Server).first()

    if not server:
        return {"error": "server not found"}

    # 2. Obtener el jugador
    player = PlayerService.get_player_by_name(db, server, player_name)
    if not player:
        # Intentar crear si no existe
        player = Player(server_id=server.id, name=player_name, uuid=state.get("uuid", "unknown"))
        db.add(player)
        db.flush()

    if not player.detail:
        from database.models.players.player_detail import PlayerDetail
        player.detail = PlayerDetail(player_id=player.id)
        db.add(player.detail)

    # 3. Actualizar datos básicos
    try:
        player.detail.health = int(state.get("health", 20))
        player.detail.position_x = int(state.get("pos_x", 0))
        player.detail.position_y = int(state.get("pos_y", 0))
        player.detail.position_z = int(state.get("pos_z", 0))
        player.detail.last_ip = state.get("ip")
        
        # Safe update for columns that might be missing in older schemas
        if hasattr(player.detail, 'country'):
            player.detail.country = state.get("country")
        if hasattr(player.detail, 'os'):
            player.detail.os = state.get("os")
    except Exception as e:
        print(f"[MineBridge] Warning: Error updating basic player stats: {e}")

    # 4. Sincronizar Skin si viene en el payload
    skin_data = state.get("skin_base64")
    if skin_data:
        # Detectar si es un JSON (Mojang style) o un raw PNG Base64
        import base64 as b64
        is_mojang = False
        try:
            decoded_test = b64.b64decode(skin_data).decode('utf-8')
            if '"textures"' in decoded_test:
                is_mojang = True
        except: pass

        if is_mojang:
            player.detail.skin_base64 = skin_data
            player.detail.skin_last_update = datetime.datetime.utcnow()
            
            # Intentar actualizar SkinRestorer
            from core.skinrestorer_bridge import set_skin_in_skinrestorer
            import os
            SKINRESTORER_DB = {
                'host': os.environ.get('SKINRESTORER_HOST', 'localhost'),
                'user': os.environ.get('SKINRESTORER_USER', 'root'),
                'password': os.environ.get('SKINRESTORER_PASS', ''),
                'database': os.environ.get('SKINRESTORER_DB', 'SkinRestorer')
            }
            # Extraer signature si viene por separado
            signature = state.get("skin_signature", "")
            set_skin_in_skinrestorer(SKINRESTORER_DB, player_name, skin_data, signature)

            # Descargar cabeza para la App
            from core.skin_utils import extract_skin_url, download_and_crop_head
            skin_url = extract_skin_url(skin_data)
            if skin_url:
                head_path = f"static/heads/{player_name}.png"
                try: download_and_crop_head(skin_url, head_path)
                except: pass
        else:
            # Es un raw PNG Base64 del Launcher
            # Lo guardamos como archivo estático para que el server pueda servirlo como URL a SkinRestorer
            try:
                import os
                os.makedirs("static/skins", exist_ok=True)
                skin_file_path = f"static/skins/{player_name}.png"
                with open(skin_file_path, "wb") as f:
                    f.write(b64.b64decode(skin_data))
                
                # Para la App, generamos la cabeza desde el PNG local
                try:
                    from PIL import Image
                    from io import BytesIO
                    skin_img = Image.open(BytesIO(b64.b64decode(skin_data))).convert('RGBA')
                    face = skin_img.crop((8, 8, 16, 16)).resize((64, 64), Image.NEAREST)
                    helmet = skin_img.crop((40, 8, 48, 16)).resize((64, 64), Image.NEAREST)
                    final_head = Image.alpha_composite(face, helmet)
                    os.makedirs("static/heads", exist_ok=True)
                    final_head.save(f"static/heads/{player_name}.png")
                except ImportError:
                    print("⚠️ Pillow (PIL) no está instalado. No se generará la cabeza para la App. (Usa 'pip install Pillow' en el servidor)")
                except Exception as e:
                    print(f"Error generando cabeza de skin: {e}")
                
                # --- ACTUALIZACIÓN PARA LA APP (Prioridad) ---
                import time
                ts = int(time.time())
                public_head_url = f"http://185.214.134.23:8000/static/heads/{player_name}.png?t={ts}"
                print(f"[MineBridge] Actualizando DB para App: {player_name} -> {public_head_url}")
                player.detail.skin_url = public_head_url
                player.detail.skin_base64 = skin_data
                player.detail.skin_last_update = datetime.datetime.utcnow()
                db.commit()
                # --- INYECCIÓN EN SKINRESTORER (Híbrido Robusto) ---
                skin_signature = state.get("skin_signature")
                injection_success = False
                
                if skin_signature:
                    try:
                        try:
                            from core.skinrestorer_bridge import set_skin_in_skinrestorer
                        except ImportError:
                            from server.core.skinrestorer_bridge import set_skin_in_skinrestorer
                        injection_success = set_skin_in_skinrestorer(db, player_name, skin_data, skin_signature)
                        if injection_success:
                            print(f"[MineBridge] Skin de {player_name} inyectada exitosamente (Premium ORM).")
                    except Exception as db_ex:
                        print(f"[MineBridge] Error en inyección ORM: {db_ex}")
                else:
                    print(f"[MineBridge] No-Premium: sin firma. MineSkin se encargará.")

                # --- INYECCIÓN GLOBAL: MineSkin para No-Premium ---
                async def signature_and_inject_task():
                    if injection_success:
                        return  # Premium ya inyectado, nada que hacer
                    
                    import aiohttp
                    import datetime as _dt
                    p_url = f"http://185.214.134.23:8000/static/skins/{player_name}.png"
                    
                    try:
                        print(f"[MineBridge] No-Premium: solicitando firma a MineSkin para {player_name}...")
                        async with aiohttp.ClientSession() as session:
                            async with session.post(
                                "https://api.mineskin.org/generate/url",
                                json={"url": p_url, "name": player_name}
                            ) as resp:
                                if resp.status == 200:
                                    data = await resp.json()
                                    texture_data = data.get("data", {}).get("texture", {})
                                    value = texture_data.get("value")
                                    signature = texture_data.get("signature")
                                    
                                    if value and signature:
                                        print(f"[MineBridge] Firma OK. Inyectando en DB para {player_name}...")
                                        # Inyección INLINE: sin imports externos que puedan fallar
                                        try:
                                            from database.models.skinrestorer import SkinRestorerSkin, SkinRestorerPlayer
                                        except ImportError:
                                            from server.database.models.skinrestorer import SkinRestorerSkin, SkinRestorerPlayer
                                        
                                        skin_name = f"custom_{player_name}"
                                        # Upsert Skin
                                        skin_rec = db.query(SkinRestorerSkin).filter(SkinRestorerSkin.Name == skin_name).first()
                                        if not skin_rec:
                                            skin_rec = SkinRestorerSkin(Name=skin_name)
                                            db.add(skin_rec)
                                        skin_rec.Value = value
                                        skin_rec.Signature = signature
                                        skin_rec.Timestamp = "none"
                                        # Upsert Player mapping
                                        p_map = db.query(SkinRestorerPlayer).filter(SkinRestorerPlayer.Nick == player_name).first()
                                        if not p_map:
                                            p_map = SkinRestorerPlayer(Nick=player_name)
                                            db.add(p_map)
                                        p_map.Skin = skin_name
                                        db.commit()
                                        print(f"[MineBridge] ✅ Skin de {player_name} inyectada en DB (No-Premium).")
                                    else:
                                        print("[MineBridge] MineSkin no devolvió datos válidos.")
                                else:
                                    print(f"[MineBridge] MineSkin API status: {resp.status}.")
                    except Exception as e:
                        print(f"[MineBridge] Error inyección No-Premium: {e}")

                asyncio.create_task(signature_and_inject_task())

            except Exception as e:
                print(f"Error procesando raw skin: {e}")

    db.commit()
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
