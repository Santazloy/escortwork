#!/bin/bash
set -euo pipefail

echo "🚀 Starting Escortwork Production Services..."

# ===== конфиг =====
WORKERS=${WORKERS:-2}
TIMEOUT=${TIMEOUT:-120}
BIND_ADDR="0.0.0.0:${PORT:-10000}"

# Логи
mkdir -p logs
BOT_LOG="logs/balance_bot.log"
WEB_LOG="logs/web.log"

# Аккуратное завершение
terminate() {
  echo "🛑 Stopping services..."
  pkill -P $$ || true
  exit 0
}
trap terminate SIGTERM SIGINT

echo "📊 Starting Balance Bot..."
python3 balance_bot.py >>"$BOT_LOG" 2>&1 &

echo "🌐 Starting Web Server: gunicorn server:app --bind $BIND_ADDR --workers $WORKERS --timeout $TIMEOUT"
exec gunicorn server:app --bind "$BIND_ADDR" --workers "$WORKERS" --timeout "$TIMEOUT" >>"$WEB_LOG" 2>&1