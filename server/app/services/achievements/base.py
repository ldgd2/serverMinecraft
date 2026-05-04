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
    # --- NUEVAS CATEGORÍAS TEMÁTICAS ---
    DIMENSIONS = "Viaje Interdimensional"
    STREAKS = "Rachas de Dominio"
    CURIOSITY = "Curiosidades"
    MEMES = "Cultura de Internet"
    EDGY = "Oscuridad y Nihilismo"
    PHILOSOPHY = "Reflexiones Existenciales"
    QUOTES = "Citas Celebres"
    ATTITUDE = "Actitud y Estilo"

@dataclass
class AchievementDefinition:
    id: str
    name: str
    description: str
    category: AchievementCategory
    requirements: Dict[str, int]
    hidden: bool = False
    rarity: float = 0.00  # 0.00 = super común, 1.00 = rareza absoluta

    @property
    def rarity_tier(self) -> str:
        if self.rarity >= 1.00: return "MYTHIC"
        if self.rarity >= 0.96: return "LEGENDARY"
        if self.rarity >= 0.86: return "EPIC"
        if self.rarity >= 0.61: return "RARE"
        if self.rarity >= 0.31: return "UNCOMMON"
        return "COMMON"

    @property
    def color(self) -> str:
        return {
            "MYTHIC":    "#AA0000",
            "LEGENDARY": "#FFAA00",
            "EPIC":      "#AA00AA",
            "RARE":      "#5555FF",
            "UNCOMMON":  "#55FF55",
        }.get(self.rarity_tier, "#AAAAAA")
