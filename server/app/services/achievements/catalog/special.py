from ..base import AchievementDefinition, AchievementCategory

SPECIAL_ACHIEVEMENTS = [
    AchievementDefinition("LOGIN_0", "mi primera chamba", "Entra al servidor por primera vez.", AchievementCategory.SPECIAL, {"login_count": 1}, rarity=0.07),
    AchievementDefinition("LOGIN_1", "ey ey ey ey", "Inicia sesión 5 veces.", AchievementCategory.SPECIAL, {"login_count": 5}, rarity=0.10),
    AchievementDefinition("LOGIN_2", "Dios, soy yo de nuevo", "Inicia sesión 25 veces.", AchievementCategory.SPECIAL, {"login_count": 25}, rarity=0.07),
    AchievementDefinition("LOGIN_3", "Las voces ganaron", "Inicia sesión 50 veces.", AchievementCategory.SPECIAL, {"login_count": 50}, rarity=0.10),
    AchievementDefinition("LOGIN_4", "El verdadero quién pudiera", "Inicia sesión 100 veces.", AchievementCategory.SPECIAL, {"login_count": 100}, rarity=0.39),
    AchievementDefinition("LOGIN_5", "No lo entenderías", "Inicia sesión 250 veces.", AchievementCategory.SPECIAL, {"login_count": 250}, rarity=0.38),

    # --- RACHAS Y LEALTAD ---
    AchievementDefinition("STREAK_7", "Adiccion severa", "Inicia sesion durante 7 dias consecutivos.", AchievementCategory.SPECIAL, {"login_streak": 7}, rarity=0.07),
    AchievementDefinition("STREAK_30", "No tocas pasto", "Inicia sesion durante 30 dias consecutivos.", AchievementCategory.SPECIAL, {"login_streak": 30}, rarity=0.11),

    # --- HORARIOS Y EVENTOS ---
    AchievementDefinition("NIGHT_OWL", "Paralisis del sueño", "Juega entre las 3:00 AM y las 5:00 AM.", AchievementCategory.SPECIAL, {"play_at_night": 1}, rarity=0.14),
    AchievementDefinition("EARLY_BIRD", "A quien madruga...", "...Dios lo deja solo.", AchievementCategory.SPECIAL, {"play_at_dawn": 1}, rarity=0.14),

    # --- EXCLUSIVIDAD ---
    AchievementDefinition("FOUNDER", "Fundador del abismo", "Se uno de los primeros 100 jugadores en unirse al servidor.", AchievementCategory.SPECIAL, {"is_founder": 1}, rarity=0.14),

    # --- SESIONES EXTREMAS ---
    AchievementDefinition("SESSION_5H", "Perdida de nocion", "Juega durante 5 horas seguidas.", AchievementCategory.SPECIAL, {"session_time_seconds": 18000}, rarity=0.89),
    AchievementDefinition("SESSION_10H", "Esclavo del monitor", "Juega durante 10 horas seguidas.", AchievementCategory.SPECIAL, {"session_time_seconds": 36000}, rarity=0.85),
    AchievementDefinition("SESSION_24H", "Desconexion de la realidad", "Juega durante 24 horas seguidas.", AchievementCategory.SPECIAL, {"session_time_seconds": 86400}, rarity=0.83),

    # --- SUPERVIVENCIA Y DESGRACIA ---
    AchievementDefinition("TOTEM_1", "Casi...", "Utiliza un Totem de la Eternidad por primera vez.", AchievementCategory.SPECIAL, {"totem_used": 1}, rarity=0.13),
    AchievementDefinition("TOTEM_10", "Inmortal a base de trampas", "Utiliza 10 Totems de la Eternidad.", AchievementCategory.SPECIAL, {"totem_used": 10}, rarity=0.07),
    AchievementDefinition("RAID_1", "Heroe de mentira", "Completa una Invasion (Raid) con exito.", AchievementCategory.SPECIAL, {"raids_completed": 1}, rarity=0.05),
    AchievementDefinition("RAID_10", "Señor de la guerra", "Completa 10 Invasiones.", AchievementCategory.SPECIAL, {"raids_completed": 10}, rarity=0.11),

    # --- COMPORTAMIENTO META ---
    AchievementDefinition("AFK_1H", "Fantasma en la maquina", "Quedate AFK durante 1 hora seguida.", AchievementCategory.SPECIAL, {"afk_seconds": 3600}, rarity=0.63),
    AchievementDefinition("TRADER_10", "Estafado", "Realiza 10 intercambios con el Vendedor Ambulante.", AchievementCategory.SPECIAL, {"wandering_trader_trade": 10}, rarity=0.09),
    AchievementDefinition("MAINTENANCE_JOIN", "Ansiedad social", "Entra al servidor en los primeros 60 segundos tras un reinicio.", AchievementCategory.SPECIAL, {"join_after_restart": 1}, rarity=0.11),

    # --- CURIOSIDADES ---
    AchievementDefinition("DRAGON_EGG", "El fin justifica los medios", "Consigue el Huevo de Dragon.", AchievementCategory.SPECIAL, {"has_dragon_egg": 1}, rarity=0.84),
    AchievementDefinition("GOD_OF_WAR", "God of war", "Elimina a 1,000 entidades hostiles.", AchievementCategory.SPECIAL, {"hostile_kills": 1000}, rarity=0.60),
    AchievementDefinition("MOUNT_MASTER", "Montaras", "Recorre 10,000 bloques montado en un animal.", AchievementCategory.SPECIAL, {"distance_mounted": 10000}, rarity=0.84),
    AchievementDefinition("HUNGER_GAMES", "Los juegos del hambre", "Gana tu primer evento de supervivencia o torneo PVP.", AchievementCategory.SPECIAL, {"tournaments_won": 1}, rarity=0.08),
    AchievementDefinition("WHAT_NOW", "Y que hago con esto", "Consigue una Patata Venenosa.", AchievementCategory.SPECIAL, {"item_acquired:minecraft:poisonous_potato": 1}, rarity=0.13),
    AchievementDefinition("WTF_IS_THAT", "Que diablos es eso", "Encuentra una Oveja Rosa de forma natural.", AchievementCategory.SPECIAL, {"pink_sheep_found": 1}, rarity=0.06),
    AchievementDefinition("YOU_ARE_GOOD", "Ya sos bien", "Alcanza el nivel 100 de experiencia.", AchievementCategory.SPECIAL, {"xp_level": 100}, rarity=0.36),
    AchievementDefinition("EVEREST", "El monte everest no tiene nada malo contra de mi", "Alcanza la altura maxima del mundo (Y=320).", AchievementCategory.SPECIAL, {"max_height_reached": 1}, rarity=0.07),
    AchievementDefinition("FEAR_PARALYSIS", "Estaba paralizado con mucho miedo y no me podia mover", "Se afectado por el efecto de Oscuridad del Warden.", AchievementCategory.SPECIAL, {"warden_darkness_effect": 1}, rarity=0.86),

    # --- LOGROS OCULTOS Y ESPECÍFICOS ---
    AchievementDefinition("GHAST_RETURN", "Devolucion de cortesia", "Elimina a un Ghast devolviéndole su propia bola de fuego.", AchievementCategory.SPECIAL, {"ghast_fireball_kill": 1}, rarity=0.46),
    AchievementDefinition("CLUTCH_SURVIVAL", "Por un pelo", "Sobrevive a una caida de mas de 30 bloques con medio corazon de vida.", AchievementCategory.SPECIAL, {"clutch_survival": 1}, rarity=0.10),
    AchievementDefinition("NETHER_SLEEP", "Sueño explosivo", "Intenta dormir en una cama en el Nether.", AchievementCategory.SPECIAL, {"nether_bed_explosion": 1}, rarity=0.15),
    AchievementDefinition("STRIDER_TAXI", "Dj Zeguita", "Recorre 5,000 bloques montado en un Lavagante sobre lava.", AchievementCategory.SPECIAL, {"strider_lava_distance": 5000}, rarity=0.68),
    AchievementDefinition("MANY_EFFECTS", "Farmacia andante", "Ten 10 efectos de estado activos al mismo tiempo.", AchievementCategory.SPECIAL, {"active_effects_count": 10}, rarity=0.14),
    AchievementDefinition("SNIPER_DUEL", "Duelo a distancia", "Elimina a un Esqueleto con una flecha desde mas de 50 metros.", AchievementCategory.SPECIAL, {"skeleton_snipe_distance": 50}, rarity=0.11),
    AchievementDefinition("CACTUS_FAIL", "Darwin Award", "Muere por un cactus mientras llevas una armadura de Netherite completa.", AchievementCategory.SPECIAL, {"netherite_cactus_death": 1}, rarity=0.49),
    AchievementDefinition("VANDALISM", "Vandalismo artistico", "Rompe 50 pinturas (cuadros) de otros jugadores.", AchievementCategory.SPECIAL, {"paintings_broken": 50}, rarity=0.14),

    # --- MEMES Y CULTURA ---
    AchievementDefinition("MEME_BED_DRAGON", "Simplemente epico", "Elimina al Dragon del Fin usando una cama.", AchievementCategory.SPECIAL, {"dragon_killed_by_bed": 1}, rarity=0.89),
    AchievementDefinition("MEME_VOID_STARK", "No me quiero ir Sr. Stark", "Muere al caer al vacio con un inventario lleno.", AchievementCategory.SPECIAL, {"full_inventory_void_death": 1}, rarity=0.70),
    AchievementDefinition("MEME_HUMILDAD", "Humildad", "Regala un stack de diamantes (64) a otro jugador.", AchievementCategory.SPECIAL, {"diamonds_gifted": 64}, rarity=0.73),
    AchievementDefinition("MEME_ANTOJEN", "No antojen", "Sostén un Pastel en la mano frente a 5 jugadores.", AchievementCategory.SPECIAL, {"hold_cake_near_players": 1}, rarity=0.70),
    AchievementDefinition("join_on_anniversary", "Es hoy, es hoy", "Entra al servidor en el dia de tu cumpleaños o aniversario del server.", AchievementCategory.SPECIAL, {"join_on_anniversary": 1}, rarity=0.11),
    AchievementDefinition("MEME_POV_VILLAGER", "POV: Eres un aldeano", "Se atacado por un jugador mientras no llevas armadura.", AchievementCategory.SPECIAL, {"attacked_without_armor": 1}, rarity=0.69),
    AchievementDefinition("MEME_EL_PEPE", "El Pepe", "Cambia tu nombre de usuario por primera vez.", AchievementCategory.SPECIAL, {"name_changed": 1}, rarity=0.73),
    AchievementDefinition("MEME_SOLO_UN_CAPO", "Ya me quieres igualar", "Alcanza el nivel 50 de experiencia sin haber muerto nunca.", AchievementCategory.SPECIAL, {"lvl_50_no_death": 1}, rarity=0.70),
    AchievementDefinition("MEME_MI_MOMENTO", "Mi momento ha llegado", "Muere por una explosion de TNT provocada por ti mismo.", AchievementCategory.SPECIAL, {"self_tnt_death": 1}, rarity=0.73),
    
    # --- NUEVAS ADICIONES ---
    AchievementDefinition("MEME_POBRES", "ya comieron pobres?", "Consume un Filete (Steak) frente a otro jugador.", AchievementCategory.SPECIAL, {"eat_steak_near_player": 1}, rarity=0.69),
    AchievementDefinition("MEME_VIBORA", "si fuera una vibora ya te hubiera picado", "Encuentra tu primer Tesoro Enterrado.", AchievementCategory.SPECIAL, {"buried_treasure_found": 1}, rarity=0.73),
    AchievementDefinition("MEME_SUPER_POLLO", "un super?", "Ten un stack (64) de Pollo Cocinado en el inventario.", AchievementCategory.SPECIAL, {"cooked_chicken_stack": 1}, rarity=0.66),
    
    # --- EDGY & CULTURA DE INTERNET ---
    AchievementDefinition("MEME_SKILL_ISSUE", "Skill Issue", "Muere contra un Baby Zombie usando armadura de Netherite completa.", AchievementCategory.COMBAT, {"skill_issue_death": 1}, rarity=0.73),
    AchievementDefinition("MEME_NO_AFECTO", "Pov: No tienes afecto femenino", "Pica 1,000 bloques de Obsidiana.", AchievementCategory.MINING, {"mine_obsidian": 1000}, rarity=0.68),
    AchievementDefinition("MEME_TURBIO", "Turbio...", "Asesina a un Ajolote.", AchievementCategory.SPECIAL, {"kill_axolotl": 1}, rarity=0.72),
    AchievementDefinition("MEME_CHAMBA_PRO", "Pendejo no dura nada", "Rompe una herramienta de Netherite por exceso de uso.", AchievementCategory.SPECIAL, {"netherite_tool_broken": 1}, rarity=0.68),
    AchievementDefinition("MEME_CINE", "Porque el que graba no ayuda", "Presencia cómo un Creeper elimina a otra entidad.", AchievementCategory.SPECIAL, {"creeper_kill_witness": 1}, rarity=0.73),

    # --- LOGROS EXISTENCIALES ---
    AchievementDefinition("PHILO_GUILT", "Todo esto es tu culpa.", "Asesina a un aldeano inocente.", AchievementCategory.SPECIAL, {"kill_villager": 1}, rarity=0.75),
    AchievementDefinition("PHILO_PURPOSE", "¿Puedes siquiera recordar por qué viniste aquí?", "Alcanza las 50 horas de juego totales.", AchievementCategory.VETERAN, {"playtime_seconds": 180000}, rarity=0.99),
    AchievementDefinition("PHILO_WAKE", "Es hora de que despiertes.", "Regresa al servidor tras una semana de ausencia.", AchievementCategory.SPECIAL, {"return_after_7d": 1}, rarity=0.68),
    AchievementDefinition("PHILO_KILL_ENT", "Matar por entretenimiento es inofensivo.", "Elimina a 10,000 entidades totales.", AchievementCategory.COMBAT, {"total_kills": 10000}, rarity=0.87),
    AchievementDefinition("PHILO_NECESSARY", "No hay diferencia entre lo que está bien y lo que es necesario.", "Saquea un cofre de una aldea.", AchievementCategory.SPECIAL, {"loot_village_chest": 1}, rarity=0.75),
    AchievementDefinition("PHILO_NO_HOME", "No puedes volver a casa.", "Entra en la dimensión del Fin.", AchievementCategory.DIMENSIONS, {"enter_dimension:minecraft:the_end": 1}, rarity=0.74),
    AchievementDefinition("PHILO_GOD", "Mata a todos, y eres un dios.", "Elimina a 50,000 entidades totales.", AchievementCategory.COMBAT, {"total_kills": 50000}, rarity=0.89),
    AchievementDefinition("PHILO_WEAKNESS", "Este no es el momento para la debilidad.", "Elimina al Warden.", AchievementCategory.COMBAT, {"kill_warden": 1}, rarity=0.85),
    AchievementDefinition("PHILO_DAILY", "¿A cuántos mobs has matado hoy?", "Elimina a 500 mobs en una sola sesión.", AchievementCategory.COMBAT, {"session_kills": 500}, rarity=0.66),
    AchievementDefinition("PHILO_SLEEP", "¿Al menos duermes tranquilo?", "Duerme en una cama teniendo el efecto de Mal Presagio.", AchievementCategory.SPECIAL, {"sleep_with_bad_omen": 1}, rarity=0.71),

    # --- CITAS Y SARCASMO ---
    AchievementDefinition("MEME_WOLF", "El lobo no es un león, pero no actúa en el circo.", "Domestica a tu primer lobo.", AchievementCategory.SPECIAL, {"tame_wolf": 1}, rarity=0.70),
    AchievementDefinition("MEME_CROSS", "llevando mi cruz", "Muere teniendo un Tótem en el inventario (pero no en la mano).", AchievementCategory.SPECIAL, {"die_with_totem_in_inv": 1}, rarity=0.70),
    AchievementDefinition("MEME_TNT_CRAFT", "no debi inventar el", "Fabrica tu primer bloque de TNT.", AchievementCategory.SPECIAL, {"craft_tnt": 1}, rarity=0.65),
    AchievementDefinition("MEME_TRIPLE_THREAT", "Hay tres cosas que salen siempre", "Muere rodeado por un creeper, un zombie y un esqueleto.", AchievementCategory.SPECIAL, {"triple_threat_death": 1}, rarity=0.66),
    AchievementDefinition("MEME_FIRST_NIGHT", "He pasado una noche estupenda, pero no ha sido ésta.", "Sobrevive tu primera noche en el mundo.", AchievementCategory.SPECIAL, {"survive_first_night": 1}, rarity=0.67),
    AchievementDefinition("MEME_TWO_BRAINS", "Si los seres humanos tuviésemos dos cerebros...", "Muere por tus propios medios (caída o fuego).", AchievementCategory.SPECIAL, {"self_death": 1}, rarity=0.68),
    AchievementDefinition("GAIN_FIRST_XP", "La experiencia es algo maravilloso.", "Gana tus primeros puntos de experiencia.", AchievementCategory.SPECIAL, {"gain_first_xp": 1}, rarity=0.11),
    AchievementDefinition("DIST_1", "Trotamundos", "Has recorrido 10,000 bloques a pie.", AchievementCategory.SPECIAL, {"distance_travelled": 10000}, rarity=0.80),
    AchievementDefinition("DIST_2", "Explorador Legendario", "Has recorrido 100,000 bloques. ¡El mundo no tiene secretos para ti!", AchievementCategory.SPECIAL, {"distance_travelled": 100000}, rarity=0.91),
    AchievementDefinition("TIME_1", "Habitante Local", "Has jugado un total de 10 horas.", AchievementCategory.SPECIAL, {"playtime_seconds": 36000}, rarity=0.85),
    AchievementDefinition("TIME_3", "Veterano del Servidor", "Has jugado un total de 100 horas. ¡Eres parte de la historia!", AchievementCategory.SPECIAL, {"playtime_seconds": 360000}, rarity=0.94),
    AchievementDefinition("PHILO_PURPOSE_NEW", "Propósito Filosófico", "Has pasado 50 horas en el servidor. ¿Qué buscas realmente?", AchievementCategory.SPECIAL, {"playtime_seconds": 180000}, rarity=0.90),
    AchievementDefinition("MEME_FIRST_DEATH", "No es que tenga miedo a morirme...", "Muere por primera vez.", AchievementCategory.SPECIAL, {"first_death": 1}, rarity=0.68),
    AchievementDefinition("MEME_DOG_LOVER", "¿Sabes qué me gusta de las personas? Sus perros.", "Ten 5 lobos domesticados al mismo tiempo.", AchievementCategory.SPECIAL, {"tame_5_dogs": 1}, rarity=0.68),
    AchievementDefinition("MEME_MEMORY", "No guardo rencor, pero tengo buena memoria.", "Sé eliminado por otro jugador.", AchievementCategory.SOCIAL, {"killed_by_player": 1}, rarity=0.69),
    AchievementDefinition("MEME_STAB_FRONT", "Los amigos de verdad te apuñalan de frente.", "Sé eliminado 10 veces por otros jugadores.", AchievementCategory.SOCIAL, {"killed_by_player_10": 1}, rarity=0.75),
    AchievementDefinition("MEME_REVENGE", "Espera de mí, lo que recibo de ti.", "Elimina al jugador que te mató por última vez.", AchievementCategory.SOCIAL, {"revenge_kill": 1}, rarity=0.74),

    # --- ACTITUD Y DESAFÍO ---
    AchievementDefinition("MEME_GG", "GG", "Escribe 'GG' tras eliminar a un jefe (Boss).", AchievementCategory.SPECIAL, {"gg_after_boss": 1}, rarity=0.66),
    AchievementDefinition("MEME_ALL_AGAINST_ME", "Todos contra yo solo", "Muere tras ser atacado por 3 o más jugadores a la vez.", AchievementCategory.SOCIAL, {"died_to_team": 1}, rarity=0.71),
    AchievementDefinition("MEME_ONLY_A_GAME", "solo es un juego.....", "Muere teniendo nivel 100 o más de experiencia.", AchievementCategory.SPECIAL, {"die_with_100_lvl": 1}, rarity=0.75),
    AchievementDefinition("MEME_TRY_AGAIN", "hazlo otra vez, a lo mejor esta vez sí", "Muere por la misma causa 3 veces seguidas en 5 minutos.", AchievementCategory.SPECIAL, {"repeat_death_streak": 1}, rarity=0.66),
    AchievementDefinition("MEME_NO_EGGS", "no hay huevos", "Ataca al Warden con tus propias manos.", AchievementCategory.SPECIAL, {"punch_warden": 1}, rarity=0.87),

    # --- NUEVOS LOGROS EDGYS (DIRECTOS DEL CLIENTE) ---
    AchievementDefinition("DESCEND_MADNESS", "Descendiendo a la Locura", "En lo profundo y ciego, el abismo te devuelve la mirada.", AchievementCategory.SPECIAL, {"DESCEND_MADNESS": 1}, hidden=True, rarity=0.98),
    AchievementDefinition("FATHOMLESS_ABYSS", "Abismo Insondable", "Ahogandote en las profundidades de la desesperacion.", AchievementCategory.SPECIAL, {"FATHOMLESS_ABYSS": 1}, hidden=True, rarity=0.90),
    AchievementDefinition("EDGE_REASON", "El Limite de la Razon", "Aferrado a la vida en el lecho de roca con dos totems.", AchievementCategory.SPECIAL, {"EDGE_REASON": 1}, hidden=True, rarity=1.00),
    AchievementDefinition("BLOOD_SWEAT", "Sudor y Sangre", "Corriendo por tu vida, hambriento y moribundo.", AchievementCategory.SPECIAL, {"BLOOD_SWEAT": 1}, hidden=True, rarity=0.88),
    AchievementDefinition("IMMINENT_MASSACRE", "Masacre Inminente", "Un arsenal de dolor listo en tus manos.", AchievementCategory.SPECIAL, {"IMMINENT_MASSACRE": 1}, hidden=True, rarity=0.80),
    AchievementDefinition("HARVEST_SOULS", "Cosecha de Almas", "El lamento de 500 almas liberadas por tu pico.", AchievementCategory.SPECIAL, {"HARVEST_SOULS": 1}, hidden=True, rarity=0.95),
    
    # --- VETERANIA EXTREMA ---
    AchievementDefinition("TIME_LEGEND", "Leyenda Viviente", "Has dedicado 1,000 horas de tiempo real al servidor.", AchievementCategory.VETERAN, {"playtime_seconds": 3600000}, rarity=0.97),
    AchievementDefinition("TIME_ANCIENT", "Entidad Ancestral", "Supera las 2,500 horas de permanencia activa.", AchievementCategory.VETERAN, {"playtime_seconds": 9000000}, rarity=1.00),
    AchievementDefinition(
        "DOMINATOR", 
        "Dominador Absoluto", 
        "200,000 bloques colocados, 50,000 bajas y 500 horas de juego.", 
        AchievementCategory.VETERAN, 
        {"block_placed": 200000, "kill": 50000, "playtime_seconds": 1800000},
        rarity=1.00
    ),
]
