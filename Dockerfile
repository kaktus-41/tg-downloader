FROM python:3.11-slim

WORKDIR /app

# Устанавливаем зависимости
RUN apt-get update && apt-get install -y \
    ffmpeg \
    wget \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Скачиваем локальный Telegram Bot API сервер
RUN wget -q https://github.com/tdlib/telegram-bot-api/releases/download/v7.3/telegram-bot-api-aarch64-linux-gnu.tar.gz \
    -O /tmp/tgapi.tar.gz || \
    wget -q https://github.com/tdlib/telegram-bot-api/releases/download/v7.3/telegram-bot-api-x86_64-linux-gnu.tar.gz \
    -O /tmp/tgapi.tar.gz && \
    tar -xzf /tmp/tgapi.tar.gz -C /usr/local/bin/ && \
    chmod +x /usr/local/bin/telegram-bot-api && \
    rm /tmp/tgapi.tar.gz

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["sh", "start.sh"]
