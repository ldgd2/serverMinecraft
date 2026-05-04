from ..base import AchievementDefinition, AchievementCategory

ENCHANTING_ACHIEVEMENTS = [
    # --- VOLUMEN GENERAL ---
    AchievementDefinition("ENCH_GEN_1", "Corrupcion inicial", "Encanta tu primer objeto.", AchievementCategory.ENCHANTING, {"item_enchanted": 1}, rarity=0.07),
    AchievementDefinition("ENCH_GEN_10", "Secta de la magia", "Encanta 10 objetos.", AchievementCategory.ENCHANTING, {"item_enchanted": 10}, rarity=0.12),
    AchievementDefinition("ENCH_GEN_50", "Obsesion mistica", "Encanta 50 objetos.", AchievementCategory.ENCHANTING, {"item_enchanted": 50}, rarity=0.09),
    AchievementDefinition("ENCH_GEN_100", "Maestro de las sombras", "Encanta 100 objetos.", AchievementCategory.ENCHANTING, {"item_enchanted": 100}, rarity=0.38),
    AchievementDefinition("ENCH_GEN_500", "Aniquilador de la pureza", "Encanta 500 objetos.", AchievementCategory.ENCHANTING, {"item_enchanted": 500}, rarity=0.37),

    # --- PODER Y SACRIFICIO (XP) ---
    AchievementDefinition("ENCH_LVL_30", "Poder prohibido", "Realiza un encantamiento de nivel 30.", AchievementCategory.ENCHANTING, {"level_30_enchant": 1}, rarity=0.09),
    AchievementDefinition("ENCH_LVL_30_X10", "Aura oscura", "Realiza 10 encantamientos de nivel 30.", AchievementCategory.ENCHANTING, {"level_30_enchant": 10}, rarity=0.12),
    AchievementDefinition("ENCH_XP_1000", "Sacrificio vital", "Gasta 1,000 niveles en la mesa de encantamientos.", AchievementCategory.ENCHANTING, {"xp_spent_enchanting": 1000}, rarity=0.63),
    AchievementDefinition("ENCH_XP_5000", "Nigromancia material", "Gasta 5,000 niveles en la mesa de encantamientos.", AchievementCategory.ENCHANTING, {"xp_spent_enchanting": 5000}, rarity=0.67),

    # --- ESPECIALIDADES (FILOS Y PROTECCIÓN) ---
    AchievementDefinition("ENCH_SHARP_5", "Filo del abismo", "Consigue el encantamiento Filo V.", AchievementCategory.ENCHANTING, {"enchant:sharpness:5": 1}, rarity=0.06),
    AchievementDefinition("ENCH_PROT_4", "Blindaje del alma", "Consigue el encantamiento Proteccion IV.", AchievementCategory.ENCHANTING, {"enchant:protection:4": 1}, rarity=0.13),
    AchievementDefinition("ENCH_FIRE_2", "Pira funeraria", "Consigue el encantamiento Aspecto Igneo II.", AchievementCategory.ENCHANTING, {"enchant:fire_aspect:2": 1}, rarity=0.05),
    AchievementDefinition("ENCH_KNOCK_2", "Repulsion social", "Consigue el encantamiento Empuje II.", AchievementCategory.ENCHANTING, {"enchant:knockback:2": 1}, rarity=0.09),

    # --- UTILIDAD Y CODICIA ---
    AchievementDefinition("ENCH_FORT_3", "Codicia suprema", "Consigue el encantamiento Fortuna III.", AchievementCategory.ENCHANTING, {"enchant:fortune:3": 1}, rarity=0.07),
    AchievementDefinition("ENCH_EFF_5", "Rapidez febril", "Consigue el encantamiento Eficiencia V.", AchievementCategory.ENCHANTING, {"enchant:efficiency:5": 1}, rarity=0.10),
    AchievementDefinition("ENCH_SILK", "Tacto de seda muerta", "Consigue el encantamiento Toque de Seda.", AchievementCategory.ENCHANTING, {"enchant:silk_touch": 1}, rarity=0.14),
    AchievementDefinition("ENCH_LOOT_3", "Saqueador de cadaveres", "Consigue el encantamiento Saqueo III.", AchievementCategory.ENCHANTING, {"enchant:looting:3": 1}, rarity=0.13),

    # --- ETERNIDAD Y REPARACIÓN ---
    AchievementDefinition("ENCH_MEND", "Parasito de experiencia", "Consigue el encantamiento Reparacion.", AchievementCategory.ENCHANTING, {"enchant:mending": 1}, rarity=0.06),
    AchievementDefinition("ENCH_UNB_3", "Eternidad artificial", "Consigue el encantamiento Irrompibilidad III.", AchievementCategory.ENCHANTING, {"enchant:unbreaking:3": 1}, rarity=0.13),

    # --- MALDICIONES Y CORRUPCIÓN REAL ---
    AchievementDefinition("ENCH_CURSE_BIND", "Maldicion eterna", "Aplica un encantamiento de Maldicion de Ligamiento.", AchievementCategory.ENCHANTING, {"enchant:binding_curse": 1}, rarity=0.06),
    AchievementDefinition("ENCH_CURSE_VANISH", "Desvanecimiento existencial", "Aplica un encantamiento de Maldicion de Desaparicion.", AchievementCategory.ENCHANTING, {"enchant:vanishing_curse": 1}, rarity=0.13),

    # --- ARMAMENTO ESPECIALIZADO ---
    AchievementDefinition("ENCH_TRI_RIP", "Tormenta de sangre", "Encanta un Tridente con Propulsion III.", AchievementCategory.ENCHANTING, {"enchant:riptide:3": 1}, rarity=0.10),
    AchievementDefinition("ENCH_TRI_CHAN", "Rayo castigador", "Encanta un Tridente con Canalizacion.", AchievementCategory.ENCHANTING, {"enchant:channeling": 1}, rarity=0.11),
    AchievementDefinition("ENCH_CROSS_MULTI", "Balistica infernal", "Encanta una Ballesta con Multidisparo.", AchievementCategory.ENCHANTING, {"enchant:multishot": 1}, rarity=0.10),
    AchievementDefinition("ENCH_CROSS_PIER", "Penetracion total", "Encanta una Ballesta con Perforacion IV.", AchievementCategory.ENCHANTING, {"enchant:piercing:4": 1}, rarity=0.09),

    # --- FORJA Y PURIFICACIÓN ---
    AchievementDefinition("ENCH_ANVIL_USE", "Forja de almas", "Combina objetos en el yunque 50 veces.", AchievementCategory.ENCHANTING, {"anvil_use": 50}, rarity=0.07),
    AchievementDefinition("ENCH_GRIND_USE", "Purificacion violenta", "Elimina encantamientos en la piedra de afilar 25 veces.", AchievementCategory.ENCHANTING, {"grindstone_use": 25}, rarity=0.06),
    AchievementDefinition("ENCH_MAXED_TOOL", "Perfeccion pecaminosa", "Aplica 7 o mas encantamientos a una sola herramienta.", AchievementCategory.ENCHANTING, {"maxed_item_enchanted": 1}, rarity=0.14),

    # --- ARCOS Y BALÍSTICA ---
    AchievementDefinition("ENCH_BOW_POW_5", "Ojo de la muerte", "Encanta un Arco con Poder V.", AchievementCategory.ENCHANTING, {"enchant:power:5": 1}, rarity=0.11),
    AchievementDefinition("ENCH_BOW_PUN_2", "Impacto violento", "Encanta un Arco con Retroceso II.", AchievementCategory.ENCHANTING, {"enchant:punch:2": 1}, rarity=0.13),
    AchievementDefinition("ENCH_BOW_FLAME", "Fuego eterno", "Encanta un Arco con Fuego.", AchievementCategory.ENCHANTING, {"enchant:flame": 1}, rarity=0.05),
    AchievementDefinition("ENCH_BOW_INF", "Municion infinita", "Encanta un Arco con Infinidad.", AchievementCategory.ENCHANTING, {"enchant:infinity": 1}, rarity=0.14),

    # --- ARMADURA ESPECIALIZADA ---
    AchievementDefinition("ENCH_ARM_THORN_3", "Venganza espinosa", "Encanta una pieza de armadura con Espinas III.", AchievementCategory.ENCHANTING, {"enchant:thorns:3": 1}, rarity=0.09),
    AchievementDefinition("ENCH_HELM_RESP_3", "Pulmones de acero", "Encanta un Casco con Respiracion III.", AchievementCategory.ENCHANTING, {"enchant:respiration:3": 1}, rarity=0.09),
    AchievementDefinition("ENCH_HELM_AQUA", "Vision acuatica", "Encanta un Casco con Afinidad Acuatica.", AchievementCategory.ENCHANTING, {"enchant:aqua_affinity": 1}, rarity=0.13),
    AchievementDefinition("ENCH_BOOT_FEATH_4", "Caida de pluma", "Encanta unas Botas con Caida de Pluma IV.", AchievementCategory.ENCHANTING, {"enchant:feather_falling:4": 1}, rarity=0.05),
    AchievementDefinition("ENCH_BOOT_DEPTH_3", "Paso de Poseidon", "Encanta unas Botas con Agilidad Acuatica III.", AchievementCategory.ENCHANTING, {"enchant:depth_strider:3": 1}, rarity=0.09),
    AchievementDefinition("ENCH_BOOT_FROST_2", "Caminante de hielo", "Encanta unas Botas con Paso Helado II.", AchievementCategory.ENCHANTING, {"enchant:frost_walker:2": 1}, rarity=0.13),
    AchievementDefinition("ENCH_BOOT_SOUL_3", "Velocidad de almas", "Encanta unas Botas con Velocidad de Almas III.", AchievementCategory.ENCHANTING, {"enchant:soul_speed:3": 1}, rarity=0.08),
    AchievementDefinition("ENCH_SWIFT_3", "Sombra silenciosa", "Encanta unas Pantalones con Sigilo Veloz III.", AchievementCategory.ENCHANTING, {"enchant:swift_sneak:3": 1}, rarity=0.06),

    # --- ESPADAS Y HERRAMIENTAS ADICIONALES ---
    AchievementDefinition("ENCH_SWORD_SMITE_5", "Exorcista", "Encanta una Espada con Castigo V.", AchievementCategory.ENCHANTING, {"enchant:smite:5": 1}, rarity=0.11),
    AchievementDefinition("ENCH_SWORD_BANE_5", "Pesticida", "Encanta una Espada con Perdicion de los Artropodos V.", AchievementCategory.ENCHANTING, {"enchant:bane_of_arthropods:5": 1}, rarity=0.14),
    AchievementDefinition("ENCH_SWORD_SWEEP_3", "Corte circular", "Encanta una Espada con Filo Arrasador III.", AchievementCategory.ENCHANTING, {"enchant:sweeping:3": 1}, rarity=0.13),

    # --- PESCA Y LIBROS ---
    AchievementDefinition("ENCH_FISH_LUCK_3", "Suerte del abismo", "Encanta una Caña con Suerte Marina III.", AchievementCategory.ENCHANTING, {"enchant:luck_of_the_sea:3": 1}, rarity=0.08),
    AchievementDefinition("ENCH_FISH_LURE_3", "Atraccion fatal", "Encanta una Caña con Atraccion III.", AchievementCategory.ENCHANTING, {"enchant:lure:3": 1}, rarity=0.10),
    AchievementDefinition("ENCH_BOOK_COLLECTOR", "Biblia de las sombras", "Encanta 50 libros en la mesa de encantamientos.", AchievementCategory.ENCHANTING, {"enchant:book": 50}, rarity=0.07),
]
