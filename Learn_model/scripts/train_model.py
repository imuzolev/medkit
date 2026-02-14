"""
Программа для обучения YOLO модели на 300 эпох с использованием GPU (CUDA).
После каждой эпохи показывает текущие параметры и дает оценку от 0 до 100.
Работает ТОЛЬКО на GPU. Если GPU недоступна — обучение не запускается.
"""

import torch
from ultralytics import YOLO
import os
import sys


def calculate_score(metrics):
    """
    Вычисляет оценку от 0 до 100 на основе метрик модели.

    Args:
        metrics: словарь с метриками (precision, recall, mAP50, mAP50-95)

    Returns:
        float: оценка от 0 до 100
    """
    weights = {
        'precision': 0.25,
        'recall': 0.25,
        'mAP50': 0.30,
        'mAP50-95': 0.20
    }

    precision = metrics.get('metrics/precision(B)', 0.0) * 100
    recall = metrics.get('metrics/recall(B)', 0.0) * 100
    map50 = metrics.get('metrics/mAP50(B)', 0.0) * 100
    map50_95 = metrics.get('metrics/mAP50-95(B)', 0.0) * 100

    score = (
        precision * weights['precision'] +
        recall * weights['recall'] +
        map50 * weights['mAP50'] +
        map50_95 * weights['mAP50-95']
    )

    return round(score, 2)


def print_epoch_info(epoch, metrics, score):
    """
    Выводит информацию об эпохе с параметрами и оценкой.

    Args:
        epoch: номер эпохи
        metrics: словарь с метриками
        score: оценка модели
    """
    print("\n" + "="*80)
    print(f"ЭПОХА {epoch}/300")
    print("="*80)

    print("\n ТЕКУЩИЕ ПАРАМЕТРЫ:")
    print("-" * 80)

    precision = metrics.get('metrics/precision(B)', 0.0)
    recall = metrics.get('metrics/recall(B)', 0.0)
    map50 = metrics.get('metrics/mAP50(B)', 0.0)
    map50_95 = metrics.get('metrics/mAP50-95(B)', 0.0)

    print(f"  Precision:     {precision:.4f} ({precision*100:.2f}%)")
    print(f"  Recall:        {recall:.4f} ({recall*100:.2f}%)")
    print(f"  mAP50:         {map50:.4f} ({map50*100:.2f}%)")
    print(f"  mAP50-95:      {map50_95:.4f} ({map50_95*100:.2f}%)")

    train_box_loss = metrics.get('train/box_loss', 0.0)
    train_cls_loss = metrics.get('train/cls_loss', 0.0)
    train_dfl_loss = metrics.get('train/dfl_loss', 0.0)
    val_box_loss = metrics.get('val/box_loss', 0.0)
    val_cls_loss = metrics.get('val/cls_loss', 0.0)
    val_dfl_loss = metrics.get('val/dfl_loss', 0.0)

    print(f"\n  Train Box Loss:  {train_box_loss:.4f}")
    print(f"  Train Cls Loss:  {train_cls_loss:.4f}")
    print(f"  Train DFL Loss:  {train_dfl_loss:.4f}")
    print(f"  Val Box Loss:    {val_box_loss:.4f}")
    print(f"  Val Cls Loss:    {val_cls_loss:.4f}")
    print(f"  Val DFL Loss:    {val_dfl_loss:.4f}")

    print("\n" + "-" * 80)
    print(f"  ОЦЕНКА МОДЕЛИ: {score}/100")
    print("-" * 80)

    bar_length = 50
    filled = int(bar_length * score / 100)
    bar = "=" * filled + "-" * (bar_length - filled)
    print(f"  [{bar}] {score}%")

    print("="*80 + "\n")


