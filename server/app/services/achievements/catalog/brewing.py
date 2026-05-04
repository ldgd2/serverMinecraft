from ..base import AchievementDefinition, AchievementCategory

BREWING_ACHIEVEMENTS = [
    AchievementDefinition("BREW_1", "Primer experimento", "Crea tu primera pocion.", AchievementCategory.BREWING, {"potion_brewed": 1}, rarity=0.12),
    AchievementDefinition("BREW_2", "Narcotraficante", "Crea 50 pociones.", AchievementCategory.BREWING, {"potion_brewed": 50}, rarity=0.15),
    AchievementDefinition("BREW_3", "Heisenberg", "Crea 250 pociones de alta calidad.", AchievementCategory.BREWING, {"potion_brewed": 250}, rarity=0.37),
    AchievementDefinition("BREW_ELITE", "Imperio de cristal", "Crea 1,000 pociones totales.", AchievementCategory.BREWING, {"potion_brewed": 1000}, rarity=0.66),
]
