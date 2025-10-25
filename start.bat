@echo off
chcp 65001 > nul

echo 🚀 Запуск Escortwork...
echo.

REM Проверяем Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python не найден. Установите Python 3.8 или выше
    pause
    exit /b 1
)

REM Создаем виртуальное окружение если его нет
if not exist "venv" (
    echo 📦 Создание виртуального окружения...
    python -m venv venv
)

REM Активируем виртуальное окружение
echo 🔧 Активация виртуального окружения...
call venv\Scripts\activate.bat

REM Устанавливаем зависимости
echo 📥 Установка зависимостей...
pip install -r requirements.txt

REM Создаем папку для загрузок
if not exist "uploads" mkdir uploads

echo.
echo ✅ Все готово!
echo.
echo 🌐 Запуск сервера на http://localhost:5000
echo 📱 Telegram бот готов к работе
echo.
echo Откройте index.html в браузере для доступа к сайту
echo Нажмите Ctrl+C для остановки сервера
echo.

REM Запускаем сервер
python server.py

pause