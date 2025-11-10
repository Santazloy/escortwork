@echo off
chcp 65001 > nul
setlocal enabledelayedexpansion

REM Скрипт запуска Balance Bot для Windows
REM Этот бот работает отдельно и отслеживает баланс в Telegram группах

echo ===================================
echo   Balance Bot Launcher (Windows)
echo ===================================

REM Проверка Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python не найден. Установите Python 3.8 или выше.
    pause
    exit /b 1
)

for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYTHON_VERSION=%%i
echo ✓ Python версия: %PYTHON_VERSION%

REM Создание виртуального окружения
if not exist "venv" (
    echo Создание виртуального окружения...
    python -m venv venv
)

REM Активация виртуального окружения
echo Активация виртуального окружения...
call venv\Scripts\activate.bat

REM Установка зависимостей
echo Установка зависимостей...
python -m pip install -q --upgrade pip
pip install -q -r requirements.txt

REM Проверка переменных окружения
if "%BALANCE_BOT_TOKEN%"=="" (
    echo ⚠️  ПРЕДУПРЕЖДЕНИЕ: BALANCE_BOT_TOKEN не установлен!
    echo Установите переменную окружения или создайте .env файл
)

if "%SUPABASE_URL%"=="" (
    echo ⚠️  ПРЕДУПРЕЖДЕНИЕ: SUPABASE_URL не установлен!
)

if "%SUPABASE_KEY%"=="" (
    echo ⚠️  ПРЕДУПРЕЖДЕНИЕ: SUPABASE_KEY не установлен!
)

echo.
echo ===================================
echo   Запуск Balance Bot...
echo ===================================
echo.

REM Запуск бота
python balance_bot.py

pause
