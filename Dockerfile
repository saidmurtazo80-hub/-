FROM python:3.11-slim

RUN apt-get update && apt-get install -y \
    ffmpeg \
    && apt-get clean

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV TEMP_DIR=/tmp/tg_media_bot
ENV PYTHONUNBUFFERED=1

CMD ["python", "-u", "bot.py"]
