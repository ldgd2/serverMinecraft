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
    def process_event(db: Session, player_uuid: str, event_key: str, increment: int = 1):
        """
        Procesa un evento (ej: 'block_broken', 'kill:zombie') para un jugador.
        """
        # 1. Obtener el jugador por su UUID
        player = db.query(Player).filter(Player.uuid == player_uuid).first()
        if not player:
            logger.warning(f"Player with UUID {player_uuid} not found. Event {event_key} ignored.")
            return

        # 2. Obtener o crear el stat específico
        stat = db.query(PlayerStat).filter(
            PlayerStat.player_id == player.id, 
            PlayerStat.stat_key == event_key
        ).first()

        if not stat:
            stat = PlayerStat(player_id=player.id, stat_key=event_key, stat_value=0)
            db.add(stat)
            db.flush()

        # 3. Actualizar el valor
        stat.stat_value += increment
        new_val = stat.stat_value
        db.commit()

        # 4. Verificar qué logros se desbloquean con este nuevo valor
        AchievementProcessor._check_unlocks(db, player, event_key, new_val)

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

                    # Notificar al servidor vía RCON (opcional pero genial)
                    msg = f'tellraw @a ["", {{"text":"🏆 ","color":"gold"}}, {{"text":"{player.name}","color":"white"}}, {{"text":" ha conseguido el logro ","color":"gray"}}, {{"text":"[{ach.name}]","color":"yellow","hoverEvent":{{"action":"show_text","contents":"{ach.description}"}}}}]'
                    try:
                        rcon_service.send_command(msg)
                    except:
                        pass
