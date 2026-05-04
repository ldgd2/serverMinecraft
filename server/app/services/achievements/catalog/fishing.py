from ..base import AchievementDefinition, AchievementCategory

FISHING_ACHIEVEMENTS = [
    AchievementDefinition("FISH_1", "Anzuelo mortal", "Pesca 10 peces.", AchievementCategory.FISHING, {"fish_caught": 10}, rarity=0.14),
    AchievementDefinition("FISH_2", "Extincion marina", "Pesca 100 peces.", AchievementCategory.FISHING, {"fish_caught": 100}, rarity=0.36),
    AchievementDefinition("FISH_3", "Reliquia del abismo", "Pesca un objeto de valor (tesoro).", AchievementCategory.FISHING, {"treasure_caught": 1}, rarity=0.07),
    AchievementDefinition("FISH_ELITE", "Depredador de los mares", "Pesca 1,000 peces.", AchievementCategory.FISHING, {"fish_caught": 1000}, rarity=0.63),
]
