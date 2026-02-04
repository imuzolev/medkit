import io
import base64
import logging
import os
import sys
from pathlib import Path

import cv2
import numpy as np
from PIL import Image
from flask import Flask, render_template, request, jsonify


# Отключаем логирование Flask и Werkzeug
logging.getLogger('werkzeug').setLevel(logging.ERROR)
logging.getLogger('flask').setLevel(logging.ERROR)
cli = sys.modules['flask.cli']
cli.show_server_banner = lambda *x: None

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
app.logger.disabled = True

APP_TITLE = "Анализ аптечки"
ALLOWED_EXTENSIONS = {'jpg', 'jpeg', 'png', 'webp'}  # Поддерживаемые форматы изображений


def allowed_file(filename):
    """Проверка допустимого расширения файла."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def resize_image_bytes(image_bytes: bytes, scale_factor: float = 1/3) -> bytes:
    """Изменяет размер изображения в scale_factor раз."""
    try:
        with Image.open(io.BytesIO(image_bytes)) as im:
            new_size = (max(1, int(im.width * scale_factor)), max(1, int(im.height * scale_factor)))
            resized_im = im.resize(new_size, Image.Resampling.LANCZOS)
            output = io.BytesIO()
            img_format = im.format if im.format else "JPEG"
            resized_im.save(output, format=img_format)
            return output.getvalue()
    except Exception:
        return image_bytes


def bytes_to_pil(image_bytes: bytes) -> Image.Image:
    """Конвертирует байты в PIL Image."""
    with Image.open(io.BytesIO(image_bytes)) as im:
        return im.convert("RGB")


def pil_to_cv2_bgr(pil_img: Image.Image) -> np.ndarray:
    """Конвертирует PIL Image в OpenCV BGR формат."""
    rgb = np.array(pil_img)
    return cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR)


def cv2_bgr_to_rgb(bgr: np.ndarray) -> np.ndarray:
    """Конвертирует OpenCV BGR в RGB."""
    return cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)


def process_image_demo(bgr: np.ndarray) -> np.ndarray:
    """
    Демо-пайплайн: Перевод в ЧБ.
    Возвращает обработанное изображение в RGB формате.
    """
    gray = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)
    processed_rgb = cv2.cvtColor(gray, cv2.COLOR_GRAY2RGB)
    return processed_rgb


def numpy_to_base64(img_array: np.ndarray) -> str:
    """Конвертирует numpy array в base64 строку."""
    img = Image.fromarray(img_array)
    buffer = io.BytesIO()
    img.save(buffer, format='PNG')
    buffer.seek(0)
    img_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
    return f"data:image/png;base64,{img_base64}"


@app.route('/')
def index():
    """Главная страница."""
    return render_template('index.html', app_title=APP_TITLE)


@app.route('/process', methods=['POST'])
def process():
    """Обработка загруженного изображения."""
    try:
        if 'image' not in request.files:
            return jsonify({'error': 'Файл не найден'}), 400
        
        file = request.files['image']
        
        if file.filename == '':
            return jsonify({'error': 'Файл не выбран'}), 400
        
        if not allowed_file(file.filename):
            return jsonify({'error': 'Недопустимый формат файла'}), 400
        
        # Читаем и изменяем размер изображения
        image_bytes = file.read()
        resized_bytes = resize_image_bytes(image_bytes, 1/3)
        
        # Конвертируем и обрабатываем
        pil_img = bytes_to_pil(resized_bytes)
        bgr_img = pil_to_cv2_bgr(pil_img)
        
        # Обработка изображения
        processed_rgb = process_image_demo(bgr_img)
        
        # Конвертируем оригинал в RGB для единообразия
        original_rgb = cv2_bgr_to_rgb(bgr_img)
        
        # Конвертируем в base64 для передачи клиенту
        original_base64 = numpy_to_base64(original_rgb)
        processed_base64 = numpy_to_base64(processed_rgb)
        
        return jsonify({
            'success': True,
            'original': original_base64,
            'processed': processed_base64
        })
    
    except Exception as e:
        return jsonify({'error': f'Ошибка обработки: {str(e)}'}), 500


if __name__ == '__main__':
    # Создаем папки если их нет
    Path('templates').mkdir(exist_ok=True)
    Path('static').mkdir(exist_ok=True)
    
    # Получаем порт из переменной окружения (для Coolify) или используем 5000 по умолчанию
    port = int(os.environ.get('PORT', 5000))
    
    # Выводим информацию о запуске для логов Coolify
    print(f"Starting Flask application on port {port}")
    print(f"PORT environment variable: {os.environ.get('PORT', 'not set (using default 5000)')}")
    print(f"Host: 0.0.0.0")
    sys.stdout.flush()
    
    try:
        # Запускаем без лишнего вывода
        print(f"Calling app.run()...")
        sys.stdout.flush()
        app.run(debug=False, host='0.0.0.0', port=port, use_reloader=False)
        print(f"Flask server started successfully on 0.0.0.0:{port}")
        sys.stdout.flush()
    except Exception as e:
        print(f"ERROR starting Flask: {e}")
        sys.stdout.flush()
        raise
