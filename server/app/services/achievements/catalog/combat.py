from ..base import AchievementDefinition, AchievementCategory

COMBAT_ACHIEVEMENTS = [
    AchievementDefinition("KILL_1", "Fue bait", "Elimina a 10 enemigos.", AchievementCategory.COMBAT, {"kill": 10}),
    AchievementDefinition("KILL_2", "y ese goresito", "Elimina a 50 enemigos.", AchievementCategory.COMBAT, {"kill": 50}),
    AchievementDefinition("KILL_3", "No debiste nacer", "Elimina a 100 enemigos.", AchievementCategory.COMBAT, {"kill": 100}),
    AchievementDefinition("KILL_4", "Psicosis", "Elimina a 500 enemigos.", AchievementCategory.COMBAT, {"kill": 500}),
    AchievementDefinition("KILL_5", "Duermanlo como a los perritos", "Elimina a 1,000 enemigos.", AchievementCategory.COMBAT, {"kill": 1000}),
    AchievementDefinition("KILL_ELITE", "I have no mouth and I must scream", "Elimina a 5,000 enemigos.", AchievementCategory.COMBAT, {"kill": 5000}),
]
