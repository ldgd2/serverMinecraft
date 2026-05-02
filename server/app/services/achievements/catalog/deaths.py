from ..base import AchievementDefinition, AchievementCategory

# --- HELPER PARA GENERAR LOGROS POR TIERS (OPCIONAL, PERO LO HAREMOS EXPLÍCITO) ---
# Tiers: 1, 10, 50, 75, 100, 250, 500, 1000

DEATH_ACHIEVEMENTS = [
    # ==========================================
    # --- JUGADORES (PVP) ---
    # ==========================================
    AchievementDefinition("DEATH_PVP_1", "Duelo de sangre", "Muere contra otro jugador por primera vez.", AchievementCategory.DEATH, {"death:player": 1}),
    AchievementDefinition("DEATH_PVP_10", "Humillado", "Muere 10 veces contra jugadores.", AchievementCategory.DEATH, {"death:player": 10}),
    AchievementDefinition("DEATH_PVP_50", "Juguete del servidor", "Muere 50 veces contra jugadores.", AchievementCategory.DEATH, {"death:player": 50}),
    AchievementDefinition("DEATH_PVP_75", "Saco de boxeo", "Muere 75 veces contra jugadores.", AchievementCategory.DEATH, {"death:player": 75}),
    AchievementDefinition("DEATH_PVP_100", "Victima recurrente", "Muere 100 veces contra jugadores.", AchievementCategory.DEATH, {"death:player": 100}),
    AchievementDefinition("DEATH_PVP_250", "Alfileres humanos", "Muere 250 veces contra jugadores.", AchievementCategory.DEATH, {"death:player": 250}),
    AchievementDefinition("DEATH_PVP_500", "Masoquista del PVP", "Muere 500 veces contra jugadores.", AchievementCategory.DEATH, {"death:player": 500}),
    AchievementDefinition("DEATH_PVP_1000", "Inmortal por humillacion", "Muere 1,000 veces contra jugadores.", AchievementCategory.DEATH, {"death:player": 1000}),

    # ==========================================
    # --- ZOMBIES ---
    # ==========================================
    AchievementDefinition("DEATH_ZOMB_1", "Cae un guerrero", "Muere por un Zombie.", AchievementCategory.DEATH, {"death:entity.minecraft.zombie": 1}),
    AchievementDefinition("DEATH_ZOMB_10", "Cerebro de esponja", "Muere 10 veces por Zombies.", AchievementCategory.DEATH, {"death:entity.minecraft.zombie": 10}),
    AchievementDefinition("DEATH_ZOMB_50", "Zombie honorario", "Muere 50 veces por Zombies.", AchievementCategory.DEATH, {"death:entity.minecraft.zombie": 50}),
    AchievementDefinition("DEATH_ZOMB_100", "Buffet libre", "Muere 100 veces por Zombies.", AchievementCategory.DEATH, {"death:entity.minecraft.zombie": 100}),
    AchievementDefinition("DEATH_ZOMB_500", "Infectado cronico", "Muere 500 veces por Zombies.", AchievementCategory.DEATH, {"death:entity.minecraft.zombie": 500}),

    # ==========================================
    # --- CREEPERS ---
    # ==========================================
    AchievementDefinition("DEATH_CREEP_1", "Sacrificio explosivo", "Muere por un Creeper.", AchievementCategory.DEATH, {"death:entity.minecraft.creeper": 1}),
    AchievementDefinition("DEATH_CREEP_10", "Iman de polvora", "Muere 10 veces por Creepers.", AchievementCategory.DEATH, {"death:entity.minecraft.creeper": 10}),
    AchievementDefinition("DEATH_CREEP_50", "Cero reflejos", "Muere 50 veces por Creepers.", AchievementCategory.DEATH, {"death:entity.minecraft.creeper": 50}),
    AchievementDefinition("DEATH_CREEP_100", "Cero reflejos premium", "Muere 100 veces por Creepers.", AchievementCategory.DEATH, {"death:entity.minecraft.creeper": 100}),
    AchievementDefinition("DEATH_CREEP_500", "Kamikaze involuntario", "Muere 500 veces por Creepers.", AchievementCategory.DEATH, {"death:entity.minecraft.creeper": 500}),

    # ==========================================
    # --- ESQUELETOS ---
    # ==========================================
    AchievementDefinition("DEATH_SKELE_1", "Blanco de leyenda", "Muere por un Esqueleto.", AchievementCategory.DEATH, {"death:entity.minecraft.skeleton": 1}),
    AchievementDefinition("DEATH_SKELE_50", "Puercoespin humano", "Muere 50 veces por Esqueletos.", AchievementCategory.DEATH, {"death:entity.minecraft.skeleton": 50}),
    AchievementDefinition("DEATH_SKELE_100", "Diana de practicas", "Muere 100 veces por Esqueletos.", AchievementCategory.DEATH, {"death:entity.minecraft.skeleton": 100}),

    # ==========================================
    # --- CAUSAS AMBIENTALES (MULTIPLE) ---
    # ==========================================
    # CAÍDA
    AchievementDefinition("DEATH_FALL_1", "Vuelo eterno", "Muere por caida.", AchievementCategory.DEATH, {"death:cause.fall": 1}),
    AchievementDefinition("DEATH_FALL_100", "Alfombra de concreto", "Muere 100 veces por caida.", AchievementCategory.DEATH, {"death:cause.fall": 100}),
    
    # LAVA
    AchievementDefinition("DEATH_LAVA_1", "Purificacion ignea", "Muere en lava.", AchievementCategory.DEATH, {"death:cause.lava": 1}),
    AchievementDefinition("DEATH_LAVA_100", "Cena rostizada", "Muere 100 veces en lava.", AchievementCategory.DEATH, {"death:cause.lava": 100}),

    # VACÍO
    AchievementDefinition("DEATH_VOID_1", "Borrado de la existencia", "Muere en el vacio.", AchievementCategory.DEATH, {"death:cause.out_of_world": 1}),
    AchievementDefinition("DEATH_VOID_10", "Viajero del cosmos", "Muere 10 veces en el vacio.", AchievementCategory.DEATH, {"death:cause.out_of_world": 10}),

    # MAGIA / POCIONES
    AchievementDefinition("DEATH_MAGIC_1", "Corrupcion interna", "Muere por magia o pociones.", AchievementCategory.DEATH, {"death:cause.magic": 1}),
    AchievementDefinition("DEATH_MAGIC_10", "Sobredosis mistica", "Muere 10 veces por magia.", AchievementCategory.DEATH, {"death:cause.magic": 10}),

    # ASFIXIA EN BLOQUES
    AchievementDefinition("DEATH_SUFF_1", "Claustrofobia", "Muere asfixiado en un bloque.", AchievementCategory.DEATH, {"death:cause.in_wall": 1}),
    AchievementDefinition("DEATH_SUFF_10", "Enterrado en vida", "Muere 10 veces asfixiado en bloques.", AchievementCategory.DEATH, {"death:cause.in_wall": 10}),

    # RAYOS
    AchievementDefinition("DEATH_LIGHT_1", "Castigo de los dioses", "Muere por un rayo.", AchievementCategory.DEATH, {"death:cause.lightning_bolt": 1}),
    AchievementDefinition("DEATH_LIGHT_5", "Pararrayos humano", "Muere 5 veces por rayos.", AchievementCategory.DEATH, {"death:cause.lightning_bolt": 5}),

    # ==========================================
    # --- OTROS MOBS (UN TIERS) ---
    # ==========================================
    AchievementDefinition("DEATH_WARDEN", "Silencio eterno", "Muere por el Warden.", AchievementCategory.DEATH, {"death:entity.minecraft.warden": 1}),
    AchievementDefinition("DEATH_DRAGON", "Cena de Dragon", "Muere por el Dragon del Fin.", AchievementCategory.DEATH, {"death:entity.minecraft.ender_dragon": 1}),
    AchievementDefinition("DEATH_WITHER", "Necrosis", "Muere por el Wither.", AchievementCategory.DEATH, {"death:entity.minecraft.wither": 1}),
    AchievementDefinition("DEATH_IRON_GOLEM", "Justicia de hierro", "Muere por un Iron Golem.", AchievementCategory.DEATH, {"death:entity.minecraft.iron_golem": 1}),
]
