from ..base import AchievementDefinition, AchievementCategory

MINING_ACHIEVEMENTS = [
    AchievementDefinition("MINER_1", "Mano de obra barata", "Mina 100 bloques.", AchievementCategory.MINING, {"block_broken": 100}),
    AchievementDefinition("MINER_2", "Sin luz al final del tunel", "Mina 500 bloques.", AchievementCategory.MINING, {"block_broken": 500}),
    AchievementDefinition("MINER_3", "Pulmon negro", "Mina 1,000 bloques.", AchievementCategory.MINING, {"block_broken": 1000}),
    AchievementDefinition("MINER_4", "Ecocidio sistematico", "Mina 5,000 bloques.", AchievementCategory.MINING, {"block_broken": 5000}),
    AchievementDefinition("MINER_5", "Aniquilacion del relieve", "Mina 10,000 bloques.", AchievementCategory.MINING, {"block_broken": 10000}),
    AchievementDefinition("MINER_ELITE", "Devorador de mundos", "Mina 50,000 bloques.", AchievementCategory.MINING, {"block_broken": 50000}),
    
    # --- MINERALES PRECIOSOS ---
    AchievementDefinition("MINE_DIAMOND", "Fiebre de diamante", "Encuentra y mina tu primer mineral de diamante.", AchievementCategory.MINING, {"mine_diamond": 1}),
    AchievementDefinition("MINE_DIAMOND_64", "Capitalismo puro", "Mina 64 minerales de diamante.", AchievementCategory.MINING, {"mine_diamond": 64}),
]
