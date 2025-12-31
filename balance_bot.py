"""
Бот для учета баланса в Telegram группах
Поддерживает несколько групп с разными языками
Не влияет на существующий функционал отправки анкет
"""

import logging
import os
import re
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
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

# ID групп (читаем из ENV, с fallback на дефолтные значения)
GROUP_RU = int(os.getenv("GROUP_RU_ID", "-1002774266933"))  # Русская группа (Shanghai)
GROUP_ZH_SHANGHAI = int(os.getenv("GROUP_ZH_ID", "-1002468561827"))  # Китайская группа Shanghai
GROUP_ZH_BEIJING = int(os.getenv("GROUP_ZH_BEIJING_ID", "-1003698590476"))  # Китайская группа Beijing 北京

# Список всех китайских групп
CHINESE_GROUPS = [GROUP_ZH_SHANGHAI, GROUP_ZH_BEIJING]

# Список всех отслеживаемых групп
ALL_GROUPS = [GROUP_RU] + CHINESE_GROUPS

# Лимиты для валидации
MAX_TRANSACTION_AMOUNT = Decimal('999999999.99')  # Максимальная сумма транзакции
MIN_TRANSACTION_AMOUNT = Decimal('0.01')  # Минимальная сумма транзакции

# Конфигурация групп (для автоматического создания записей в БД)
GROUP_CONFIG = {
    GROUP_RU: {'name': 'Русская группа (Shanghai)', 'language': 'ru'},
    GROUP_ZH_SHANGHAI: {'name': '上海中文群组', 'language': 'zh'},
    GROUP_ZH_BEIJING: {'name': '北京中文群组', 'language': 'zh'},
}

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
            # Используем str() для безопасной конвертации в Decimal
            return Decimal(str(response.data[0]['current_balance']))
        else:
            # Если записи нет, создаем её с конфигурацией из GROUP_CONFIG
            config = GROUP_CONFIG.get(group_id, {'name': f'Group {group_id}', 'language': 'zh'})

            supabase.table('group_balances').insert({
                'group_id': group_id,
                'group_name': config['name'],
                'current_balance': '0.00',  # Используем строку для точности
                'language': config['language']
            }).execute()

            logger.info(f"Создана запись баланса для группы {group_id} ({config['name']})")
            return Decimal('0')
    except Exception as e:
        logger.error(f"Ошибка получения баланса для группы {group_id}: {e}")
        raise


def validate_amount(amount: Decimal) -> tuple[bool, str]:
    """
    Валидирует сумму транзакции
    Возвращает (is_valid, error_message)
    """
    abs_amount = abs(amount)

    if abs_amount < MIN_TRANSACTION_AMOUNT:
        return False, f"Сумма слишком мала. Минимум: {MIN_TRANSACTION_AMOUNT}"

    if abs_amount > MAX_TRANSACTION_AMOUNT:
        return False, f"Сумма слишком большая. Максимум: {MAX_TRANSACTION_AMOUNT}"

    return True, ""


def normalize_amount(amount: Decimal) -> Decimal:
    """
    Нормализует сумму до 2 знаков после запятой
    Использует банковское округление (ROUND_HALF_UP)
    """
    return amount.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)


def update_balance(group_id: int, amount: Decimal, user_id: int, username: str, message_id: int) -> tuple[Decimal, Decimal]:
    """
    Обновляет баланс группы и сохраняет транзакцию
    Возвращает (предыдущий_баланс, новый_баланс)

    ВАЖНО: Используем str() для Decimal значений чтобы избежать
    потери точности при конвертации в float
    """
    # Нормализуем сумму до 2 знаков после запятой
    amount = normalize_amount(amount)

    # Получаем текущий баланс
    previous_balance = get_current_balance(group_id)
    new_balance = normalize_amount(previous_balance + amount)

    try:
        # Обновляем баланс в базе (используем str для сохранения точности)
        supabase.table('group_balances').update({
            'current_balance': str(new_balance)
        }).eq('group_id', group_id).execute()

        # Сохраняем транзакцию (используем str для всех Decimal полей)
        transaction_type = 'add' if amount > 0 else 'subtract'
        supabase.table('balance_transactions').insert({
            'group_id': group_id,
            'user_id': user_id,
            'username': username or 'Unknown',
            'amount': str(amount),
            'previous_balance': str(previous_balance),
            'new_balance': str(new_balance),
            'transaction_type': transaction_type,
            'message_id': message_id
        }).execute()

        logger.info(f"Баланс обновлен для группы {group_id}: {previous_balance} -> {new_balance} (изменение: {amount})")
        return previous_balance, new_balance

    except Exception as e:
        logger.error(f"Ошибка обновления баланса для группы {group_id}: {e}")
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


def get_language_for_group(group_id: int) -> str:
    """Возвращает язык для группы"""
    config = GROUP_CONFIG.get(group_id)
    if config:
        return config['language']
    # По умолчанию китайский для неизвестных групп
    return 'zh'


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обрабатывает сообщения в группах"""

    # Проверяем, что сообщение из нужной группы
    if not update.message or not update.message.chat:
        return

    chat_id = update.message.chat.id

    # Проверяем, что это одна из наших групп
    if chat_id not in ALL_GROUPS:
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

        # Безопасный парсинг суммы
        try:
            amount = Decimal(amount_str)
        except InvalidOperation:
            logger.warning(f"Невалидная сумма: {amount_str}")
            return

        # Применяем знак
        if sign == '-':
            amount = -amount

        # Валидируем сумму
        is_valid, error_msg = validate_amount(amount)
        if not is_valid:
            logger.warning(f"Сумма не прошла валидацию: {amount} - {error_msg}")
            return

        # Получаем информацию о пользователе
        user_id = update.message.from_user.id if update.message.from_user else 0
        username = update.message.from_user.username if update.message.from_user else None
        message_id = update.message.message_id

        # Обновляем баланс
        previous_balance, new_balance = update_balance(
            group_id=chat_id,
            amount=amount,
            user_id=user_id,
            username=username,
            message_id=message_id
        )

        # Форматируем ответное сообщение на основе языка группы
        language = get_language_for_group(chat_id)
        if language == 'ru':
            response_message = format_message_ru(amount, previous_balance, new_balance)
        else:  # zh (китайский) - для всех китайских групп (Shanghai и Beijing)
            response_message = format_message_zh(amount, previous_balance, new_balance)

        # Отправляем ответ
        await update.message.reply_text(
            text=response_message,
            parse_mode='HTML'
        )

        group_name = GROUP_CONFIG.get(chat_id, {}).get('name', str(chat_id))
        logger.info(f"Обработана транзакция в группе {group_name}: {amount}")

    except Exception as e:
        logger.error(f"Ошибка обработки сообщения в группе {chat_id}: {e}", exc_info=True)


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

    logger.info("=" * 50)
    logger.info("Balance bot запущен и готов к работе!")
    logger.info("=" * 50)
    logger.info("Отслеживаемые группы:")
    for group_id, config in GROUP_CONFIG.items():
        logger.info(f"  - {config['name']} (ID: {group_id}, язык: {config['language']})")
    logger.info("=" * 50)

    # Запускаем бота
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
