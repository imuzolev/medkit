import logging
import os
import sys
from collections import Counter
from pathlib import Path

import cv2
import numpy as np
from flask import Flask, jsonify, render_template, request
from ultralytics import YOLO

# Отключаем логирование Flask и Werkzeug
logging.getLogger('werkzeug').setLevel(logging.ERROR)
logging.getLogger('flask').setLevel(logging.ERROR)
cli = sys.modules['flask.cli']
cli.show_server_banner = lambda *x: None

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
app.logger.disabled = True
APP_TITLE = "Анализ комплектации дорожной аптечки"
ALLOWED_EXTENSIONS = {'jpg', 'jpeg', 'png', 'webp'}  # Поддерживаемые форматы изображений
MODEL = None

# ========================= DETECTION SETTINGS =========================
LOW_CONF = 0.05
HIGH_CONF = 0.25
IMG_SIZE = 1280
MAX_BOX_AREA_RATIO = 0.85
BANDAGE_GAP_THRESHOLD = 2.0

REQUIRED_ITEMS = {
    'Large bandage': 3,
    'small bandage': 3,
    'wipes': 2,
    'Adhesive plaster': 1,
    'Artificial respiration device': 2,
    'Instruction leaflet': 1,
    'pencil': 1,
    'Thermal blanket': 1,
    'Medical mask': 1,
    'Gloves': 1,
    'Scissors': 1,
    'Notepad': 1,
    'Tourniquet': 1,
}

ITEM_NAME_RU = {
    'Large bandage': 'Бинт большой',
    'small bandage': 'Бинт малый',
    'wipes': 'Салфетки',
    'Adhesive plaster': 'Лейкопластырь',
    'Artificial respiration device': 'Устройство для ИВЛ',
    'Instruction leaflet': 'Инструкция',
    'pencil': 'Карандаш',
    'Thermal blanket': 'Термоодеяло',
    'Medical mask': 'Медицинская маска',
    'Gloves': 'Перчатки',
    'Scissors': 'Ножницы',
    'Notepad': 'Блокнот',
    'Tourniquet': 'Жгут',
}


class DetectedObject:
    def __init__(self, cls_name: str, conf: float, box: np.ndarray):
        self.cls_name = cls_name
        self.conf = conf
        self.box = box

    @property
    def area(self) -> float:
        return float((self.box[2] - self.box[0]) * (self.box[3] - self.box[1]))


