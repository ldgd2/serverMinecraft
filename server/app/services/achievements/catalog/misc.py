from ..base import AchievementDefinition, AchievementCategory

MISC_ACHIEVEMENTS = [
    AchievementDefinition("MISC_TAMING", "Sindrome de Estocolmo", "Domestica a 10 animales.", AchievementCategory.SPECIAL, {"animal_tamed": 10}, rarity=0.10),
    AchievementDefinition("MISC_SHEARING", "Explotacion textil", "Trasquila a 100 ovejas.", AchievementCategory.SPECIAL, {"sheep_sheared": 100}, rarity=0.44),
    AchievementDefinition("MISC_EATING", "Hambre de poder", "Consume 1,000 unidades de comida.", AchievementCategory.SPECIAL, {"food_eaten": 1000}, rarity=0.70),
    AchievementDefinition("MISC_MUSIC", "DJ del apocalipsis", "Reproduce 10 discos de musica en el tocadiscos.", AchievementCategory.SPECIAL, {"music_disc_played": 10}, rarity=0.14),
    AchievementDefinition("MISC_SLEEP", "Insomnio cronico", "Duerme 100 veces en una cama.", AchievementCategory.SPECIAL, {"bed_slept": 100}, rarity=0.37),
]
