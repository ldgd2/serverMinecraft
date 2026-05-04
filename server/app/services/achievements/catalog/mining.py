from ..base import AchievementDefinition, AchievementCategory

MINING_ACHIEVEMENTS = [
    AchievementDefinition("MINER_1", "Mano de obra barata", "Mina 100 bloques.", AchievementCategory.MINING, {"block_broken": 100}, rarity=0.37),
    AchievementDefinition("MINER_2", "Sin luz al final del tunel", "Mina 500 bloques.", AchievementCategory.MINING, {"block_broken": 500}, rarity=0.36),
    AchievementDefinition("MINER_3", "Pulmon negro", "Mina 1,000 bloques.", AchievementCategory.MINING, {"block_broken": 1000}, rarity=0.65),
    AchievementDefinition("MINER_4", "Ecocidio sistematico", "Mina 5,000 bloques.", AchievementCategory.MINING, {"block_broken": 5000}, rarity=0.62),
    AchievementDefinition("MINER_5", "Aniquilacion del relieve", "Mina 10,000 bloques.", AchievementCategory.MINING, {"block_broken": 10000}, rarity=0.85),
    AchievementDefinition("MINER_ELITE", "Devorador de mundos", "Mina 50,000 bloques.", AchievementCategory.MINING, {"block_broken": 50000}, rarity=0.88),
    
    # --- MINERALES PRECIOSOS ---
    AchievementDefinition("MINE_DIAMOND", "Fiebre de diamante", "Encuentra y mina tu primer mineral de diamante.", AchievementCategory.MINING, {"mine_diamond": 1}, rarity=0.14),
    AchievementDefinition("MINE_DIAMOND_64", "Capitalismo puro", "Mina 64 minerales de diamante.", AchievementCategory.MINING, {"mine_diamond": 64}, rarity=0.06),
    AchievementDefinition("MINER_BRUTAL", "Devorador de Tierras", "Has alcanzado los 500,000 bloques minados.", AchievementCategory.MINING, {"block_broken": 500000}, rarity=0.99),
]
