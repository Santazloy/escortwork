#!/bin/bash

# Скрипт запуска проекта Escortwork

echo "🚀 Запуск Escortwork..."
echo ""

# Проверяем наличие Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 не найден. Установите Python 3.8 или выше"
    exit 1
fi

# Проверяем наличие pip
if ! command -v pip3 &> /dev/null; then
    echo "❌ pip3 не найден. Установите pip"
    exit 1
fi

# Создаем виртуальное окружение если его нет
if [ ! -d "venv" ]; then
    echo "📦 Создание виртуального окружения..."
    python3 -m venv venv
fi

# Активируем виртуальное окружение
echo "🔧 Активация виртуального окружения..."
source venv/bin/activate

# Устанавливаем зависимости
echo "📥 Установка зависимостей..."
pip install -r requirements.txt

# Создаем папку для загрузок
mkdir -p uploads

echo ""
echo "✅ Все готово!"
echo ""
echo "🌐 Запуск сервера на http://localhost:5000"
echo "📱 Telegram бот готов к работе"
echo ""
echo "Откройте index.html в браузере для доступа к сайту"
echo "Нажмите Ctrl+C для остановки сервера"
echo ""

# Запускаем сервер
python3 server.py