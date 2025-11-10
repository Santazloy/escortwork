#!/bin/bash

# Production startup script для Render
# Запускает веб-сервер и balance bot одновременно

echo "🚀 Starting Escortwork Production Services..."

# Запускаем balance bot в фоне
echo "📊 Starting Balance Bot..."
python3 balance_bot.py &
BALANCE_BOT_PID=$!
echo "✅ Balance bot started with PID: $BALANCE_BOT_PID"

# Небольшая пауза для инициализации бота
sleep 2

# Запускаем веб-сервер (он будет на переднем плане)
echo "🌐 Starting Web Server..."
gunicorn server:app --bind 0.0.0.0:$PORT --workers 2 --timeout 120

# Если веб-сервер упал, останавливаем balance bot
echo "⚠️ Web server stopped, stopping balance bot..."
kill $BALANCE_BOT_PID 2>/dev/null