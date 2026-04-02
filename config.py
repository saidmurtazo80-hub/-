import os

# ── Обязательно: вставь свой токен бота от @BotFather ─────────────────────
BOT_TOKEN = os.getenv("BOT_TOKEN", "8760555909:AAE6ORjq4gBLYgiyypNhae3hDFjg65IzC44")

# Папка для временных файлов (создаётся автоматически)
TEMP_DIR = os.getenv("TEMP_DIR", "/tmp/tg_media_bot")

# Куки для Instagram/TikTok (опционально, для приватного контента)
# Путь к файлу cookies.txt в формате Netscape
COOKIES_FILE = os.getenv("COOKIES_FILE", "")  # например: "cookies.txt"
