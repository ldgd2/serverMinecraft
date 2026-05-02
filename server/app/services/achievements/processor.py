import logging
from sqlalchemy.orm import Session
from .registry import ACHIEVEMENTS_REGISTRY, get_achievement_by_id
from ...database.models.players.player_stats import PlayerStats
from ...database.models.players.player_achievement import PlayerAchievement
from ...services.minecraft.rcon import rcon_service

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
        # 1. Obtener o crear stats del jugador
        stats = db.query(PlayerStats).filter(PlayerStats.player_uuid == player_uuid).first()
        if not stats:
            stats = PlayerStats(player_uuid=player_uuid, counters={})
            db.add(stats)
            db.flush()

        # 2. Actualizar el contador específico
        current_val = stats.counters.get(event_key, 0)
        new_val = current_val + increment
        stats.counters[event_key] = new_val
        db.commit()

        # 3. Verificar qué logros se desbloquean con este nuevo valor
        AchievementProcessor._check_unlocks(db, player_uuid, event_key, new_val)

    @staticmethod
    def _check_unlocks(db: Session, player_uuid: str, event_key: str, current_value: int):
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
                    PlayerAchievement.player_uuid == player_uuid,
                    AchievementAchievement.achievement_id == ach.id
                ).first()

                if not exists:
                    AchievementProcessor._unlock_achievement(db, player_uuid, ach)

    @staticmethod
    def _unlock_achievement(db: Session, player_uuid: str, achievement):
        """
        Registra el logro como obtenido y lo anuncia al servidor.
        """
        try:
            new_unlock = PlayerAchievement(
                player_uuid=player_uuid,
                achievement_id=achievement.id
            )
            db.add(new_unlock)
            db.commit()

            # ANUNCIO EN EL CHAT DE MINECRAFT (Via RCON)
            # Usamos colores dorados y aqua para el estilo "edgy/premium"
            msg = f'tellraw @a ["", {{"text":"[LOGRO] ","color":"gold","bold":true}}, {{"text":"{player_uuid} ","color":"aqua"}}, {{"text":"ha alcanzado: ","color":"gray"}}, {{"text":"{achievement.title}","color":"yellow","italic":true}}]'
            rcon_service.send_command(msg)

            logger.info(f"Logro desbloqueado: {achievement.id} para {player_uuid}")
        except Exception as e:
            logger.error(f"Error al desbloquear logro {achievement.id}: {str(e)}")
            db.rollback()
