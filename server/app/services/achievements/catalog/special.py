from ..base import AchievementDefinition, AchievementCategory

SPECIAL_ACHIEVEMENTS = [
    AchievementDefinition("LOGIN_0", "mi primera chamba", "Entra al servidor por primera vez.", AchievementCategory.SPECIAL, {"login_count": 1}),
    AchievementDefinition("LOGIN_1", "ey ey ey ey", "Inicia sesión 5 veces.", AchievementCategory.SPECIAL, {"login_count": 5}),
    AchievementDefinition("LOGIN_2", "Dios, soy yo de nuevo", "Inicia sesión 25 veces.", AchievementCategory.SPECIAL, {"login_count": 25}),
    AchievementDefinition("LOGIN_3", "Las voces ganaron", "Inicia sesión 50 veces.", AchievementCategory.SPECIAL, {"login_count": 50}),
    AchievementDefinition("LOGIN_4", "El verdadero quién pudiera", "Inicia sesión 100 veces.", AchievementCategory.SPECIAL, {"login_count": 100}),
    AchievementDefinition("LOGIN_5", "No lo entenderías", "Inicia sesión 250 veces.", AchievementCategory.SPECIAL, {"login_count": 250}),

    # --- RACHAS Y LEALTAD ---
    AchievementDefinition("STREAK_7", "Adiccion severa", "Inicia sesion durante 7 dias consecutivos.", AchievementCategory.SPECIAL, {"login_streak": 7}),
    AchievementDefinition("STREAK_30", "No tocas pasto", "Inicia sesion durante 30 dias consecutivos.", AchievementCategory.SPECIAL, {"login_streak": 30}),

    # --- HORARIOS Y EVENTOS ---
    AchievementDefinition("NIGHT_OWL", "Paralisis del sueño", "Juega entre las 3:00 AM y las 5:00 AM.", AchievementCategory.SPECIAL, {"play_at_night": 1}),
    AchievementDefinition("EARLY_BIRD", "A quien madruga...", "...Dios lo deja solo.", AchievementCategory.SPECIAL, {"play_at_dawn": 1}),

    # --- EXCLUSIVIDAD ---
    AchievementDefinition("FOUNDER", "Fundador del abismo", "Se uno de los primeros 100 jugadores en unirse al servidor.", AchievementCategory.SPECIAL, {"is_founder": 1}),

    # --- SESIONES EXTREMAS ---
    AchievementDefinition("SESSION_5H", "Perdida de nocion", "Juega durante 5 horas seguidas.", AchievementCategory.SPECIAL, {"session_time_seconds": 18000}),
    AchievementDefinition("SESSION_10H", "Esclavo del monitor", "Juega durante 10 horas seguidas.", AchievementCategory.SPECIAL, {"session_time_seconds": 36000}),
    AchievementDefinition("SESSION_24H", "Desconexion de la realidad", "Juega durante 24 horas seguidas.", AchievementCategory.SPECIAL, {"session_time_seconds": 86400}),

    # --- SUPERVIVENCIA Y DESGRACIA ---
    AchievementDefinition("TOTEM_1", "Casi...", "Utiliza un Totem de la Eternidad por primera vez.", AchievementCategory.SPECIAL, {"totem_used": 1}),
    AchievementDefinition("TOTEM_10", "Inmortal a base de trampas", "Utiliza 10 Totems de la Eternidad.", AchievementCategory.SPECIAL, {"totem_used": 10}),
    AchievementDefinition("RAID_1", "Heroe de mentira", "Completa una Invasion (Raid) con exito.", AchievementCategory.SPECIAL, {"raids_completed": 1}),
    AchievementDefinition("RAID_10", "Señor de la guerra", "Completa 10 Invasiones.", AchievementCategory.SPECIAL, {"raids_completed": 10}),

    # --- COMPORTAMIENTO META ---
    AchievementDefinition("AFK_1H", "Fantasma en la maquina", "Quedate AFK durante 1 hora seguida.", AchievementCategory.SPECIAL, {"afk_seconds": 3600}),
    AchievementDefinition("TRADER_10", "Estafado", "Realiza 10 intercambios con el Vendedor Ambulante.", AchievementCategory.SPECIAL, {"wandering_trader_trade": 10}),
    AchievementDefinition("MAINTENANCE_JOIN", "Ansiedad social", "Entra al servidor en los primeros 60 segundos tras un reinicio.", AchievementCategory.SPECIAL, {"join_after_restart": 1}),

    # --- CURIOSIDADES ---
    AchievementDefinition("DRAGON_EGG", "El fin justifica los medios", "Consigue el Huevo de Dragon.", AchievementCategory.SPECIAL, {"has_dragon_egg": 1}),
    AchievementDefinition("GOD_OF_WAR", "God of war", "Elimina a 1,000 entidades hostiles.", AchievementCategory.SPECIAL, {"hostile_kills": 1000}),
    AchievementDefinition("MOUNT_MASTER", "Montaras", "Recorre 10,000 bloques montado en un animal.", AchievementCategory.SPECIAL, {"distance_mounted": 10000}),
    AchievementDefinition("HUNGER_GAMES", "Los juegos del hambre", "Gana tu primer evento de supervivencia o torneo PVP.", AchievementCategory.SPECIAL, {"tournaments_won": 1}),
    AchievementDefinition("WHAT_NOW", "Y que hago con esto", "Consigue una Patata Venenosa.", AchievementCategory.SPECIAL, {"item_acquired:minecraft:poisonous_potato": 1}),
    AchievementDefinition("WTF_IS_THAT", "Que diablos es eso", "Encuentra una Oveja Rosa de forma natural.", AchievementCategory.SPECIAL, {"pink_sheep_found": 1}),
    AchievementDefinition("YOU_ARE_GOOD", "Ya sos bien", "Alcanza el nivel 100 de experiencia.", AchievementCategory.SPECIAL, {"xp_level": 100}),
    AchievementDefinition("EVEREST", "El monte everest no tiene nada malo contra de mi", "Alcanza la altura maxima del mundo (Y=320).", AchievementCategory.SPECIAL, {"max_height_reached": 1}),
    AchievementDefinition("FEAR_PARALYSIS", "Estaba paralizado con mucho miedo y no me podia mover", "Se afectado por el efecto de Oscuridad del Warden.", AchievementCategory.SPECIAL, {"warden_darkness_effect": 1}),

    # --- LOGROS OCULTOS Y ESPECÍFICOS ---
    AchievementDefinition("GHAST_RETURN", "Devolucion de cortesia", "Elimina a un Ghast devolviéndole su propia bola de fuego.", AchievementCategory.SPECIAL, {"ghast_fireball_kill": 1}),
    AchievementDefinition("CLUTCH_SURVIVAL", "Por un pelo", "Sobrevive a una caida de mas de 30 bloques con medio corazon de vida.", AchievementCategory.SPECIAL, {"clutch_survival": 1}),
    AchievementDefinition("NETHER_SLEEP", "Sueño explosivo", "Intenta dormir en una cama en el Nether.", AchievementCategory.SPECIAL, {"nether_bed_explosion": 1}),
    AchievementDefinition("STRIDER_TAXI", "Dj Zeguita", "Recorre 5,000 bloques montado en un Lavagante sobre lava.", AchievementCategory.SPECIAL, {"strider_lava_distance": 5000}),
    AchievementDefinition("MANY_EFFECTS", "Farmacia andante", "Ten 10 efectos de estado activos al mismo tiempo.", AchievementCategory.SPECIAL, {"active_effects_count": 10}),
    AchievementDefinition("SNIPER_DUEL", "Duelo a distancia", "Elimina a un Esqueleto con una flecha desde mas de 50 metros.", AchievementCategory.SPECIAL, {"skeleton_snipe_distance": 50}),
    AchievementDefinition("CACTUS_FAIL", "Darwin Award", "Muere por un cactus mientras llevas una armadura de Netherite completa.", AchievementCategory.SPECIAL, {"netherite_cactus_death": 1}),
    AchievementDefinition("VANDALISM", "Vandalismo artistico", "Rompe 50 pinturas (cuadros) de otros jugadores.", AchievementCategory.SPECIAL, {"paintings_broken": 50}),

    # --- MEMES Y CULTURA ---
    AchievementDefinition("MEME_BED_DRAGON", "Simplemente epico", "Elimina al Dragon del Fin usando una cama.", AchievementCategory.SPECIAL, {"dragon_killed_by_bed": 1}),
    AchievementDefinition("MEME_VOID_STARK", "No me quiero ir Sr. Stark", "Muere al caer al vacio con un inventario lleno.", AchievementCategory.SPECIAL, {"full_inventory_void_death": 1}),
    AchievementDefinition("MEME_HUMILDAD", "Humildad", "Regala un stack de diamantes (64) a otro jugador.", AchievementCategory.SPECIAL, {"diamonds_gifted": 64}),
    AchievementDefinition("MEME_ANTOJEN", "No antojen", "Sostén un Pastel en la mano frente a 5 jugadores.", AchievementCategory.SPECIAL, {"hold_cake_near_players": 1}),
    AchievementDefinition("join_on_anniversary", "Es hoy, es hoy", "Entra al servidor en el dia de tu cumpleaños o aniversario del server.", AchievementCategory.SPECIAL, {"join_on_anniversary": 1}),
    AchievementDefinition("MEME_POV_VILLAGER", "POV: Eres un aldeano", "Se atacado por un jugador mientras no llevas armadura.", AchievementCategory.SPECIAL, {"attacked_without_armor": 1}),
    AchievementDefinition("MEME_EL_PEPE", "El Pepe", "Cambia tu nombre de usuario por primera vez.", AchievementCategory.SPECIAL, {"name_changed": 1}),
    AchievementDefinition("MEME_SOLO_UN_CAPO", "Ya me quieres igualar", "Alcanza el nivel 50 de experiencia sin haber muerto nunca.", AchievementCategory.SPECIAL, {"lvl_50_no_death": 1}),
    AchievementDefinition("MEME_MI_MOMENTO", "Mi momento ha llegado", "Muere por una explosion de TNT provocada por ti mismo.", AchievementCategory.SPECIAL, {"self_tnt_death": 1}),
    
    # --- NUEVAS ADICIONES ---
    AchievementDefinition("MEME_POBRES", "ya comieron pobres?", "Consume un Filete (Steak) frente a otro jugador.", AchievementCategory.SPECIAL, {"eat_steak_near_player": 1}),
    AchievementDefinition("MEME_VIBORA", "si fuera una vibora ya te hubiera picado", "Encuentra tu primer Tesoro Enterrado.", AchievementCategory.SPECIAL, {"buried_treasure_found": 1}),
    AchievementDefinition("MEME_SUPER_POLLO", "un super?", "Ten un stack (64) de Pollo Cocinado en el inventario.", AchievementCategory.SPECIAL, {"cooked_chicken_stack": 1}),
    
    # --- EDGY & CULTURA DE INTERNET ---
    AchievementDefinition("MEME_SKILL_ISSUE", "Skill Issue", "Muere contra un Baby Zombie usando armadura de Netherite completa.", AchievementCategory.COMBAT, {"skill_issue_death": 1}),
    AchievementDefinition("MEME_NO_AFECTO", "Pov: No tienes afecto femenino", "Pica 1,000 bloques de Obsidiana.", AchievementCategory.MINING, {"mine_obsidian": 1000}),
    AchievementDefinition("MEME_TURBIO", "Turbio...", "Asesina a un Ajolote.", AchievementCategory.SPECIAL, {"kill_axolotl": 1}),
    AchievementDefinition("MEME_CHAMBA_PRO", "Pendejo no dura nada", "Rompe una herramienta de Netherite por exceso de uso.", AchievementCategory.SPECIAL, {"netherite_tool_broken": 1}),
    AchievementDefinition("MEME_CINE", "Porque el que graba no ayuda", "Presencia cómo un Creeper elimina a otra entidad.", AchievementCategory.SPECIAL, {"creeper_kill_witness": 1}),

    # --- LOGROS EXISTENCIALES ---
    AchievementDefinition("PHILO_GUILT", "Todo esto es tu culpa.", "Asesina a un aldeano inocente.", AchievementCategory.SPECIAL, {"kill_villager": 1}),
    AchievementDefinition("PHILO_PURPOSE", "¿Puedes siquiera recordar por qué viniste aquí?", "Alcanza las 50 horas de juego totales.", AchievementCategory.VETERAN, {"playtime_seconds": 180000}),
    AchievementDefinition("PHILO_WAKE", "Es hora de que despiertes.", "Regresa al servidor tras una semana de ausencia.", AchievementCategory.SPECIAL, {"return_after_7d": 1}),
    AchievementDefinition("PHILO_KILL_ENT", "Matar por entretenimiento es inofensivo.", "Elimina a 10,000 entidades totales.", AchievementCategory.COMBAT, {"total_kills": 10000}),
    AchievementDefinition("PHILO_NECESSARY", "No hay diferencia entre lo que está bien y lo que es necesario.", "Saquea un cofre de una aldea.", AchievementCategory.SPECIAL, {"loot_village_chest": 1}),
    AchievementDefinition("PHILO_NO_HOME", "No puedes volver a casa.", "Entra en la dimensión del Fin.", AchievementCategory.DIMENSIONS, {"enter_dimension:minecraft:the_end": 1}),
    AchievementDefinition("PHILO_GOD", "Mata a todos, y eres un dios.", "Elimina a 50,000 entidades totales.", AchievementCategory.COMBAT, {"total_kills": 50000}),
    AchievementDefinition("PHILO_WEAKNESS", "Este no es el momento para la debilidad.", "Elimina al Warden.", AchievementCategory.COMBAT, {"kill_warden": 1}),
    AchievementDefinition("PHILO_DAILY", "¿A cuántos mobs has matado hoy?", "Elimina a 500 mobs en una sola sesión.", AchievementCategory.COMBAT, {"session_kills": 500}),
    AchievementDefinition("PHILO_SLEEP", "¿Al menos duermes tranquilo?", "Duerme en una cama teniendo el efecto de Mal Presagio.", AchievementCategory.SPECIAL, {"sleep_with_bad_omen": 1}),

    # --- CITAS Y SARCASMO ---
    AchievementDefinition("MEME_WOLF", "El lobo no es un león, pero no actúa en el circo.", "Domestica a tu primer lobo.", AchievementCategory.SPECIAL, {"tame_wolf": 1}),
    AchievementDefinition("MEME_CROSS", "llevando mi cruz", "Muere teniendo un Tótem en el inventario (pero no en la mano).", AchievementCategory.SPECIAL, {"die_with_totem_in_inv": 1}),
    AchievementDefinition("MEME_TNT_CRAFT", "no debi inventar el", "Fabrica tu primer bloque de TNT.", AchievementCategory.SPECIAL, {"craft_tnt": 1}),
    AchievementDefinition("MEME_TRIPLE_THREAT", "Hay tres cosas que salen siempre", "Muere rodeado por un creeper, un zombie y un esqueleto.", AchievementCategory.SPECIAL, {"triple_threat_death": 1}),
    AchievementDefinition("MEME_FIRST_NIGHT", "He pasado una noche estupenda, pero no ha sido ésta.", "Sobrevive tu primera noche en el mundo.", AchievementCategory.SPECIAL, {"survive_first_night": 1}),
    AchievementDefinition("MEME_TWO_BRAINS", "Si los seres humanos tuviésemos dos cerebros...", "Muere por tus propios medios (caída o fuego).", AchievementCategory.SPECIAL, {"self_death": 1}),
    AchievementDefinition("GAIN_FIRST_XP", "La experiencia es algo maravilloso.", "Gana tus primeros puntos de experiencia.", AchievementCategory.SPECIAL, {"gain_first_xp": 1}),
    AchievementDefinition("DIST_1", "Trotamundos", "Has recorrido 10,000 bloques a pie.", AchievementCategory.SPECIAL, {"distance_travelled": 10000}),
    AchievementDefinition("DIST_2", "Explorador Legendario", "Has recorrido 100,000 bloques. ¡El mundo no tiene secretos para ti!", AchievementCategory.SPECIAL, {"distance_travelled": 100000}),
    AchievementDefinition("TIME_1", "Habitante Local", "Has jugado un total de 10 horas.", AchievementCategory.SPECIAL, {"playtime_seconds": 36000}),
    AchievementDefinition("TIME_3", "Veterano del Servidor", "Has jugado un total de 100 horas. ¡Eres parte de la historia!", AchievementCategory.SPECIAL, {"playtime_seconds": 360000}),
    AchievementDefinition("PHILO_PURPOSE_NEW", "Propósito Filosófico", "Has pasado 50 horas en el servidor. ¿Qué buscas realmente?", AchievementCategory.SPECIAL, {"playtime_seconds": 180000}),
    AchievementDefinition("MEME_FIRST_DEATH", "No es que tenga miedo a morirme...", "Muere por primera vez.", AchievementCategory.SPECIAL, {"first_death": 1}),
    AchievementDefinition("MEME_DOG_LOVER", "¿Sabes qué me gusta de las personas? Sus perros.", "Ten 5 lobos domesticados al mismo tiempo.", AchievementCategory.SPECIAL, {"tame_5_dogs": 1}),
    AchievementDefinition("MEME_MEMORY", "No guardo rencor, pero tengo buena memoria.", "Sé eliminado por otro jugador.", AchievementCategory.SOCIAL, {"killed_by_player": 1}),
    AchievementDefinition("MEME_STAB_FRONT", "Los amigos de verdad te apuñalan de frente.", "Sé eliminado 10 veces por otros jugadores.", AchievementCategory.SOCIAL, {"killed_by_player_10": 1}),
    AchievementDefinition("MEME_REVENGE", "Espera de mí, lo que recibo de ti.", "Elimina al jugador que te mató por última vez.", AchievementCategory.SOCIAL, {"revenge_kill": 1}),

    # --- ACTITUD Y DESAFÍO ---
    AchievementDefinition("MEME_GG", "GG", "Escribe 'GG' tras eliminar a un jefe (Boss).", AchievementCategory.SPECIAL, {"gg_after_boss": 1}),
    AchievementDefinition("MEME_ALL_AGAINST_ME", "Todos contra yo solo", "Muere tras ser atacado por 3 o más jugadores a la vez.", AchievementCategory.SOCIAL, {"died_to_team": 1}),
    AchievementDefinition("MEME_ONLY_A_GAME", "solo es un juego.....", "Muere teniendo nivel 100 o más de experiencia.", AchievementCategory.SPECIAL, {"die_with_100_lvl": 1}),
    AchievementDefinition("MEME_TRY_AGAIN", "hazlo otra vez, a lo mejor esta vez sí", "Muere por la misma causa 3 veces seguidas en 5 minutos.", AchievementCategory.SPECIAL, {"repeat_death_streak": 1}),
    AchievementDefinition("playtime_seconds", "¿Puedes siquiera recordar por qué viniste aquí?", "Alcanza las primeras horas de juego totales.", AchievementCategory.VETERAN, {"playtime_seconds": 1}),
    AchievementDefinition("distance_travelled", "Nómada del Abismo", "Has recorrido tus primeros kilómetros en este mundo.", AchievementCategory.EXPLORATION, {"distance_travelled": 1}),
    AchievementDefinition("MEME_NO_EGGS", "no hay huevos", "Ataca al Warden con tus propias manos.", AchievementCategory.SPECIAL, {"punch_warden": 1}),
]
