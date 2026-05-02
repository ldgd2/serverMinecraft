from ..base import AchievementDefinition, AchievementCategory

DIMENSION_ACHIEVEMENTS = [
    # --- NETHER ---
    AchievementDefinition("NETHER_ENTER", "Abandona toda esperanza", "Entra al Nether por primera vez.", AchievementCategory.SPECIAL, {"dimension_enter:minecraft:the_nether": 1}),
    AchievementDefinition("BLAZE_KILL", "Crematorio", "Elimina a tu primer Blaze.", AchievementCategory.SPECIAL, {"kill:entity.minecraft.blaze": 1}),
    AchievementDefinition("PIGLIN_TRADE", "Usurero de almas", "Realiza un intercambio con un Piglin.", AchievementCategory.SPECIAL, {"piglin_barter": 1}),
    
    # --- THE END ---
    AchievementDefinition("END_ENTER", "El abismo te devuelve la mirada", "Entra al End por primera vez.", AchievementCategory.SPECIAL, {"dimension_enter:minecraft:the_end": 1}),
    AchievementDefinition("END_DRAGON_KILL", "te sientes un heroe ahora?", "Elimina al Dragon del Fin.", AchievementCategory.SPECIAL, {"kill:entity.minecraft.ender_dragon": 1}),
    AchievementDefinition("WITHER_KILL", "Necrosis", "Elimina al Wither.", AchievementCategory.SPECIAL, {"kill:entity.minecraft.wither": 1}),
    AchievementDefinition("END_VICTORY", "Esquizofrenia", "Elimina a 100 Endermans.", AchievementCategory.SPECIAL, {"kill:entity.minecraft.enderman": 100}),
]
