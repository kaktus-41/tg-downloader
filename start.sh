#!/bin/bash
# Запускаем локальный Bot API сервер
telegram-bot-api \
  --api-id=$API_ID \
  --api-hash=$API_HASH \
  --local \
  --dir=/tmp/telegram-bot-api \
  --port=8081 &

# Ждём пока сервер запустится
sleep 5

# Запускаем бота
python3 bot.py
