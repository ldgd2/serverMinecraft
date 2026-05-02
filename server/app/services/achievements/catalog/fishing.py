from ..base import AchievementDefinition, AchievementCategory

FISHING_ACHIEVEMENTS = [
    AchievementDefinition("FISH_1", "Anzuelo mortal", "Pesca 10 peces.", AchievementCategory.FISHING, {"fish_caught": 10}),
    AchievementDefinition("FISH_2", "Extincion marina", "Pesca 100 peces.", AchievementCategory.FISHING, {"fish_caught": 100}),
    AchievementDefinition("FISH_3", "Reliquia del abismo", "Pesca un objeto de valor (tesoro).", AchievementCategory.FISHING, {"treasure_caught": 1}),
    AchievementDefinition("FISH_ELITE", "Depredador de los mares", "Pesca 1,000 peces.", AchievementCategory.FISHING, {"fish_caught": 1000}),
]
