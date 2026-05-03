from .catalog.mining import MINING_ACHIEVEMENTS
from .catalog.combat import COMBAT_ACHIEVEMENTS
from .catalog.special import SPECIAL_ACHIEVEMENTS
from .catalog.social import SOCIAL_ACHIEVEMENTS
from .catalog.dimensions import DIMENSION_ACHIEVEMENTS
from .catalog.exploration import EXPLORATION_ACHIEVEMENTS
from .catalog.architecture import ARCHITECTURE_ACHIEVEMENTS
from .catalog.redstone import REDSTONE_ACHIEVEMENTS
from .catalog.farming import FARMING_ACHIEVEMENTS
from .catalog.economy import ECONOMY_ACHIEVEMENTS
from .catalog.loot import LOOT_ACHIEVEMENTS
from .catalog.fishing import FISHING_ACHIEVEMENTS
from .catalog.brewing import BREWING_ACHIEVEMENTS
from .catalog.enchanting import ENCHANTING_ACHIEVEMENTS
from .catalog.deaths import DEATH_ACHIEVEMENTS
from .catalog.misc import MISC_ACHIEVEMENTS

# Registro maestro unificado de logros modulares
# Solo mantenemos lo especial y social por petición del usuario para ahorrar recursos
ACHIEVEMENTS_REGISTRY = (
    SPECIAL_ACHIEVEMENTS +
    SOCIAL_ACHIEVEMENTS
)

def get_achievement_by_id(achievement_id: str):
    for ach in ACHIEVEMENTS_REGISTRY:
        if ach.id == achievement_id:
            return ach
    return None
