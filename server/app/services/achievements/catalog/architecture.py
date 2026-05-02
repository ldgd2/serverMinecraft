from ..base import AchievementDefinition, AchievementCategory

ARCHITECTURE_ACHIEVEMENTS = [
    AchievementDefinition("ARCH_1", "Pintamos toda la casa...", "Coloca 1,000 bloques.", AchievementCategory.ARCHITECTURE, {"block_placed": 1000}),
    AchievementDefinition("ARCH_2", "Y la de agarrar la pala?", "Coloca 10,000 bloques.", AchievementCategory.ARCHITECTURE, {"block_placed": 10000}),
    AchievementDefinition("ARCH_3", "Todo es risas hasta", "Coloca 50,000 bloques.", AchievementCategory.ARCHITECTURE, {"block_placed": 50000}),
    AchievementDefinition("ARCH_4", "Arquitecto del apocalipsis", "Coloca 100,000 bloques.", AchievementCategory.ARCHITECTURE, {"block_placed": 100000}),
    AchievementDefinition("ARCH_5", "Catedral de sangre", "Coloca 500,000 bloques.", AchievementCategory.ARCHITECTURE, {"block_placed": 500000}),
    AchievementDefinition("ARCH_GOD", "Dios de la materia", "Coloca 1,000,000 de bloques.", AchievementCategory.ARCHITECTURE, {"block_placed": 1000000}),
]
