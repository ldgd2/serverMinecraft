from ..base import AchievementDefinition, AchievementCategory

ARCHITECTURE_ACHIEVEMENTS = [
    AchievementDefinition("ARCH_1", "Pintamos toda la casa...", "Coloca 1,000 bloques.", AchievementCategory.ARCHITECTURE, {"block_placed": 1000}, rarity=0.66),
    AchievementDefinition("ARCH_2", "Y la de agarrar la pala?", "Coloca 10,000 bloques.", AchievementCategory.ARCHITECTURE, {"block_placed": 10000}, rarity=0.89),
    AchievementDefinition("ARCH_3", "Todo es risas hasta", "Coloca 50,000 bloques.", AchievementCategory.ARCHITECTURE, {"block_placed": 50000}, rarity=0.81),
    AchievementDefinition("ARCH_4", "Arquitecto del apocalipsis", "Coloca 100,000 bloques.", AchievementCategory.ARCHITECTURE, {"block_placed": 100000}, rarity=0.91),
    AchievementDefinition("ARCH_5", "Catedral de sangre", "Coloca 500,000 bloques.", AchievementCategory.ARCHITECTURE, {"block_placed": 500000}, rarity=0.94),
    AchievementDefinition("ARCH_GOD", "Dios de la materia", "Coloca 1,000,000 de bloques.", AchievementCategory.ARCHITECTURE, {"block_placed": 1000000}, rarity=1.00),
    AchievementDefinition("ARCH_MEGA", "Constructor de Civilizaciones", "Supera los 250,000 bloques colocados en el mundo.", AchievementCategory.ARCHITECTURE, {"block_placed": 250000}, rarity=0.97),
    AchievementDefinition("ARCH_IMPERIAL", "Arquitecto de Imperios", "Has posicionado 1,000,000 de bloques de construccion.", AchievementCategory.ARCHITECTURE, {"block_placed": 1000000}, rarity=1.00),
    AchievementDefinition("WAR_ARCHITECT", "Arquitecto de Guerra", "Coloca 100,000 bloques y elimina a 10,000 enemigos.", AchievementCategory.ARCHITECTURE, {"block_placed": 100000, "kill": 10000}, rarity=0.93),
]