def allowed_file(filename):
    """Проверка допустимого расширения файла."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def get_model_path() -> Path:
    """Возвращает путь к best.pt (приоритет: корень проекта)."""
    base_dir = Path(__file__).resolve().parent
    root_best = base_dir / "best.pt"
    if root_best.exists():
        return root_best

    fallback_best = base_dir / "runs" / "train" / "yolo_retrain_english_3" / "weights" / "best.pt"
    if fallback_best.exists():
        return fallback_best

    raise FileNotFoundError("Файл модели best.pt не найден")


def get_model() -> YOLO:
    """Ленивая загрузка модели YOLO."""
    global MODEL
    if MODEL is None:
        model_path = get_model_path()
        MODEL = YOLO(str(model_path))
    return MODEL


def decode_image_to_bgr(image_bytes: bytes) -> np.ndarray:
    """Декодирует изображение из байтов в OpenCV BGR."""
    np_buffer = np.frombuffer(image_bytes, np.uint8)
    bgr_img = cv2.imdecode(np_buffer, cv2.IMREAD_COLOR)
    if bgr_img is None:
        raise ValueError("Не удалось прочитать изображение")
    return bgr_img


def raw_detect(model: YOLO, image: np.ndarray, img_area: float) -> list[DetectedObject]:
    """Сырая детекция объектов с базовой фильтрацией."""
    results = model.predict(
        image,
        conf=LOW_CONF,
        iou=0.5,
        imgsz=IMG_SIZE,
        augment=True,
        verbose=False,
    )[0]

    relevant_classes = set(REQUIRED_ITEMS.keys())
    objects: list[DetectedObject] = []

    for box in results.boxes:
        cls_id = int(box.cls[0])
        cls_name = model.names[cls_id]
        conf = float(box.conf[0])
        xyxy = box.xyxy[0].cpu().numpy()

        if cls_name not in relevant_classes:
            continue

        obj = DetectedObject(cls_name, conf, xyxy)
        if obj.area > img_area * MAX_BOX_AREA_RATIO:
            continue
        objects.append(obj)

    return objects


def classify_bandages(bandages: list[DetectedObject]) -> list[DetectedObject]:
    """Классифицирует бинты как большие/малые по площади и confidence."""
    if not bandages:
        return []

    bandages = [b for b in bandages if b.conf >= HIGH_CONF]
    if not bandages:
        return []

    bandages.sort(key=lambda x: x.area, reverse=True)
    areas = [b.area for b in bandages]
    max_gap = 0.0
    split_idx = -1
    gap_confirmed = False

    if len(bandages) > 1:
        for i in range(len(areas) - 1):
            denom = areas[i + 1] if areas[i + 1] > 0 else 1e-6
            ratio = areas[i] / denom
            if ratio > max_gap:
                max_gap = ratio
                split_idx = i

    if max_gap >= BANDAGE_GAP_THRESHOLD:
        gap_confirmed = True
        for i, bandage in enumerate(bandages):
            bandage.cls_name = 'Large bandage' if i <= split_idx else 'small bandage'
    else:
        votes_large = sum(1 for b in bandages if 'Large' in b.cls_name)
        votes_small = len(bandages) - votes_large

        if votes_large > votes_small:
            winner = 'Large bandage'
        elif votes_small > votes_large:
            winner = 'small bandage'
        else:
            avg_large = np.mean([b.area for b in bandages if 'Large' in b.cls_name]) if votes_large > 0 else 0
            avg_small = np.mean([b.area for b in bandages if 'small' in b.cls_name]) if votes_small > 0 else 0
            winner = 'Large bandage' if avg_large >= avg_small else 'small bandage'

        for bandage in bandages:
            bandage.cls_name = winner

    large_group = [b for b in bandages if 'Large' in b.cls_name]
    small_group = [b for b in bandages if 'small' in b.cls_name]

    if gap_confirmed:
        large_group.sort(key=lambda x: x.area, reverse=True)
        small_group.sort(key=lambda x: x.area, reverse=True)

        while len(large_group) > 3 and len(small_group) < 3:
            item = large_group.pop()
            item.cls_name = 'small bandage'
            small_group.insert(0, item)

        while len(small_group) > 3 and len(large_group) < 3:
            item = small_group.pop(0)
            item.cls_name = 'Large bandage'
            large_group.append(item)

    large_group.sort(key=lambda x: x.conf, reverse=True)
    small_group.sort(key=lambda x: x.conf, reverse=True)
    return large_group[:3] + small_group[:3]


def two_tier_filter(objects: list[DetectedObject]) -> list[DetectedObject]:
    """Фильтр в два уровня: сначала high confidence, затем добивка low confidence."""
    grouped: dict[str, list[DetectedObject]] = {}
    for obj in objects:
        grouped.setdefault(obj.cls_name, []).append(obj)

    result: list[DetectedObject] = []
    for cls_name, limit in REQUIRED_ITEMS.items():
        if 'bandage' in cls_name.lower():
            continue

        candidates = grouped.get(cls_name, [])
        candidates.sort(key=lambda x: x.conf, reverse=True)
        high = [obj for obj in candidates if obj.conf >= HIGH_CONF][:limit]
        selected = list(high)

        remaining = limit - len(selected)
        if remaining > 0:
            low = [obj for obj in candidates if obj.conf < HIGH_CONF][:remaining]
            selected.extend(low)

        result.extend(selected)

    return result


def filter_detections(raw_objects: list[DetectedObject]) -> list[DetectedObject]:
    """Финальная фильтрация детекций, включая отдельную логику для бинтов."""
    bandages = [obj for obj in raw_objects if 'bandage' in obj.cls_name.lower()]
    others = [obj for obj in raw_objects if 'bandage' not in obj.cls_name.lower()]
    filtered_bandages = classify_bandages(bandages)
    filtered_others = two_tier_filter(others)
    return filtered_bandages + filtered_others


def build_result(found: Counter) -> tuple[bool, str, list[str]]:
    """Формирует итоговый текст по комплектности."""
    missing = []
    for item, required in REQUIRED_ITEMS.items():
        current = found.get(item, 0)
        if current < required:
            ru_name = ITEM_NAME_RU.get(item, item)
            missing.append(f"{ru_name} — не хватает {required - current} шт.")

    is_complete = len(missing) == 0
    if is_complete:
        result_text = "Комплектация полная."
    else:
        result_text = "Комплектация неполная.\nНе хватает:\n- " + "\n- ".join(missing)

    return is_complete, result_text, missing


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

        # Читаем и декодируем изображение
        image_bytes = file.read()
        bgr_img = decode_image_to_bgr(image_bytes)
        img_area = bgr_img.shape[0] * bgr_img.shape[1]

        # Детекция и фильтрация по встроенной логике
        model = get_model()
        raw_objects = raw_detect(model, bgr_img, img_area)
        filtered_objects = filter_detections(raw_objects)
        found = Counter(obj.cls_name for obj in filtered_objects)
        is_complete, result_text, missing = build_result(found)

        return jsonify({
            'success': True,
            'is_complete': is_complete,
            'result_text': result_text,
            'missing': missing
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
    print("Host: 0.0.0.0")
    sys.stdout.flush()

    try:
        # Запускаем без лишнего вывода
        print("Calling app.run()...")
        sys.stdout.flush()
        app.run(debug=False, host='0.0.0.0', port=port, use_reloader=False)
        print(f"Flask server started successfully on 0.0.0.0:{port}")
        sys.stdout.flush()
    except Exception as e:
        print(f"ERROR starting Flask: {e}")
        sys.stdout.flush()
        raise
