FROM python:3.11-slim

# Install ffmpeg (required by yt-dlp for audio extraction & merging)
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV TEMP_DIR=/tmp/tg_media_bot

CMD ["python", "bot.py"]
