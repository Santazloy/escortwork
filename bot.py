import logging
import asyncio
import os
from telegram import Bot
from telegram.error import TelegramError

# Настройки
BOT_TOKEN = os.getenv("BOT_TOKEN")
GROUP_ID = os.getenv("GROUP_ID")

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)


async def send_application_to_group(data, photos=None, video=None):
    """
    Отправляет анкету в Telegram группу

    Args:
        data: словарь с данными анкеты
        photos: список путей к фото файлам
        video: путь к видео файлу
    """
    bot = Bot(token=BOT_TOKEN)

    try:
        # Формируем текст сообщения
        message = f"""
🆕 <b>НОВАЯ АНКЕТА МОДЕЛИ</b>

👤 <b>Имя:</b> {data.get('name', 'Не указано')}
🎂 <b>Возраст:</b> {data.get('age', 'Не указано')} лет
📏 <b>Рост:</b> {data.get('height', 'Не указано')} см
⚖️ <b>Вес:</b> {data.get('weight', 'Не указано')} кг
🌍 <b>Гражданство:</b> {data.get('citizenship', 'Не указано')}
💬 <b>Telegram:</b> {data.get('telegram', 'Не указано')}
📲 <b>WhatsApp:</b> {data.get('whatsapp', 'Не указано')}
💼 <b>Опыт:</b> {data.get('experience', 'Не указано')}
"""

        if data.get('countries'):
            message += f"🗺️ <b>Страны опыта:</b> {data.get('countries')}\n"

        # Отправляем текстовое сообщение
        await bot.send_message(
            chat_id=GROUP_ID,
            text=message,
            parse_mode='HTML'
        )

        # Отправляем фото если есть
        if photos:
            for photo_path in photos:
                try:
                    with open(photo_path, 'rb') as photo_file:
                        await bot.send_photo(
                            chat_id=GROUP_ID,
                            photo=photo_file
                        )
                except Exception as e:
                    logger.error(f"Ошибка отправки фото {photo_path}: {e}")

        # Отправляем видео если есть
        if video:
            try:
                with open(video, 'rb') as video_file:
                    await bot.send_video(
                        chat_id=GROUP_ID,
                        video=video_file,
                        caption="📹 Видео презентация"
                    )
            except Exception as e:
                logger.error(f"Ошибка отправки видео {video}: {e}")

        logger.info("Анкета успешно отправлена в группу")
        return True

    except TelegramError as e:
        logger.error(f"Ошибка Telegram API: {e}")
        return False
    except Exception as e:
        logger.error(f"Неожиданная ошибка: {e}")
        return False


# Функция для синхронного вызова
def send_application(data, photos=None, video=None):
    """Синхронная обертка для отправки анкеты"""
    return asyncio.run(send_application_to_group(data, photos, video))


if __name__ == "__main__":
    # Тестовая отправка
    test_data = {
        'name': 'Тест Тестовый',
        'age': '25',
        'height': '175',
        'weight': '55',
        'citizenship': 'Россия',
        'telegram': '@test',
        'whatsapp': '+7 999 999-99-99',
        'experience': 'Есть опыт',
        'countries': 'Россия, Италия'
    }

    print("Отправка тестовой анкеты...")
    result = send_application(test_data)
    if result:
        print("✅ Успешно отправлено!")
    else:
        print("❌ Ошибка отправки")