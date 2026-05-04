from enum import Enum
from dataclasses import dataclass
from typing import Optional, List, Tuple

class AchievementCategory(Enum):
    MINING = "Mineria Extrema"
    COMBAT = "Operaciones de Combate"
    SOCIAL = "Red Social"
    EXPLORATION = "Exploracion Mundial"
    ARCHITECTURE = "Ingenieria y Arquitectura"
    REDSTONE = "Automatizacion"
    HARDCORE = "Supervivencia Extrema"
    VETERAN = "Legado del Servidor"
    SPECIAL = "Especiales y Memes"
    DIMENSIONS = "Dimensiones"

class RarityTier(Enum):
    # Nombre, peso mínimo, peso máximo, color hexadecimal (para el Launcher/UI)
    COMMON = ("Común", 0.00, 0.30, "#AAAAAA")       # Gris
    UNCOMMON = ("Poco Común", 0.31, 0.60, "#55FF55")  # Verde
    RARE = ("Raro", 0.61, 0.85, "#5555FF")        # Azul
    EPIC = ("Épico", 0.86, 0.95, "#AA00AA")       # Morado
    LEGENDARY = ("Legendario", 0.96, 0.99, "#FFAA00") # Dorado / Naranja
    MYTHIC = ("Mítico", 1.00, 1.00, "#AA0000")      # Rojo Oscuro (Edgys/Imposibles)

    @classmethod
    def get_tier(cls, weight: float) -> 'RarityTier':
        for tier in cls:
            if tier.value[1] <= weight <= tier.value[2]:
                return tier
        return cls.COMMON

@dataclass
class AchievementDefinition:
    id: str
    name: str
    description: str
    category: AchievementCategory
    # Requisitos: dict de {stat_key: threshold}
    requirements: dict
    hidden: bool = False
    rarity: float = 0.00  # Rango de 0.00 a 1.00
    
    @property
    def rarity_tier(self) -> RarityTier:
        return RarityTier.get_tier(self.rarity)
    
    @property
    def color(self) -> str:
        return self.rarity_tier.value[3]
