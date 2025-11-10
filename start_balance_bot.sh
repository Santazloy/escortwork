#!/bin/bash

# Скрипт запуска Balance Bot (НЕ трогает основной сервер)
# Этот бот работает отдельно и отслеживает баланс в Telegram группах

echo "==================================="
echo "  Balance Bot Launcher"
echo "==================================="

# Проверка версии Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 не найден. Установите Python 3.8 или выше."
    exit 1
fi

PYTHON_VERSION=$(python3 --version | cut -d ' ' -f 2 | cut -d '.' -f 1,2)
echo "✓ Python версия: $PYTHON_VERSION"

# Создание виртуального окружения если его нет
if [ ! -d "venv" ]; then
    echo "Создание виртуального окружения..."
    python3 -m venv venv
fi

# Активация виртуального окружения
echo "Активация виртуального окружения..."
source venv/bin/activate

# Установка зависимостей
echo "Установка зависимостей..."
pip install -q --upgrade pip
pip install -q -r requirements.txt

# Проверка переменных окружения
if [ -z "$BALANCE_BOT_TOKEN" ]; then
    echo "⚠️  ПРЕДУПРЕЖДЕНИЕ: BALANCE_BOT_TOKEN не установлен!"
    echo "Установите переменную окружения или создайте .env файл"
fi

if [ -z "$SUPABASE_URL" ] || [ -z "$SUPABASE_KEY" ]; then
    echo "⚠️  ПРЕДУПРЕЖДЕНИЕ: SUPABASE_URL или SUPABASE_KEY не установлены!"
    echo "Настройте подключение к Supabase"
fi

echo ""
echo "==================================="
echo "  Запуск Balance Bot..."
echo "==================================="
echo ""

# Запуск бота
python3 balance_bot.py