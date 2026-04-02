"""
Media downloader using yt-dlp.
Handles: TikTok, YouTube, Instagram, Twitter/X
Modes: video, photo (thumbnail/images), audio
"""

import os
import uuid
import asyncio
import logging
from pathlib import Path
from typing import Optional

import yt_dlp

from config import TEMP_DIR, COOKIES_FILE

logger = logging.getLogger(__name__)


class MediaDownloader:
    def __init__(self):
        self.temp_dir = TEMP_DIR

    # ── public API ───────────────────────────────────────────────────────────

    async def download(self, url: str, media_type: str, platform: str) -> dict:
        """
        media_type: 'video' | 'photo' | 'audio'
        Returns: {"files": [path, ...], "title": str}
        """
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None, self._download_sync, url, media_type, platform
        )

    # ── internal ─────────────────────────────────────────────────────────────

    def _base_opts(self, out_template: str) -> dict:
        opts = {
            "outtmpl": out_template,
            "quiet": True,
            "no_warnings": True,
            "noplaylist": True,
            "socket_timeout": 30,
            "retries": 3,
        }
        if COOKIES_FILE and os.path.exists(COOKIES_FILE):
            opts["cookiefile"] = COOKIES_FILE
        return opts

    def _uid(self) -> str:
        return uuid.uuid4().hex[:12]

    def _download_sync(self, url: str, media_type: str, platform: str) -> dict:
        uid = self._uid()
        out_dir = Path(self.temp_dir) / uid
        out_dir.mkdir(parents=True, exist_ok=True)

        try:
            if media_type == "audio":
                return self._dl_audio(url, out_dir, uid)
            elif media_type == "photo":
                return self._dl_photo(url, out_dir, uid, platform)
            else:  # video (default)
                return self._dl_video(url, out_dir, uid, platform)
        except Exception as e:
            logger.exception("Download failed")
            raise RuntimeError(str(e))

    # ── VIDEO ────────────────────────────────────────────────────────────────

    def _dl_video(self, url: str, out_dir: Path, uid: str, platform: str) -> dict:
        template = str(out_dir / f"{uid}_video.%(ext)s")

        ydl_opts = self._base_opts(template)
        ydl_opts.update({
            # Best mp4 up to 1080p; fallback to best available
            "format": "bestvideo[ext=mp4][height<=1080]+bestaudio[ext=m4a]/best[ext=mp4][height<=1080]/best",
            "merge_output_format": "mp4",
        })

        # TikTok: prefer no-watermark format when available
        if platform == "tiktok":
            ydl_opts["format"] = (
                "bestvideo[format_note*=no watermark][ext=mp4]+bestaudio/"
                "bestvideo[ext=mp4]+bestaudio/best[ext=mp4]/best"
            )

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            title = info.get("title", "")

        files = sorted(out_dir.glob(f"{uid}_video.*"))
        return {"files": [str(f) for f in files], "title": title}

    # ── PHOTO / THUMBNAIL ────────────────────────────────────────────────────

    def _dl_photo(self, url: str, out_dir: Path, uid: str, platform: str) -> dict:
        """
        For photo-only posts (Instagram carousel, Twitter images) — download images.
        For video posts — download thumbnail/cover.
        """
        template = str(out_dir / f"{uid}_photo.%(ext)s")
        ydl_opts = self._base_opts(template)

        # Try write_all_thumbnails to grab cover art / thumbnails
        ydl_opts.update({
            "skip_download": True,
            "write_thumbnail": True,
            "write_all_thumbnails": True,
            "writethumbnail": True,
        })

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            title = info.get("title", "")

            # Check if it's an image post (no video stream)
            entries = info.get("entries") or [info]
            is_image_post = all(
                not e.get("url", "").endswith((".mp4", ".webm", ".mov"))
                and e.get("ext") in ("jpg", "jpeg", "png", "webp", None)
                for e in entries
            )

        if is_image_post:
            # Re-download as actual image files
            img_template = str(out_dir / f"{uid}_img_%(autonumber)s.%(ext)s")
            img_opts = self._base_opts(img_template)
            img_opts.update({
                "format": "best",
                "merge_output_format": None,
            })
            with yt_dlp.YoutubeDL(img_opts) as ydl:
                ydl.download([url])

        # Collect all image files produced
        exts = {".jpg", ".jpeg", ".png", ".webp"}
        files = [f for f in out_dir.iterdir() if f.suffix.lower() in exts]
        files.sort()

        if not files:
            # Fallback: download thumbnail via requests
            thumb_url = None
            with yt_dlp.YoutubeDL({"quiet": True}) as ydl:
                info2 = ydl.extract_info(url, download=False)
                thumb_url = info2.get("thumbnail")

            if thumb_url:
                import urllib.request
                thumb_path = out_dir / f"{uid}_thumb.jpg"
                urllib.request.urlretrieve(thumb_url, thumb_path)
                files = [thumb_path]

        return {"files": [str(f) for f in files], "title": title}

    # ── AUDIO ────────────────────────────────────────────────────────────────

    def _dl_audio(self, url: str, out_dir: Path, uid: str) -> dict:
        template = str(out_dir / f"{uid}_audio.%(ext)s")
        ydl_opts = self._base_opts(template)
        ydl_opts.update({
            "format": "bestaudio/best",
            "postprocessors": [
                {
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "mp3",
                    "preferredquality": "192",
                }
            ],
            # Embed thumbnail as cover art
            "writethumbnail": False,
            "embedthumbnail": False,
        })

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            title = info.get("title", "")

        files = sorted(out_dir.glob(f"{uid}_audio.*"))
        return {"files": [str(f) for f in files], "title": title}
