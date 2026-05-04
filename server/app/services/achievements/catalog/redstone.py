from ..base import AchievementDefinition, AchievementCategory

REDSTONE_ACHIEVEMENTS = [
    AchievementDefinition("TECH_1", "localhost:8000", "Coloca 500 componentes de Redstone.", AchievementCategory.REDSTONE, {"block_placed": 500}, rarity=0.39),
    AchievementDefinition("TECH_2", "Cerralo y volvelo a abrir", "Coloca 2,500 componentes de Redstone.", AchievementCategory.REDSTONE, {"block_placed": 2500}, rarity=0.68),
    AchievementDefinition(
        "ELITE_TECHNICIAN", 
        "Ingeniero de Sistemas", 
        "Envía 10,000 mensajes, coloca 50,000 bloques y juega 250 horas.", 
        AchievementCategory.REDSTONE, 
        {"chat_message": 10000, "block_placed": 50000, "playtime_seconds": 900000}
    ),
]
