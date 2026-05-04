from ..base import AchievementDefinition, AchievementCategory

LOOT_ACHIEVEMENTS = [
    # --- MATERIALES BÁSICOS Y MISERIA ---
    AchievementDefinition("LOOT_1", "Nacido en el fango", "Recoge 1,000 bloques de tierra.", AchievementCategory.LOOT, {"item_pickup:minecraft:dirt": 1000}, rarity=0.66),
    AchievementDefinition("LOOT_2", "Coleccionista de miseria", "Recoge 10,000 objetos totales del suelo.", AchievementCategory.LOOT, {"item_pickup": 10000}, rarity=0.80),

    # --- RIQUEZA Y CODICIA ---
    AchievementDefinition("LOOT_3", "Corazón de cristal", "Recoge 64 diamantes.", AchievementCategory.LOOT, {"item_pickup:minecraft:diamond": 64}, rarity=0.06),
    AchievementDefinition("LOOT_4", "Supremacía material", "Recoge 20 fragmentos de netherite.", AchievementCategory.LOOT, {"item_pickup:minecraft:ancient_debris": 20}, rarity=0.12),
    
    # --- RELIQUIAS Y PODER ---
    AchievementDefinition("LOOT_5", "Falsa inmortalidad", "Consigue un Totem de la Eternidad.", AchievementCategory.LOOT, {"item_pickup:minecraft:totem_of_undying": 1}, rarity=0.11),
    AchievementDefinition("LOOT_6", "Alas de ceniza", "Consigue unas Elitros.", AchievementCategory.LOOT, {"item_pickup:minecraft:elytra": 1}, rarity=0.13),
    AchievementDefinition("LOOT_7", "Reliquia de sangre", "Consigue una Manzana de Oro Encantada.", AchievementCategory.LOOT, {"item_pickup:minecraft:enchanted_golden_apple": 1}, rarity=0.11),
]
