# 📥 Telegram Media Downloader Bot

Скачивает видео, фото и музыку (аудио) **отдельно** из:
- 🎵 TikTok
- ▶️ YouTube
- 📸 Instagram
- 🐦 Twitter / X

---

## ⚙️ Быстрый старт

### 1. Получи токен бота
1. Открой [@BotFather](https://t.me/BotFather) в Telegram
2. Отправь `/newbot` и следуй инструкциям
3. Скопируй токен вида `123456789:ABCdef...`

---

### 2. Запуск без Docker (локально)

**Требования:** Python 3.10+, ffmpeg

```bash
# Установи ffmpeg (Ubuntu/Debian)
sudo apt install ffmpeg

# Установи ffmpeg (macOS)
brew install ffmpeg

# Клонируй / скачай файлы бота
cd tg_downloader_bot

# Установи зависимости
pip install -r requirements.txt

# Задай токен
export BOT_TOKEN="123456789:ВАШ_ТОКЕН"

# Запусти
python bot.py
```

---

### 3. Запуск через Docker (рекомендуется)

```bash
cd tg_downloader_bot

# Создай файл .env
echo "BOT_TOKEN=123456789:ВАШ_ТОКЕН" > .env

# Собери и запусти
docker-compose up -d --build

# Смотри логи
docker-compose logs -f
```

---

## 🔧 Файл config.py

```python
BOT_TOKEN = os.getenv("BOT_TOKEN", "YOUR_BOT_TOKEN_HERE")
TEMP_DIR  = os.getenv("TEMP_DIR", "/tmp/tg_media_bot")
COOKIES_FILE = os.getenv("COOKIES_FILE", "")
```

Можно задать токен прямо в `config.py` или через переменную окружения.

---

## 🍪 Куки (для Instagram и закрытых аккаунтов)

Для скачивания с Instagram или закрытых TikTok-аккаунтов нужны куки:

1. Установи расширение [Get cookies.txt LOCALLY](https://chrome.google.com/webstore/detail/get-cookiestxt-locally/cclelndahbckbenkjhflpdbgdldlbecc)
2. Зайди на сайт (instagram.com / tiktok.com)
3. Экспортируй куки → `cookies.txt`
4. Положи файл рядом с `bot.py`
5. В `config.py` или `.env` задай: `COOKIES_FILE=cookies.txt`

---

## 📋 Как работает бот

```
Пользователь отправляет ссылку
        ↓
Бот определяет платформу
        ↓
Показывает кнопки:
  [🎬 Скачать видео]
  [🖼 Скачать фото / превью]
  [🎵 Скачать музыку / аудио]
        ↓
Скачивает нужный файл через yt-dlp + ffmpeg
        ↓
Отправляет файл в Telegram
        ↓
Удаляет временные файлы
```

---

## 📁 Структура проекта

```
tg_downloader_bot/
├── bot.py           # Основной файл бота (aiogram 3)
├── downloader.py    # Логика скачивания (yt-dlp)
├── config.py        # Конфигурация
├── requirements.txt # Зависимости Python
├── Dockerfile       # Docker образ
├── docker-compose.yml
└── README.md
```

---

## ⚠️ Ограничения Telegram

- Максимальный размер файла: **50 МБ** (через Bot API)
- Для файлов > 50 МБ бот выдаст предупреждение
- YouTube видео в высоком качестве могут превышать лимит

---

## 🛠 Зависимости

| Пакет | Назначение |
|-------|-----------|
| `aiogram` 3.x | Telegram Bot framework |
| `yt-dlp` | Скачивание медиа с 1000+ сайтов |
| `ffmpeg` | Конвертация аудио, склейка видео+аудио |

---

## 📝 Лицензия

MIT — используй свободно.
