from ..base import AchievementDefinition, AchievementCategory

FARMING_ACHIEVEMENTS = [
    # --- VOLUMEN GENERAL ---
    AchievementDefinition("FARM_1", "Farmeo", "Cosecha 1,000 cultivos.", AchievementCategory.FARMING, {"crop_harvested": 1000}, rarity=0.66),
    AchievementDefinition("FARM_2", "Mentalidad de tiburón", "Cosecha 5,000 cultivos.", AchievementCategory.FARMING, {"crop_harvested": 5000}, rarity=0.67),
    AchievementDefinition("FARM_3", "Aura +10000", "Cosecha 50,000 cultivos.", AchievementCategory.FARMING, {"crop_harvested": 50000}, rarity=0.81),
    AchievementDefinition("FARM_ULTRA", "Cosecha de almas", "Cosecha 100,000 cultivos totales.", AchievementCategory.FARMING, {"crop_harvested": 100000}, rarity=1.00),

    # --- CULTIVOS ESPECÍFICOS ---
    # Papas (Pobreza)
    AchievementDefinition("FARM_POTATO_1", "Primeros Pasos", "Cosecha tu primera papa.", AchievementCategory.FARMING, {"crop:minecraft:potatoes": 1, "block_broken:minecraft:potatoes": 1}, rarity=0.11),
    AchievementDefinition("FARM_POTATO", "Dieta tercermundista", "Cosecha 500 papas.", AchievementCategory.FARMING, {"crop:minecraft:potatoes": 500}, rarity=0.43),
    
    # Zanahorias
    AchievementDefinition("FARM_CARROT_1", "Vitamina A", "Cosecha tu primera zanahoria.", AchievementCategory.FARMING, {"crop:minecraft:carrots": 1, "block_broken:minecraft:carrots": 1}, rarity=0.13),
    AchievementDefinition("FARM_CARROT", "Conejo de la Suerte", "Cosecha 500 zanahorias.", AchievementCategory.FARMING, {"crop:minecraft:carrots": 500}, rarity=0.39),

    # Trigo (Trabajo forzado)
    AchievementDefinition("FARM_WHEAT", "Trabajo forzado", "Cosecha 1,000 unidades de trigo.", AchievementCategory.FARMING, {"crop:minecraft:wheat": 1000}, rarity=0.63),
    
    # Caña de Azúcar (Tráfico)
    AchievementDefinition("FARM_SUGAR_1", "Traficante de azucar", "Cosecha 1,000 cañas de azucar.", AchievementCategory.FARMING, {"crop:minecraft:sugar_cane": 1000}, rarity=0.69),
    AchievementDefinition("FARM_SUGAR_2", "Diabetes infantil", "Cosecha 5,000 cañas de azucar.", AchievementCategory.FARMING, {"crop:minecraft:sugar_cane": 5000}, rarity=0.63),
    
    # Verrugas del Nether (Sustancias Prohibidas)
    AchievementDefinition("FARM_NETHER", "Hierba del diablo", "Cosecha 500 verrugas del Nether.", AchievementCategory.FARMING, {"crop:minecraft:nether_wart": 500}, rarity=0.39),
    
    # Bayas (Dolor)
    AchievementDefinition("FARM_BERRY", "Pinchazos dulces", "Cosecha 250 bayas dulces.", AchievementCategory.FARMING, {"crop:minecraft:sweet_berries": 250}, rarity=0.40),
]

