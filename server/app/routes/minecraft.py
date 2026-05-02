from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from ..database.config import get_db
from ..services.achievements.processor import AchievementProcessor
from pydantic import BaseModel

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
    event: MinecraftEvent, 
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Endpoint para recibir eventos de logros (bloques, muertes, etc.)
    """
    try:
        background_tasks.add_task(
            AchievementProcessor.process_event,
            db,
            event.player_uuid,
            event.event_key,
            event.increment
        )
        return {"status": "received"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/chat")
async def handle_minecraft_chat(event: dict, db: Session = Depends(get_db)):
    # ... (lógica de chat existente)
    return {"status": "ok"}

@router.post("/player_state")
async def handle_player_state(state: dict, db: Session = Depends(get_db)):
    """
    Recibe el estado del jugador (pos, salud, etc.) y calcula distancia/tiempo.
    """
    player_uuid = state.get("player_name") # Por ahora usamos nombre como ID
    if not player_uuid: return {"error": "no uuid"}

    # 1. Obtener stats actuales
    stats = db.query(PlayerStats).filter(PlayerStats.player_uuid == player_uuid).first()
    if not stats:
        stats = PlayerStats(player_uuid=player_uuid, counters={})
        db.add(stats)
        db.flush()

    # 2. CALCULAR DISTANCIA (Pitágoras entre pos anterior y actual)
    last_x = stats.counters.get("_last_x", state["x"])
    last_y = stats.counters.get("_last_y", state["y"])
    last_z = stats.counters.get("_last_z", state["z"])
    
    dist = ((state["x"]-last_x)**2 + (state["y"]-last_y)**2 + (state["z"]-last_z)**2)**0.5
    
    if dist > 0.1 and dist < 100: # Evitar teleports o micro-movimientos
        AchievementProcessor.process_event(db, player_uuid, "distance_travelled", int(dist))

    # 3. CALCULAR TIEMPO (Cada update son ~5 segundos)
    AchievementProcessor.process_event(db, player_uuid, "playtime_seconds", 5)

    # 4. Actualizar última posición conocida
    stats.counters["_last_x"] = state["x"]
    stats.counters["_last_y"] = state["y"]
    stats.counters["_last_z"] = state["z"]
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
        # Formateamos el mensaje para que destaque en el juego
        # [APP] Nombre: Mensaje
        rcon_msg = f'tellraw @a ["", {{"text":"[APP] ","color":"dark_gray"}}, {{"text":"{user_name}: ","color":"dark_aqua"}}, {{"text":"{message}","color":"gray"}}]'
        
        from ..services.minecraft.rcon import rcon_service
        rcon_service.send_command(rcon_msg)
        
        return {"status": "sent"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
