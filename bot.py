#!/usr/bin/env python3
"""
Telegram Media Downloader Bot
Supports: TikTok, YouTube, Instagram, Twitter/X
Downloads: Video, Photo, Audio (music) separately
"""

import os
import asyncio
import logging
from pathlib import Path

from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, FSInputFile
from aiogram.filters import CommandStart, Command
from aiogram.fsm.storage.memory import MemoryStorage

from downloader import MediaDownloader
from config import BOT_TOKEN, TEMP_DIR

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger(__name__)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())
downloader = MediaDownloader()

# ── helpers ──────────────────────────────────────────────────────────────────

def detect_platform(url: str) -> str | None:
    url = url.lower()
    if "tiktok.com" in url or "vm.tiktok.com" in url:
        return "tiktok"
    if "youtube.com" in url or "youtu.be" in url:
        return "youtube"
    if "instagram.com" in url:
        return "instagram"
    if "twitter.com" in url or "x.com" in url or "t.co" in url:
        return "twitter"
    return None

PLATFORM_EMOJI = {
    "tiktok": "🎵",
    "youtube": "▶️",
    "instagram": "📸",
    "twitter": "🐦",
}

def build_menu(url: str, platform: str) -> InlineKeyboardMarkup:
    emoji = PLATFORM_EMOJI.get(platform, "🌐")
    rows = [
        [InlineKeyboardButton(text=f"🎬 Скачать видео", callback_data=f"dl:video:{url}")],
        [InlineKeyboardButton(text=f"🖼 Скачать фото / превью", callback_data=f"dl:photo:{url}")],
        [InlineKeyboardButton(text=f"🎵 Скачать музыку / аудио", callback_data=f"dl:audio:{url}")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=rows)

async def cleanup(paths: list[str]):
    for p in paths:
        try:
            if p and os.path.exists(p):
                os.remove(p)
        except Exception:
            pass

# ── handlers ─────────────────────────────────────────────────────────────────

@dp.message(CommandStart())
async def cmd_start(msg: Message):
    text = (
        "👋 <b>Привет! Я бот для скачивания медиа.</b>\n\n"
        "Поддерживаемые платформы:\n"
        "🎵 TikTok  |  ▶️ YouTube  |  📸 Instagram  |  🐦 Twitter/X\n\n"
        "📌 <b>Просто отправь мне ссылку</b> — и я предложу:\n"
        "• 🎬 Видео\n"
        "• 🖼 Фото / превью\n"
        "• 🎵 Только музыку / аудио\n\n"
        "Всё скачивается <b>отдельно</b>, без лишнего!"
    )
    await msg.answer(text, parse_mode="HTML")

@dp.message(Command("help"))
async def cmd_help(msg: Message):
    await cmd_start(msg)

@dp.message(F.text)
async def handle_url(msg: Message):
    url = msg.text.strip()
    platform = detect_platform(url)
    if not platform:
        await msg.answer(
            "❌ Ссылка не распознана.\n\n"
            "Поддерживаются: TikTok, YouTube, Instagram, Twitter/X\n"
            "Отправь просто ссылку, без лишнего текста."
        )
        return

    emoji = PLATFORM_EMOJI[platform]
    await msg.answer(
        f"{emoji} Платформа: <b>{platform.capitalize()}</b>\n\nЧто скачать?",
        parse_mode="HTML",
        reply_markup=build_menu(url, platform),
    )

@dp.callback_query(F.data.startswith("dl:"))
async def handle_download(cb: CallbackQuery):
    _, media_type, url = cb.data.split(":", 2)
    platform = detect_platform(url)

    type_labels = {"video": "видео 🎬", "photo": "фото 🖼", "audio": "аудио 🎵"}
    label = type_labels.get(media_type, media_type)

    status = await cb.message.answer(f"⏳ Скачиваю {label}…\nЭто может занять несколько секунд.")
    await cb.answer()

    try:
        result = await downloader.download(url, media_type, platform)

        if not result or not result.get("files"):
            await status.edit_text("❌ Не удалось скачать. Возможно, контент недоступен или приватный.")
            return

        files = result["files"]
        title = result.get("title", "")
        caption = f"<b>{title}</b>\n🔗 {platform.capitalize()}" if title else f"🔗 {platform.capitalize()}"

        for fpath in files:
            if not os.path.exists(fpath):
                continue
            fsize = os.path.getsize(fpath)
            if fsize > 50 * 1024 * 1024:  # > 50 MB
                await cb.message.answer(
                    f"⚠️ Файл слишком большой ({fsize // 1024 // 1024} МБ) для отправки через Telegram.\n"
                    "Telegram позволяет максимум 50 МБ."
                )
                continue

            fsf = FSInputFile(fpath)
            ext = Path(fpath).suffix.lower()

            if ext in (".mp4", ".mov", ".webm", ".mkv"):
                await cb.message.answer_video(fsf, caption=caption, parse_mode="HTML")
            elif ext in (".mp3", ".m4a", ".ogg", ".wav", ".opus"):
                await cb.message.answer_audio(fsf, caption=caption, parse_mode="HTML")
            elif ext in (".jpg", ".jpeg", ".png", ".webp"):
                await cb.message.answer_photo(fsf, caption=caption, parse_mode="HTML")
            else:
                await cb.message.answer_document(fsf, caption=caption, parse_mode="HTML")

        await status.delete()
        await cleanup(files)

    except Exception as e:
        logger.exception("Download error")
        await status.edit_text(f"❌ Ошибка: {e}\n\nПопробуй другую ссылку или повтори позже.")

# ── entry point ───────────────────────────────────────────────────────────────

async def main():
    Path(TEMP_DIR).mkdir(parents=True, exist_ok=True)
    logger.info("Bot started")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
