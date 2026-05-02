from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Request
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
    server_name: str = "MinecraftTest"

class MinecraftChat(BaseModel):
    player_uuid: str
    player_name: str
    message: str
    type: str # 'chat', 'join', 'leave', 'achievement'
    server_name: str = "MinecraftTest"

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
        if not body:
             logger.warning("📥 Received empty body in /event")
             return {"status": "ignored", "reason": "empty body"}
             
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
    logger.info(f"💬 Received Minecraft Chat/System Event from {chat.server_name}: {chat.player_name}: {chat.message} ({chat.type})")
    
    # 1. Intentar encontrar el servidor por nombre
    server = db.query(Server).filter(Server.name == chat.server_name).first()
    
    # Fallback si no existe ese nombre, usar el primero (para compatibilidad)
    if not server:
        server = db.query(Server).first()
        
    if not server:
        return {"status": "error", "message": "No server found"}

    # 2. Registrar jugador si es un evento de join
    if chat.type == "join":
        # Buscar si ya existe por UUID
        player = db.query(Player).filter(
            Player.uuid == chat.player_uuid,
            Player.server_id == server.id
        ).first()
        
        # Fallback por nombre si no tiene UUID (jugadores no-premium o mod desactualizado)
        if not player:
            player = db.query(Player).filter(
                Player.name.ilike(chat.player_name),
                Player.server_id == server.id
            ).first()

        if not player:
            logger.info(f"🆕 Creating new player record for {chat.player_name}")
            player = Player(
                server_id=server.id,
                uuid=chat.player_uuid,
                name=chat.player_name
            )
            db.add(player)
            db.flush() # Para tener el ID disponible
            
            # Inicializar detalles
            if not player.detail:
                player.detail = PlayerDetail(player_id=player.id)
                db.add(player.detail)
        else:
            # Actualizar datos si ya existe
            player.name = chat.player_name
            if chat.player_uuid and chat.player_uuid != "unknown":
                player.uuid = chat.player_uuid
        
        db.commit()

    # 3. Guardar en historial (Chat, Join, Leave, Achievement)
    chat_mapping = {
        "chat": "received",
        "join": "join",
        "leave": "leave",
        "achievement": "achievement"
    }
    
    db_type = chat_mapping.get(chat.type, "received")
    
    new_chat = ServerChat(
        server_id=server.id,
        username=chat.player_name if chat.type == "chat" else "System",
        message=chat.message if chat.type == "chat" else f"{chat.player_name} " + 
               ("ha entrado al servidor" if chat.type == "join" else 
                "ha salido del servidor" if chat.type == "leave" else chat.message),
        type=db_type
    )
    db.add(new_chat)
    db.commit()

    # 4. Retransmitir a la App en tiempo real
    # El broadcaster usa el nombre del servidor como canal
    is_system = chat.type in ['join', 'leave', 'achievement']
    await broadcaster.broadcast_chat(
        server.name, 
        chat.player_name if not is_system else "System", 
        chat.message,
        is_system=is_system,
        chat_type=chat.type if is_system else "received"
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
    message: str,
    server_name: str = None,
    db: Session = Depends(get_db)
):
    """
    Envía un mensaje desde la App hacia el chat del juego usando RCON.
    """
    try:
        from app.services.minecraft.rcon import rcon_service
        
        # 1. Encontrar el servidor
        if server_name:
            server = db.query(Server).filter(Server.name == server_name).first()
        else:
            server = db.query(Server).first()
            
        if not server:
            raise HTTPException(status_code=404, detail="Server not found")

        # 2. Guardar en historial como mensaje 'sent'
        new_chat = ServerChat(
            server_id=server.id,
            username=user_name,
            message=message,
            type="sent"
        )
        db.add(new_chat)
        db.commit()

        # 3. Notificar a otros clientes de la App (broadcaster)
        await broadcaster.broadcast_chat(
            server.name, 
            user_name, 
            message,
            is_system=False,
            chat_type="sent"
        )

        # 4. Enviar al juego vía RCON
        # Formateamos el mensaje para que destaque en el juego
        rcon_msg = f'tellraw @a ["", {{"text":"[APP] ","color":"dark_gray"}}, {{"text":"{user_name}: ","color":"dark_aqua"}}, {{"text":"{message}","color":"gray"}}]'
        success = rcon_service.send_command(rcon_msg, server_name=server.name)
        
        if not success:
            # Si falló el envío al juego, pero se guardó en la DB, al menos la App lo ve.
            # Pero informamos del error.
            return {"status": "partial_success", "message": "Saved to history but failed to send to game (Server offline?)"}

        return {"status": "sent"}
    except Exception as e:
        logger.error(f"Error sending message to game: {e}")
        raise HTTPException(status_code=500, detail=str(e))
