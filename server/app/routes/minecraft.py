from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Request
from sqlalchemy.orm import Session
from database.connection import get_db
from app.services.achievements.processor import AchievementProcessor
from database.models.players.player import Player
from database.models.players.player_detail import PlayerDetail
from database.models.server import Server
from database.models.server_chat import ServerChat
from database.models.players.player_achievement import PlayerAchievement
from core.broadcaster import broadcaster
from pydantic import BaseModel
import logging
import datetime
from app.services.minecraft.player_manager import PlayerManager

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/minecraft", tags=["minecraft-integration"])

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

@router.post("/batch")
async def receive_batch(
    request: Request,
    batch: dict,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    chats = batch.get("chats", [])
    for chat_data in chats:
        try:
            chat = MinecraftChat(**chat_data)
            await handle_minecraft_chat(chat, db)
        except Exception as e:
            logger.error(f"❌ Error processing batched minecraft chat: {e}")

    return {"status": "ok", "processed": {"chats": len(chats)}}

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

    # 2. Identificar al jugador si es un evento relevante
    player = None
    if chat.type in ["chat", "join", "leave", "achievement"]:
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
        
        # --- PROCESAR LOGROS ESPECÍFICOS DE INICIO DE SESIÓN ---
        if chat.type == "join":
            # Actualizar caché central
            PlayerManager._global_online_players.setdefault(server.name, {})[chat.player_name] = {
                "uuid": chat.player_uuid,
                "joined_at": datetime.datetime.utcnow().isoformat()
            }
            
            # 1. Incrementar contador de inicios de sesión
            AchievementProcessor.process_stat_update(db, player, "login_count", 1, server_name=server.name)
            
            # 2. Logros por horario (Night Owl / Early Bird)
            now = datetime.datetime.utcnow()
            if 3 <= now.hour < 5:
                AchievementProcessor.unlock_achievement(db, player, "PLAY_AT_NIGHT", server_name=server.name)
            elif 5 <= now.hour < 7:
                AchievementProcessor.unlock_achievement(db, player, "PLAY_AT_DAWN", server_name=server.name)

            # 3. Logro por cumpleaños
            if player.detail and player.detail.birthday:
                # El formato es 'MM-DD'
                today_md = now.strftime("%m-%d")
                if player.detail.birthday == today_md:
                    AchievementProcessor.unlock_achievement(db, player, "BIRTHDAY_LOGIN", server_name=server.name)

            # 3. Actualizar fecha de último ingreso para cálculos de sesión
            if player.detail:
                player.detail.last_joined_at = now
            
            db.commit()

        elif chat.type == "leave":
            # Actualizar caché central
            if server.name in PlayerManager._global_online_players:
                PlayerManager._global_online_players[server.name].pop(chat.player_name, None)
            
            # El resumen de sesión se enviará por el endpoint /stats/session

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

    # 3.1. Retransmitir a la App en tiempo real
    await broadcaster.broadcast_chat(
        server.name, 
        new_chat.username, 
        new_chat.message,
        is_system=(chat.type != "chat"),
        chat_type=db_type
    )

    # --- PROCESAR LOGROS DE CHAT ---
    if chat.type == "chat" and player:
        AchievementProcessor.process_stat_update(db, player, "chat_message", 1, server_name=server.name)

    # 4. Registrar logro si aplica
    if chat.type == "achievement" and player:
        # Usamos el nuevo método profesional que busca metadata y notifica a App/Launcher
        AchievementProcessor.unlock_achievement(db, player, chat.message, server_name=server.name)
    
    db.commit()

    return {"status": "ok"}

@router.get("/stats/{player_uuid}")
async def get_player_stats(player_uuid: str, db: Session = Depends(get_db)):
    """
    Devuelve las estadísticas persistentes para que el Mod cargue sus contadores.
    """
    from database.models.players.player_stat import PlayerStat
    player = db.query(Player).filter(Player.uuid == player_uuid).first()
    if not player:
        return {}
    
    stats = db.query(PlayerStat).filter(PlayerStat.player_id == player.id).all()
    return {s.stat_key: s.stat_value for s in stats}

@router.post("/stats/session")
async def receive_session_summary(summary: dict, db: Session = Depends(get_db)):
    """
    Recibe el acumulado de la sesión al desconectarse el jugador.
    """
    player_uuid = summary.get("player_uuid")
    stats_to_update = summary.get("stats", {}) # Ej: {"block_broken": 150, "kill:zombie": 5}
    
    player = db.query(Player).filter(Player.uuid == player_uuid).first()
    if not player:
        return {"status": "error", "message": "player not found"}

    for key, value in stats_to_update.items():
        AchievementProcessor.process_stat_update(db, player, key, value)
    
    db.commit()
    return {"status": "ok", "updated": len(stats_to_update)}

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
        # Formateamos el mensaje: $nombredeusuarioAdmin: mensaje
        # Usamos colores para que destaque
        rcon_msg = f'tellraw @a ["", {{"text":"{user_name}","color":"yellow"}}, {{"text":"Admin","color":"gold","bold":true}}, {{"text":": ","color":"gray"}}, {{"text":"{message}","color":"white"}}]'
        success = rcon_service.send_command(rcon_msg, server_name=server.name)
        
        if not success:
            # Si falló el envío al juego, pero se guardó en la DB, al menos la App lo ve.
            # Pero informamos del error.
            return {"status": "partial_success", "message": "Saved to history but failed to send to game (Server offline?)"}

        return {"status": "sent"}
    except Exception as e:
        logger.error(f"Error sending message to game: {e}")
        raise HTTPException(status_code=500, detail=str(e))
