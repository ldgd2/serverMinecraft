from enum import Enum
from dataclasses import dataclass
from typing import Dict

class AchievementCategory(Enum):
    MINING = "Mineria Extrema"
    COMBAT = "Operaciones de Combate"
    SOCIAL = "Red Social"
    EXPLORATION = "Exploracion Mundial"
    ARCHITECTURE = "Ingenieria y Arquitectura"
    REDSTONE = "Automatizacion"
    HARDCORE = "Supervivencia Extrema"
    VETERAN = "Legado del Servidor"
    SPECIAL = "Operaciones Especiales"
    FARMING = "Sector Primario"
    ECONOMY = "Mercado Libre"
    LOOT = "Tesoros y Despojos"
    FISHING = "Depredacion Marina"
    BREWING = "Quimica Ilegal"
    ENCHANTING = "Corrupcion Mistica"
    DEATH = "Fracaso Sistematico"

@dataclass
class AchievementDefinition:
    id: str
    name: str
    description: str
    category: AchievementCategory
    requirements: Dict[str, int]
    hidden: bool = False
