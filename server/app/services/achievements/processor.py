import logging
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
    def process_stat_update(db: Session, player: Player, stat_key: str, increment: int = 1, value: str = None):
        """
        Versión alternativa para el Bridge que recibe el objeto Player directamente.
        """
        # 1. Obtener o crear el stat específico
        stat = db.query(PlayerStat).filter(
            PlayerStat.player_id == player.id, 
            PlayerStat.stat_key == stat_key
        ).first()
        
        if not stat:
            stat = PlayerStat(player_id=player.id, stat_key=stat_key, stat_value=0)
            db.add(stat)
            db.flush()
            
        # 2. Actualizar valor
        stat.stat_value += increment
        db.commit()
        
        # 3. Actualizar PlayerAccount (Estadísticas globales/launcher)
        try:
            from database.models.players.player_account import PlayerAccount
            account = db.query(PlayerAccount).filter(
                (PlayerAccount.uuid == player.uuid) | (PlayerAccount.username == player.name)
            ).first()

            if account:
                HOSTILE_MOBS = {
                    "zombie", "skeleton", "creeper", "spider", "enderman", "witch", "slime", "silverfish",
                    "ghast", "blaze", "magma_cube", "endermite", "guardian", "shulker", "husk", "stray",
                    "wither_skeleton", "vex", "evoker", "vindicator", "pillager", "ravager", "hoglin",
                    "zoglin", "piglin_brute", "warden", "drowned", "phantom", "wither", "ender_dragon", 
                    "elder_guardian", "ravager"
                }

                if stat_key.startswith("kill:"):
                    entity = stat_key.split(":")[-1].lower()
                    if entity == "player":
                        account.total_player_kills += increment
                    elif entity in HOSTILE_MOBS:
                        account.total_hostile_kills += increment
                    
                    # Genocida: todo lo que muera suma (jugadores, hostiles y pasivos)
                    account.total_genocide_score += increment
                    account.total_kills += increment
                
                elif stat_key == "total_death":
                    account.total_deaths += increment
                elif stat_key == "total_block_broken":
                    account.total_blocks_broken += increment
                elif stat_key == "total_block_placed":
                    account.total_blocks_placed += increment

                db.commit()
        except Exception as e:
            logger.error(f"Error updating global PlayerAccount stats: {e}")

        # 4. Verificar logros
        AchievementProcessor._check_unlocks(db, player, stat_key, stat.stat_value)

    @staticmethod
    def process_event(db: Session, player_uuid: str, event_key: str, increment: int = 1):
        """
        Procesa un evento (ej: 'block_broken', 'kill:zombie') para un jugador.
        """
        # 1. Obtener el jugador por su UUID
        player = db.query(Player).filter(Player.uuid == player_uuid).first()
        if not player:
            logger.warning(f"Player with UUID {player_uuid} not found. Event {event_key} ignored.")
            return

        # Reutilizar lógica
        AchievementProcessor.process_stat_update(db, player, event_key, increment)

    @staticmethod
    def _check_unlocks(db: Session, player: Player, event_key: str, current_value: int):
        """
        Busca en el registro maestro qué logros dependen de este evento y 
        si se cumplen las condiciones.
        """
        # Filtrar logros que dependen de este event_key
        potential_achievements = [
            ach for ach in ACHIEVEMENTS_REGISTRY 
            if event_key in ach.requirements
        ]

        for ach in potential_achievements:
            target = ach.requirements[event_key]
            
            # Si el jugador alcanzó el objetivo
            if current_value >= target:
                # Verificar si ya lo tiene desbloqueado
                exists = db.query(PlayerAchievement).filter(
                    PlayerAchievement.player_id == player.id,
                    PlayerAchievement.achievement_id == ach.id
                ).first()

                if not exists:
                    # ¡LOGRO DESBLOQUEADO!
                    logger.info(f"🏆 Logro desbloqueado: {player.name} -> {ach.name}")
                    
                    new_ach = PlayerAchievement(
                        player_id=player.id,
                        achievement_id=ach.id,
                        name=ach.name,
                        description=ach.description
                    )
                    db.add(new_ach)
                    db.commit()

                    # Notificar al servidor vía WebSocket para que el Mod haga saltar el logro
                    try:
                        from server.routes.bridge import manager
                        from database.models.server import Server
                        from database.models.user import User
                        import asyncio
                        
                        # Buscar el username del dueño del servidor
                        server = db.query(Server).filter(Server.id == player.server_id).first()
                        if server:
                            admin = db.query(User).filter(User.id == server.user_id).first()
                            if admin:
                                # Necesitamos programarlo en el event loop principal
                                try:
                                    loop = asyncio.get_running_loop()
                                    loop.create_task(manager.send_achievement(admin.username, player.name, ach.name, ach.description))
                                except RuntimeError:
                                    # Si no hay loop corriendo (ej. hilo síncrono), usamos un hilo nuevo
                                    asyncio.run(manager.send_achievement(admin.username, player.name, ach.name, ach.description))
                    except Exception as e:
                        logger.error(f"Error enviando logro por WS: {e}")
