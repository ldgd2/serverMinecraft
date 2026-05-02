from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from database.connection import get_db
from app.services.achievements.processor import AchievementProcessor
from database.models.players.player import Player
from database.models.players.player_detail import PlayerDetail
from database.models.server import Server
from database.models.server_chat import ServerChat
from core.broadcaster import broadcaster
from pydantic import BaseModel
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/minecraft", tags=["minecraft-integration"])

# --- MODELOS ---

class MinecraftEvent(BaseModel):
    player_uuid: str
    event_key: str
    increment: int = 1

class MinecraftChat(BaseModel):
    player_uuid: str
    player_name: str
    message: str
    type: str # 'chat', 'join', 'leave', 'achievement'

# --- ENDPOINTS ---

@router.post("/event")
async def receive_minecraft_event(
    request: Request,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Endpoint para recibir eventos de logros (bloques, muertes, etc.)
    """
    try:
        body = await request.json()
        logger.info(f"📥 Received Minecraft Event: {body}")
        
        event = MinecraftEvent(**body)
        
        background_tasks.add_task(
            AchievementProcessor.process_event,
            db,
            event.player_uuid,
            event.event_key,
            event.increment
        )
        return {"status": "received"}
    except Exception as e:
        logger.error(f"❌ Error processing minecraft event: {e}")
        # Intentar sacar el body crudo para debug si falló el parseo
        try:
            raw_body = await request.body()
            logger.error(f"Raw body that failed: {raw_body.decode()}")
        except: pass
        raise HTTPException(status_code=422, detail=str(e))

@router.post("/chat")
async def handle_minecraft_chat(chat: MinecraftChat, db: Session = Depends(get_db)):
    """
    Endpoint para sincronizar el chat y eventos de sistema (join/leave)
    """
    logger.info(f"💬 Received Minecraft Chat/System Event: {chat.player_name}: {chat.message} ({chat.type})")
    
    # 1. Intentar encontrar el servidor (Heurística: primer servidor si no sabemos cual es)
    # En producción idealmente el Mod enviaría su Server ID
    server = db.query(Server).first()
    if not server:
        return {"status": "error", "message": "No server found"}

    # 2. Guardar en historial si es chat
    if chat.type == "chat":
        new_chat = ServerChat(
            server_id=server.id,
            username=chat.player_name,
            message=chat.message,
            type="received"
        )
        db.add(new_chat)
        db.commit()

    # 3. Retransmitir a la App en tiempo real
    # El broadcaster usa el nombre del servidor como canal
    is_system = chat.type in ['join', 'leave', 'achievement']
    await broadcaster.broadcast_chat(
        server.name, 
        chat.player_name if not is_system else "System", 
        chat.message,
        is_system=is_system
    )

    return {"status": "ok"}

@router.post("/player_state")
async def handle_player_state(state: dict, db: Session = Depends(get_db)):
    """
    Recibe el estado del jugador (pos, salud, etc.) y calcula distancia/tiempo.
    El mod envía: pos_x, pos_y, pos_z, player (UUID), health, food, world.
    """
    player_uuid = state.get("player")
    if not player_uuid: return {"error": "no player"}

    # 1. Obtener jugador y su detalle
    player = db.query(Player).filter(Player.uuid == player_uuid).first()
    if not player:
        return {"error": "player not found"}
    
    if not player.detail:
        player.detail = PlayerDetail(player_id=player.id)
        db.add(player.detail)
        db.flush()

    # 2. CALCULAR DISTANCIA (Pitágoras entre pos anterior y actual)
    x = state.get("pos_x", 0)
    y = state.get("pos_y", 0)
    z = state.get("pos_z", 0)

    last_x = player.detail.position_x
    last_y = player.detail.position_y
    last_z = player.detail.position_z
    
    dist = ((x - last_x)**2 + (y - last_y)**2 + (z - last_z)**2)**0.5
    
    if 0.1 < dist < 100:  # Evitar teleports o micro-movimientos
        AchievementProcessor.process_event(db, player_uuid, "distance_travelled", int(dist))

    # 3. CALCULAR TIEMPO (Cada update son ~5 segundos)
    AchievementProcessor.process_event(db, player_uuid, "playtime_seconds", 5)

    # 4. Actualizar posición y salud en PlayerDetail
    player.detail.position_x = int(x)
    player.detail.position_y = int(y)
    player.detail.position_z = int(z)
    player.detail.health = int(state.get("health", 20))
    player.detail.total_playtime_seconds += 5
    
    db.commit()

    return {"status": "ok"}

@router.post("/send-to-game")
async def send_to_game(
    user_name: str,
    message: str
):
    """
    Envía un mensaje desde la App hacia el chat del juego usando RCON.
    """
    try:
        from app.services.minecraft.rcon import rcon_service
        # Formateamos el mensaje para que destaque en el juego
        rcon_msg = f'tellraw @a ["", {{"text":"[APP] ","color":"dark_gray"}}, {{"text":"{user_name}: ","color":"dark_aqua"}}, {{"text":"{message}","color":"gray"}}]'
        rcon_service.send_command(rcon_msg)
        return {"status": "sent"}
    except Exception as e:
        logger.error(f"Error sending message to game via RCON: {e}")
        raise HTTPException(status_code=500, detail=str(e))