def on_fit_epoch_end(trainer):
    """
    Колбэк, вызываемый после каждой эпохи обучения (train + val).
    Выводит параметры модели и оценку.
    """
    epoch = trainer.epoch + 1

    all_metrics = {}

    if hasattr(trainer, 'metrics') and trainer.metrics:
        all_metrics.update(trainer.metrics)

    if hasattr(trainer, 'label_loss_items') and hasattr(trainer, 'tloss'):
        try:
            train_losses = trainer.label_loss_items(trainer.tloss, prefix="train")
            all_metrics.update(train_losses)
        except Exception:
            pass

    if hasattr(trainer, 'validator') and hasattr(trainer.validator, 'loss'):
        try:
            val_losses = trainer.label_loss_items(trainer.validator.loss, prefix="val")
            all_metrics.update(val_losses)
        except Exception:
            pass

    score = calculate_score(all_metrics)
    print_epoch_info(epoch, all_metrics, score)


def check_gpu():
    """
    Проверяет доступность GPU. Завершает программу, если GPU недоступна.
    """
    if not torch.cuda.is_available():
        print("\n[ОШИБКА] CUDA недоступна! Обучение возможно ТОЛЬКО на GPU.")
        print("  Убедитесь, что:")
        print("  1. Установлен NVIDIA драйвер")
        print("  2. PyTorch установлен с поддержкой CUDA")
        print("  Установите нужную версию:")
        print("    pip install --pre torch torchvision --index-url https://download.pytorch.org/whl/nightly/cu128")
        sys.exit(1)

    # Проверяем работоспособность GPU
    try:
        test_tensor = torch.randn(1, 1).cuda()
        del test_tensor
        torch.cuda.empty_cache()
    except RuntimeError as e:
        print(f"\n[ОШИБКА] GPU обнаружена, но не работает: {e}")
        print("  Возможно, нужна другая сборка PyTorch с поддержкой вашей GPU.")
        print("  Для RTX 50xx (Blackwell, sm_120) установите:")
        print("    pip install --pre torch torchvision --index-url https://download.pytorch.org/whl/nightly/cu128")
        sys.exit(1)

    gpu_name = torch.cuda.get_device_name(0)
    cuda_version = torch.version.cuda
    capability = torch.cuda.get_device_capability(0)
    mem_gb = torch.cuda.get_device_properties(0).total_memory / 1024**3

    print(f"\n[GPU] Устройство: CUDA")
    print(f"  GPU: {gpu_name}")
    print(f"  CUDA версия: {cuda_version}")
    print(f"  Compute Capability: sm_{capability[0]}{capability[1]}")
    print(f"  Память GPU: {mem_gb:.2f} GB")


def main():
    """Основная функция для обучения модели."""
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    # Проверяем GPU — без GPU не запускаемся
    check_gpu()

    # Путь к конфигурационному файлу датасета
    data_yaml = os.path.join(base_dir, "configs", "data.yaml")

    if not os.path.exists(data_yaml):
        print(f"[ОШИБКА] Файл data.yaml не найден!")
        print(f"  Ищу по пути: {data_yaml}")
        return

    print(f"\n[ДАННЫЕ] Загрузка датасета из: {data_yaml}")

    # Инициализация модели
    print("\n[МОДЕЛЬ] Инициализация YOLOv8s...")
    weights_path = os.path.join(base_dir, "models", "yolov8s.pt")
    model = YOLO(weights_path if os.path.exists(weights_path) else "yolov8s.pt")

    # Колбэк для вывода информации после каждой эпохи
    model.add_callback("on_fit_epoch_end", on_fit_epoch_end)

    print("\n[СТАРТ] Начало обучения на 300 эпох (GPU)...\n")

    try:
        results = model.train(
            data=data_yaml,
            epochs=300,
            imgsz=864,
            batch=32,
            device=0,             # GPU 0
            workers=8,
            project=os.path.join(base_dir, "logs", "train"),
            name='yolo_training',
            exist_ok=True,
            verbose=True,
            save=True,
            plots=True,
            amp=True,             # Смешанная точность для ускорения на GPU
            # mixup=0.0,          # Отключаем mixup (создает "призраков")
            # copy_paste=0.0,     # Отключаем copy_paste (нарушает количество предметов)
            # mosaic=1.0,         # Оставляем mosaic (стандарт для YOLO)
        )

        print("\n[ГОТОВО] Обучение завершено успешно!")
        print(f"  Результаты сохранены в: {os.path.join(base_dir, 'logs', 'train', 'yolo_training')}")

    except Exception as e:
        print(f"\n[ОШИБКА] При обучении: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()


