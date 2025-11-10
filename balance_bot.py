"""
Бот для учета баланса в двух Telegram группах
Не влияет на существующий функционал отправки анкет
"""

import logging
import os
import re
from decimal import Decimal
from supabase import create_client, Client
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Настройки из переменных окружения
BOT_TOKEN = os.getenv("BOT_TOKEN")  # Используем того же бота, что и для анкет
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

# ID групп
GROUP_RU = -1002774266933  # Русская группа
GROUP_ZH = -1002468561827  # Китайская группа

# Инициализация Supabase клиента
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)


def format_number(number: Decimal) -> str:
    """Форматирует число с разделителями тысяч"""
    # Конвертируем в строку с 2 знаками после запятой
    num_str = f"{number:,.2f}"
    # Заменяем запятую на пробел для тысяч, а точку на запятую для дробной части
    num_str = num_str.replace(",", " ")
    # Удаляем .00 если нет дробной части
    if num_str.endswith(".00"):
        num_str = num_str[:-3]
    return num_str


def get_current_balance(group_id: int) -> Decimal:
    """Получает текущий баланс группы из базы данных"""
    try:
        response = supabase.table('group_balances').select('current_balance').eq('group_id', group_id).execute()

        if response.data and len(response.data) > 0:
            return Decimal(str(response.data[0]['current_balance']))
        else:
            # Если записи нет, создаем её
            language = 'ru' if group_id == GROUP_RU else 'zh'
            group_name = 'Русская группа' if group_id == GROUP_RU else '中文群组'

            supabase.table('group_balances').insert({
                'group_id': group_id,
                'group_name': group_name,
                'current_balance': 0,
                'language': language
            }).execute()

            return Decimal('0')
    except Exception as e:
        logger.error(f"Ошибка получения баланса: {e}")
        return Decimal('0')


def update_balance(group_id: int, amount: Decimal, user_id: int, username: str, message_id: int) -> tuple[Decimal, Decimal]:
    """
    Обновляет баланс группы и сохраняет транзакцию
    Возвращает (предыдущий_баланс, новый_баланс)
    """
    try:
        # Получаем текущий баланс
        previous_balance = get_current_balance(group_id)
        new_balance = previous_balance + amount

        # Обновляем баланс в базе
        supabase.table('group_balances').update({
            'current_balance': float(new_balance)
        }).eq('group_id', group_id).execute()

        # Сохраняем транзакцию
        transaction_type = 'add' if amount > 0 else 'subtract'
        supabase.table('balance_transactions').insert({
            'group_id': group_id,
            'user_id': user_id,
            'username': username,
            'amount': float(amount),
            'previous_balance': float(previous_balance),
            'new_balance': float(new_balance),
            'transaction_type': transaction_type,
            'message_id': message_id
        }).execute()

        logger.info(f"Баланс обновлен для группы {group_id}: {previous_balance} -> {new_balance}")
        return previous_balance, new_balance

    except Exception as e:
        logger.error(f"Ошибка обновления баланса: {e}")
        raise


def format_message_ru(amount: Decimal, previous_balance: Decimal, new_balance: Decimal) -> str:
    """Форматирует сообщение на русском языке"""
    if amount > 0:
        emoji = "💰"
        title = "Баланс пополнен!"
        operation_emoji = "➕"
        operation_text = "Пополнение"
    else:
        emoji = "💸"
        title = "Списание с баланса"
        operation_emoji = "➖"
        operation_text = "Списание"
        amount = abs(amount)  # Делаем положительным для отображения

    message = f"""{emoji} <b>{title}</b>
📈 <b>Было:</b> {format_number(previous_balance)} ¥
{operation_emoji} <b>{operation_text}:</b> {format_number(amount)} ¥
💎 <b>Итоговый баланс:</b> {format_number(new_balance)} ¥"""

    return message


def format_message_zh(amount: Decimal, previous_balance: Decimal, new_balance: Decimal) -> str:
    """Форматирует сообщение на китайском языке"""
    if amount > 0:
        emoji = "💰"
        title = "余额已充值！"
        operation_emoji = "➕"
        operation_text = "充值金额"
    else:
        emoji = "💸"
        title = "余额已扣除"
        operation_emoji = "➖"
        operation_text = "扣除金额"
        amount = abs(amount)

    message = f"""{emoji} <b>{title}</b>
📈 <b>之前余额:</b> {format_number(previous_balance)} ¥
{operation_emoji} <b>{operation_text}:</b> {format_number(amount)} ¥
💎 <b>当前余额:</b> {format_number(new_balance)} ¥"""

    return message


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обрабатывает сообщения в группах"""

    # Проверяем, что сообщение из нужной группы
    if not update.message or not update.message.chat:
        return

    chat_id = update.message.chat.id

    # Проверяем, что это одна из наших групп
    if chat_id not in [GROUP_RU, GROUP_ZH]:
        return

    # Получаем текст сообщения
    text = update.message.text
    if not text:
        return

    # Парсим сообщение на наличие +число или -число
    # Поддерживаем форматы: +1000, -5000, +1,000, -5,000, +1000.50
    pattern = r'^([+\-])\s*(\d{1,3}(?:[,\s]?\d{3})*(?:\.\d{1,2})?)$'
    match = re.match(pattern, text.strip())

    if not match:
        return

    try:
        sign = match.group(1)
        amount_str = match.group(2).replace(',', '').replace(' ', '')
        amount = Decimal(amount_str)

        # Применяем знак
        if sign == '-':
            amount = -amount

        # Получаем информацию о пользователе
        user_id = update.message.from_user.id if update.message.from_user else 0
        username = update.message.from_user.username if update.message.from_user else "Unknown"
        message_id = update.message.message_id

        # Обновляем баланс
        previous_balance, new_balance = update_balance(
            group_id=chat_id,
            amount=amount,
            user_id=user_id,
            username=username,
            message_id=message_id
        )

        # Форматируем ответное сообщение
        if chat_id == GROUP_RU:
            response_message = format_message_ru(amount, previous_balance, new_balance)
        else:  # GROUP_ZH
            response_message = format_message_zh(amount, previous_balance, new_balance)

        # Отправляем ответ
        await update.message.reply_text(
            text=response_message,
            parse_mode='HTML'
        )

        logger.info(f"Обработана транзакция в группе {chat_id}: {amount}")

    except Exception as e:
        logger.error(f"Ошибка обработки сообщения: {e}")
        # Не отправляем сообщение об ошибке пользователю, чтобы не спамить


def main():
    """Запускает бота"""

    # Проверяем наличие необходимых переменных окружения
    if not BOT_TOKEN:
        logger.error("BOT_TOKEN не установлен!")
        return

    if not SUPABASE_URL or not SUPABASE_KEY:
        logger.error("SUPABASE_URL или SUPABASE_KEY не установлены!")
        return

    # Создаем приложение
    application = Application.builder().token(BOT_TOKEN).build()

    # Добавляем обработчик для всех текстовых сообщений в группах
    application.add_handler(
        MessageHandler(
            filters.TEXT & filters.ChatType.GROUPS,
            handle_message
        )
    )

    logger.info("Balance bot запущен и готов к работе!")
    logger.info(f"Отслеживаемые группы: {GROUP_RU} (RU), {GROUP_ZH} (ZH)")

    # Запускаем бота
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
