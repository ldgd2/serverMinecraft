from ..base import AchievementDefinition, AchievementCategory

DIMENSION_ACHIEVEMENTS = [
    # --- NETHER ---
    AchievementDefinition("NETHER_ENTER", "Abandona toda esperanza", "Entra al Nether por primera vez.", AchievementCategory.SPECIAL, {
        "dimension_enter:minecraft:the_nether": 1, 
        "dimension:the_nether": 1,
        "dimension:minecraft:the_nether": 1
    }),
    AchievementDefinition("BLAZE_KILL", "Crematorio", "Elimina a tu primer Blaze.", AchievementCategory.SPECIAL, {"kill:entity.minecraft.blaze": 1}, rarity=0.51),
    AchievementDefinition("PIGLIN_TRADE", "Usurero de almas", "Realiza un intercambio con un Piglin.", AchievementCategory.SPECIAL, {"piglin_barter": 1}, rarity=0.09),
    
    # Adiciones refinadas del Nether
    AchievementDefinition("GHAST_KILL", "Caza-Fantasmas", "Devuelve un alma al más allá eliminando un Ghast.", AchievementCategory.SPECIAL, {"kill:entity.minecraft.ghast": 1}, rarity=0.53),
    AchievementDefinition("WITHER_SKELETON_KILL", "Huesos Negros", "Elimina a un Esqueleto Wither.", AchievementCategory.SPECIAL, {"kill:entity.minecraft.wither_skeleton": 1}, rarity=0.81),
    AchievementDefinition("PIGLIN_BRUTE_KILL", "Fuerza bruta", "Derrota a un Piglin Bruto defendiendo su tesoro.", AchievementCategory.SPECIAL, {"kill:entity.minecraft.piglin_brute": 1}, rarity=0.46),
    AchievementDefinition("MAGMA_CUBE_KILL", "Rebotes Calientes", "Destruye a un Cubo de Magma.", AchievementCategory.SPECIAL, {"kill:entity.minecraft.magma_cube": 1}, rarity=0.47),
    AchievementDefinition("HOGLIN_KILL", "Tocino infernal", "Convierte a un Hoglin en la cena de hoy.", AchievementCategory.SPECIAL, {"kill:entity.minecraft.hoglin": 1}, rarity=0.52),
    AchievementDefinition("ANCIENT_DEBRIS", "Tesoro sepultado", "Mina Escombros Ancestrales por primera vez.", AchievementCategory.SPECIAL, {"mine_ancient_debris": 1}, rarity=0.07),
    AchievementDefinition("ANCIENT_DEBRIS_10", "Avaricia en el infierno", "Mina 10 Escombros Ancestrales.", AchievementCategory.SPECIAL, {"mine_ancient_debris": 10}, rarity=0.07),
    
    # --- THE END ---
    AchievementDefinition("END_ENTER", "El abismo te devuelve la mirada", "Entra al End por primera vez.", AchievementCategory.SPECIAL, {"dimension_enter:minecraft:the_end": 1}, rarity=0.10),
    AchievementDefinition("END_DRAGON_KILL", "te sientes un heroe ahora?", "Elimina al Dragon del Fin.", AchievementCategory.SPECIAL, {"kill:entity.minecraft.ender_dragon": 1}, rarity=0.86),
    AchievementDefinition("WITHER_KILL", "Necrosis", "Elimina al Wither.", AchievementCategory.SPECIAL, {"kill:entity.minecraft.wither": 1}, rarity=0.89),
    AchievementDefinition("END_VICTORY", "Esquizofrenia", "Elimina a 100 Endermans.", AchievementCategory.SPECIAL, {"kill:entity.minecraft.enderman": 100}, rarity=0.47),
]
