from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import os
from werkzeug.utils import secure_filename
import logging
from bot import send_application

app = Flask(__name__, static_folder='.', static_url_path='')
CORS(app)  # Разрешаем CORS для frontend

# Настройки
UPLOAD_FOLDER = 'uploads'
ALLOWED_PHOTO_EXTENSIONS = {'png', 'jpg', 'jpeg', 'heic'}
ALLOWED_VIDEO_EXTENSIONS = {'mp4', 'mov', 'avi'}
MAX_FILE_SIZE = 100 * 1024 * 1024  # 100 MB

# Создаем папку для загрузок если её нет
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = MAX_FILE_SIZE

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def allowed_file(filename, allowed_extensions):
    """Проверяет допустимость расширения файла"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in allowed_extensions


@app.route('/api/submit', methods=['POST'])
def submit_application():
    """Обработка отправки анкеты"""
    try:
        # Получаем данные формы
        data = {
            'name': request.form.get('name'),
            'age': request.form.get('age'),
            'height': request.form.get('height'),
            'weight': request.form.get('weight'),
            'citizenship': request.form.get('citizenship'),
            'telegram': request.form.get('telegram'),
            'whatsapp': request.form.get('whatsapp'),
            'experience': request.form.get('experience'),
            'countries': request.form.get('countries')
        }

        logger.info(f"Получена анкета от: {data.get('name')}")

        # Обработка фото
        photo_paths = []
        if 'photos' in request.files:
            photos = request.files.getlist('photos')
            for photo in photos:
                if photo and photo.filename and allowed_file(photo.filename, ALLOWED_PHOTO_EXTENSIONS):
                    filename = secure_filename(photo.filename)
                    # Добавляем timestamp к имени файла для уникальности
                    import time
                    filename = f"{int(time.time())}_{filename}"
                    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                    photo.save(filepath)
                    photo_paths.append(filepath)
                    logger.info(f"Сохранено фото: {filename}")

        # Обработка видео
        video_path = None
        if 'video' in request.files:
            video = request.files['video']
            if video and video.filename and allowed_file(video.filename, ALLOWED_VIDEO_EXTENSIONS):
                filename = secure_filename(video.filename)
                import time
                filename = f"{int(time.time())}_{filename}"
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                video.save(filepath)
                video_path = filepath
                logger.info(f"Сохранено видео: {filename}")

        # Отправляем в Telegram
        success = send_application(data, photo_paths, video_path)

        # Удаляем файлы после отправки
        for photo_path in photo_paths:
            try:
                os.remove(photo_path)
            except:
                pass

        if video_path:
            try:
                os.remove(video_path)
            except:
                pass

        if success:
            return jsonify({
                'success': True,
                'message': 'Анкета успешно отправлена!'
            }), 200
        else:
            return jsonify({
                'success': False,
                'message': 'Ошибка при отправке анкеты'
            }), 500

    except Exception as e:
        logger.error(f"Ошибка обработки анкеты: {e}")
        return jsonify({
            'success': False,
            'message': f'Ошибка сервера: {str(e)}'
        }), 500


@app.route('/api/test', methods=['GET'])
def test():
    """Тестовый эндпоинт"""
    return jsonify({
        'status': 'ok',
        'message': 'Сервер работает'
    })


@app.route('/')
def index():
    """Отдача главной страницы"""
    return send_from_directory('.', 'index.html')


@app.errorhandler(404)
def fallback(e):
    """Обработчик 404 для SPA - отдаем index.html"""
    return send_from_directory('.', 'index.html'), 200


if __name__ == '__main__':
    port = int(os.getenv("PORT", 5000))
    print(f"🚀 Запуск сервера на порту {port}")
    print("📱 Telegram бот готов к отправке анкет")
    app.run(host='0.0.0.0', port=port)