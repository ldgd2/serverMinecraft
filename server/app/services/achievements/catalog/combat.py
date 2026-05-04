from ..base import AchievementDefinition, AchievementCategory

COMBAT_ACHIEVEMENTS = [
    AchievementDefinition("KILL_1", "Fue bait", "Elimina a 10 enemigos.", AchievementCategory.COMBAT, {"kill": 10}, rarity=0.52),
    AchievementDefinition("KILL_2", "y ese goresito", "Elimina a 50 enemigos.", AchievementCategory.COMBAT, {"kill": 50}, rarity=0.47),
    AchievementDefinition("KILL_3", "No debiste nacer", "Elimina a 100 enemigos.", AchievementCategory.COMBAT, {"kill": 100}, rarity=0.51),
    AchievementDefinition("KILL_4", "Psicosis", "Elimina a 500 enemigos.", AchievementCategory.COMBAT, {"kill": 500}, rarity=0.55),
    AchievementDefinition("KILL_5", "Duermanlo como a los perritos", "Elimina a 1,000 enemigos.", AchievementCategory.COMBAT, {"kill": 1000}, rarity=0.63),
    AchievementDefinition("KILL_ELITE", "I have no mouth and I must scream", "Elimina a 5,000 enemigos.", AchievementCategory.COMBAT, {"kill": 5000}, rarity=0.66),
    AchievementDefinition("WARLORD", "Soberano del Campo de Batalla", "Alcanza las 10,000 bajas confirmadas.", AchievementCategory.COMBAT, {"kill": 10000}, rarity=0.89),
    AchievementDefinition("GENOCIDE", "Aniquilador Sistematico", "Has exterminado a 100,000 criaturas hostiles.", AchievementCategory.COMBAT, {"kill": 100000}, rarity=0.98),
]
