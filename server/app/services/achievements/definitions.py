from enum import Enum
from dataclasses import dataclass
from typing import Optional, List

class AchievementCategory(Enum):
    MINING = "Mineria Extrema"
    COMBAT = "Operaciones de Combate"
    SOCIAL = "Red Social"
    EXPLORATION = "Exploracion Mundial"
    ARCHITECTURE = "Ingenieria y Arquitectura"
    REDSTONE = "Automatizacion"
    HARDCORE = "Supervivencia Extrema"
    VETERAN = "Legado del Servidor"

@dataclass
class AchievementDefinition:
    id: str
    name: str
    description: str
    category: AchievementCategory
    # Requisitos: dict de {stat_key: threshold}
    requirements: dict
    hidden: bool = False

# CATÁLOGO MAESTRO DE LOGROS (SIN EMOJIS - NIVEL PROFESIONAL)
ACHIEVEMENTS_CATALOG: List[AchievementDefinition] = [
    # --- MINERÍA ---
    AchievementDefinition("MINER_ELITE", "Estratega de Excavacion", "Completa la extraccion de 100,000 unidades de materia.", AchievementCategory.MINING, {"block_broken": 100000}),
    AchievementDefinition("MINER_BRUTAL", "Devorador de Tierras", "Has alcanzado los 500,000 bloques minados.", AchievementCategory.MINING, {"block_broken": 500000}),
    
    # --- COMBATE ---
    AchievementDefinition("WARLORD", "Soberano del Campo de Batalla", "Alcanza las 10,000 bajas confirmadas.", AchievementCategory.COMBAT, {"kill": 10000}),
    AchievementDefinition("GENOCIDE", "Aniquilador Sistematico", "Has exterminado a 100,000 criaturas hostiles.", AchievementCategory.COMBAT, {"kill": 100000}),
    
    # --- ARQUITECTURA ---
    AchievementDefinition("ARCH_MEGA", "Constructor de Civilizaciones", "Supera los 250,000 bloques colocados en el mundo.", AchievementCategory.ARCHITECTURE, {"block_placed": 250000}),
    AchievementDefinition("ARCH_IMPERIAL", "Arquitecto de Imperios", "Has posicionado 1,000,000 de bloques de construccion.", AchievementCategory.ARCHITECTURE, {"block_placed": 1000000}),
    
    # --- VETERANÍA ---
    AchievementDefinition("TIME_LEGEND", "Leyenda Viviente", "Has dedicado 1,000 horas de tiempo real al servidor.", AchievementCategory.VETERAN, {"playtime_seconds": 3600000}),
    AchievementDefinition("TIME_ANCIENT", "Entidad Ancestral", "Supera las 2,500 horas de permanencia activa.", AchievementCategory.VETERAN, {"playtime_seconds": 9000000}),

    # --- LOGROS COMPLEJOS (BRUTALES) ---
    AchievementDefinition(
        "DOMINATOR", 
        "Dominador Absoluto", 
        "200,000 bloques colocados, 50,000 bajas y 500 horas de juego.", 
        AchievementCategory.VETERAN, 
        {"block_placed": 200000, "kill": 50000, "playtime_seconds": 1800000}
    ),
    AchievementDefinition(
        "WAR_ARCHITECT", 
        "Arquitecto de Guerra", 
        "Coloca 100,000 bloques y elimina a 10,000 enemigos.", 
        AchievementCategory.ARCHITECTURE, 
        {"block_placed": 100000, "kill": 10000}
    ),
    AchievementDefinition(
        "ELITE_TECHNICIAN", 
        "Ingeniero de Sistemas", 
        "Envía 10,000 mensajes, coloca 50,000 bloques y juega 250 horas.", 
        AchievementCategory.REDSTONE, 
        {"chat_message": 10000, "block_placed": 50000, "playtime_seconds": 900000}
    ),
]
