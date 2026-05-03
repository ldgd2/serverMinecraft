import logging
import asyncio

# Guardamos el event loop principal al importar para usarlo desde background threads
_main_loop: asyncio.AbstractEventLoop = None

def set_main_loop(loop: asyncio.AbstractEventLoop):
    global _main_loop
    _main_loop = loop
from sqlalchemy.orm import Session
from .registry import ACHIEVEMENTS_REGISTRY, get_achievement_by_id
from database.models.players.player import Player
from database.models.players.player_stat import PlayerStat
from database.models.players.player_achievement import PlayerAchievement
from app.services.minecraft.rcon import rcon_service

logger = logging.getLogger(__name__)

class AchievementProcessor:
    """
    Cerebro encargado de recibir eventos del Mod de Minecraft y 
    procesar el progreso de los logros.
    """

    @staticmethod
    def process_stat_update(db: Session, player: Player, stat_key: str, increment: int = 1, value: str = None, server_name: str = None):
        """
        Registra estadísticas básicas (como login_count) y verifica logros de servidor.
        Ya no sincronizamos estadísticas globales de combate/minería aquí para ahorrar recursos.
        """
        # 1. Obtener o crear el stat
        stat = db.query(PlayerStat).filter(
            PlayerStat.player_id == player.id, 
            PlayerStat.stat_key == stat_key
        ).first()
        
        if not stat:
            stat = PlayerStat(player_id=player.id, stat_key=stat_key, stat_value=0)
            db.add(stat)
            db.flush()
            
        stat.stat_value += increment
        db.commit()
        
        # 2. Logros automáticos del servidor (Ej: X veces conectado)
        if stat_key == "login_count":
            if stat.stat_value == 100:
                AchievementProcessor.unlock_achievement(db, player, "LOGIN_100", server_name=server_name)
            elif stat.stat_value == 500:
                AchievementProcessor.unlock_achievement(db, player, "LOGIN_500", server_name=server_name)
        
        pass

    @staticmethod
    def unlock_achievement(db: Session, player: Player, achievement_id: str, server_name: str = None):
        """
        Desbloquea un logro directamente (usado cuando el Mod detecta el logro).
        Se encarga de la persistencia y la notificación a la App/Launcher.
        """
        # 1. Buscar metadata en el registro
        from .registry import get_achievement_by_id
        ach = get_achievement_by_id(achievement_id)
        
        name = achievement_id
        description = "Logro obtenido en el juego"
        
        if ach:
            name = ach.name
            description = ach.description

        # 2. Verificar si ya existe
        exists = db.query(PlayerAchievement).filter(
            PlayerAchievement.player_id == player.id,
            PlayerAchievement.achievement_id == achievement_id
        ).first()

        if not exists:
            logger.info(f"🏆 Logro registrado (Mod-Driven): {player.name} -> {name}")
            
            new_ach = PlayerAchievement(
                player_id=player.id,
                achievement_id=achievement_id,
                name=name,
                description=description
            )
            db.add(new_ach)
            db.commit()

            # 3. Notificar vía WebSocket al administrador/launcher/app
            try:
                from routes.bridge import manager
                from database.models.server import Server
                from database.models.user import User
                from core.broadcaster import broadcaster
                
                # Buscar servidor para el broadcast
                server = None
                if server_name:
                    server = db.query(Server).filter(Server.name == server_name).first()
                if not server:
                    server = db.query(Server).filter(Server.id == player.server_id).first()
                
                if server:
                    # Notificar a la App (WebSocket Broadcaster)
                    # El broadcaster enviará esto a los canales de la app móvil
                    asyncio.create_task(broadcaster.broadcast_chat(
                        server.name, 
                        "System", 
                        f"🏆 {player.name} ha obtenido: {name}",
                        is_system=True,
                        chat_type="achievement"
                    ))

                    # Notificar al Launcher (WebSocket Bridge manager)
                    admin = db.query(User).filter(User.id == server.user_id).first()
                    if admin:
                        loop = _main_loop
                        if loop and loop.is_running():
                            asyncio.run_coroutine_threadsafe(
                                manager.send_achievement(admin.username, player.name, name, description),
                                loop
                            )
            except Exception as e:
                logger.error(f"Error notificando desbloqueo de logro: {e}")
            
            return True
        return False

    @staticmethod
    def process_event(db: Session, player_uuid: str, event_key: str, increment: int = 1, server_name: str = None):
        """
        ENDPOINT DESACTIVADO para eventos de juego (bloques, muertes).
        El Mod gestiona esta lógica internamente.
        """
        pass

    @staticmethod
    def _check_unlocks(db: Session, player: Player, event_key: str, current_value: int, server_name: str = None):
        """
        [DEPRECATED/LEGACY] 
        Mantenemos el código por si en el futuro se quiere procesar algún logro 
        especial desde el backend (ej: por tiempo de juego), pero ya no se 
        ejecuta en cada evento de bloque/muerte.
        """
        # Filtrar logros que dependen de este event_key
        potential_achievements = [
            ach for ach in ACHIEVEMENTS_REGISTRY 
            if event_key in ach.requirements
        ]

        if not potential_achievements:
            return

        for ach in potential_achievements:
            # 1. Verificar si ya lo tiene desbloqueado
            exists = db.query(PlayerAchievement).filter(
                PlayerAchievement.player_id == player.id,
                PlayerAchievement.achievement_id == ach.id
            ).first()

            if exists:
                continue

            # 2. Verificar TODAS las condiciones del logro
            all_met = True
            for req_key, req_value in ach.requirements.items():
                if req_key == event_key:
                    val = current_value
                else:
                    # Consultar DB para otros requisitos
                    other_stat = db.query(PlayerStat).filter(
                        PlayerStat.player_id == player.id,
                        PlayerStat.stat_key == req_key
                    ).first()
                    val = other_stat.stat_value if other_stat else 0
                
                if val < req_value:
                    all_met = False
                    break
            
            if all_met:
                # Usar el nuevo método unificado para desbloquear
                AchievementProcessor.unlock_achievement(db, player, ach.id, server_name=server_name)
