"""Настройки приложения"""

# VK API настройки
VK_APP_ID = 6287487
VK_REDIRECT_URI = "https://oauth.vk.com/blank.html"
VK_API_VERSION = "5.131"
VK_SCOPE = "audio,offline"

# Настройки плеера
MAX_TRACKS_TO_LOAD = 2000
TRACKS_PER_REQUEST = 200
RECOMMENDATIONS_COUNT = 100

# Настройки UI
WINDOW_WIDTH = 1000
WINDOW_HEIGHT = 700
VOLUME_DEFAULT = 70

# Пути
TOKEN_FILE = "vk_token.json"
LOG_FILE = "vk_music_player.log"

# Режим отладки
DEBUG_MODE = True
