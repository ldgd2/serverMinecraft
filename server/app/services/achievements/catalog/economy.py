from ..base import AchievementDefinition, AchievementCategory

ECONOMY_ACHIEVEMENTS = [
    # --- INICIACIÓN ---
    AchievementDefinition("ECON_1", "6.98?", "Consigue tu primera esmeralda.", AchievementCategory.ECONOMY, {"item_acquired:minecraft:emerald": 1}, rarity=0.12),
    AchievementDefinition("ECON_2", "Vendedor de humo", "Realiza tu primera venta a otro jugador.", AchievementCategory.ECONOMY, {"player_sale": 1}, rarity=0.06),
    
    # --- COMERCIO Y ALDEANOS ---
    AchievementDefinition("ECON_TRADE_50", "blue o paralelo", "Intercambia con aldeanos 50 veces.", AchievementCategory.ECONOMY, {"villager_trade": 50}, rarity=0.10),
    AchievementDefinition("ECON_TRADE_500", "Lobo de Wall Street", "Intercambia con aldeanos 500 veces.", AchievementCategory.ECONOMY, {"villager_trade": 500}, rarity=0.38),
    
    # --- ACUMULACIÓN DE RIQUEZA (EL 1%) ---
    AchievementDefinition("ECON_BAL_10K", "precio por inbox", "Acumula 10,000 esmeraldas.", AchievementCategory.ECONOMY, {"emerald_balance": 10000}, rarity=0.81),
    AchievementDefinition("ECON_BAL_50K", "Capitalismo salvaje", "Acumula 50,000 esmeraldas.", AchievementCategory.ECONOMY, {"emerald_balance": 50000}, rarity=0.83),
    AchievementDefinition("ECON_BAL_100K", "El 1%", "Acumula 100,000 esmeraldas.", AchievementCategory.ECONOMY, {"emerald_balance": 100000}, rarity=0.94),
    AchievementDefinition("ECON_BAL_1M", "Dueño del servidor", "Acumula 1,000,000 esmeraldas.", AchievementCategory.ECONOMY, {"emerald_balance": 1000000}, rarity=0.95),

    # --- GASTOS Y CONSUMISMO ---
    AchievementDefinition("ECON_SPEND_5K", "Lavado de activos", "Gasta 5,000 esmeraldas totales.", AchievementCategory.ECONOMY, {"emerald_spent": 5000}, rarity=0.68),
    AchievementDefinition("ECON_SPEND_50K", "Inflacion galopante", "Gasta 50,000 esmeraldas totales.", AchievementCategory.ECONOMY, {"emerald_spent": 50000}, rarity=0.90),
    AchievementDefinition("ECON_LUXURY", "Lujo obsceno", "Compra un objeto de elite (Faro o Manzana Notch).", AchievementCategory.ECONOMY, {"luxury_item_bought": 1}, rarity=0.14),
]
