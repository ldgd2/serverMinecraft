from ..base import AchievementDefinition, AchievementCategory

SOCIAL_ACHIEVEMENTS = [
    AchievementDefinition("CHAT_0", "inbox (solo para conocedores)", "Envía tu primer mensaje.", AchievementCategory.SOCIAL, {"chat_message": 1}),
    AchievementDefinition("CHAT_1", "y esa jaireada", "Envía 50 mensajes.", AchievementCategory.SOCIAL, {"chat_message": 50}),
    AchievementDefinition("CHAT_2", "te naneaste", "Envía 250 mensajes.", AchievementCategory.SOCIAL, {"chat_message": 250}),
    AchievementDefinition("CHAT_3", "no leo lloros", "Envía 1,000 mensajes.", AchievementCategory.SOCIAL, {"chat_message": 1000}),
    AchievementDefinition("CHAT_4", "Skibidi", "Envía 5,000 mensajes.", AchievementCategory.SOCIAL, {"chat_message": 5000}),
]
