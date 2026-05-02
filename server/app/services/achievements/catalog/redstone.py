from ..base import AchievementDefinition, AchievementCategory

REDSTONE_ACHIEVEMENTS = [
    AchievementDefinition("TECH_1", "localhost:8000", "Coloca 500 componentes de Redstone.", AchievementCategory.REDSTONE, {"block_placed": 500}),
    AchievementDefinition("TECH_2", "Cerralo y volvelo a abrir", "Coloca 2,500 componentes de Redstone.", AchievementCategory.REDSTONE, {"block_placed": 2500}),
]
