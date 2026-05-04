from ..base import AchievementDefinition, AchievementCategory

EXPLORATION_ACHIEVEMENTS = [
    # --- TIEMPO DE JUEGO (VETERANÍA) ---
    AchievementDefinition("TIME_1", "Estado vegetal", "Juega durante 10 horas.", AchievementCategory.VETERAN, {"playtime_seconds": 36000}, rarity=0.81),
    AchievementDefinition("TIME_2", "Vida desperdiciada", "Juega durante 50 horas.", AchievementCategory.VETERAN, {"playtime_seconds": 180000}, rarity=0.98),
    AchievementDefinition("TIME_3", "Obsesion compulsiva", "Juega durante 100 horas.", AchievementCategory.VETERAN, {"playtime_seconds": 360000}, rarity=0.92),
    AchievementDefinition("TIME_4", "Hoy se cena aire", "Juega durante 500 horas.", AchievementCategory.VETERAN, {"playtime_seconds": 1800000}, rarity=1.00),
    AchievementDefinition("TIME_ULTIMATE", "Olvidado por Dios", "Juega durante 1,000 horas.", AchievementCategory.VETERAN, {"playtime_seconds": 3600000}, rarity=1.00),

    # --- DISTANCIA RECORRIDA ---
    AchievementDefinition("DIST_1", "Caminante sin sombra", "Recorre 10,000 bloques.", AchievementCategory.VETERAN, {"distance_travelled": 10000}, rarity=0.83),
    AchievementDefinition("DIST_2", "Nomada del vacio", "Recorre 100,000 bloques.", AchievementCategory.VETERAN, {"distance_travelled": 100000}, rarity=0.90),
]
