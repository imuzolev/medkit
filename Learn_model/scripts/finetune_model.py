"""
Скрипт для дообучения (Fine-tuning) модели YOLOv8s на оригинальных данных.
Загружает веса из last.pt и продолжает обучение.
"""

import torch
from ultralytics import YOLO
import os
import sys


def calculate_score(metrics):
    """
    Вычисляет оценку от 0 до 100 на основе метрик модели.
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
    """
    print("\n" + "="*80)
    print(f"FINE-TUNING ЭПОХА {epoch}")
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
    Проверяет доступность GPU.
    """
    if not torch.cuda.is_available():
        print("\n[ОШИБКА] CUDA недоступна! Обучение возможно ТОЛЬКО на GPU.")
        sys.exit(1)

    gpu_name = torch.cuda.get_device_name(0)
    cuda_version = torch.version.cuda
    print(f"\n[GPU] Устройство: CUDA")
    print(f"  GPU: {gpu_name}")
    print(f"  CUDA версия: {cuda_version}")


def main():
    """Основная функция для Fine-tuning."""
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    check_gpu()

    # 1. Config for reshuffled data
    data_yaml = os.path.join(base_dir, "configs", "data_reshuffled.yaml")
    if not os.path.exists(data_yaml):
        print(f"[ОШИБКА] Файл data_reshuffled.yaml не найден!")
        return

    print(f"\n[ДАННЫЕ] Загрузка конфига: {data_yaml}")

    # 2. Load last weights (from original training to start fresh fine-tuning)
    weights_path = os.path.join(base_dir, "logs", "train", "yolo_training", "weights", "last.pt")
    if not os.path.exists(weights_path):
        print(f"[ОШИБКА] Веса не найдены: {weights_path}")
        return

    print(f"\n[МОДЕЛЬ] Загрузка весов из: {weights_path}")
    model = YOLO(weights_path)

    model.add_callback("on_fit_epoch_end", on_fit_epoch_end)

    print("\n[СТАРТ] Запуск Fine-tuning на 100 эпох (RESHUFFLED DATA)...")
    print("  - Заморозка backbone (freeze=10)")
    print("  - Мягкая аугментация")
    print("  - Данные переразбиты 80/20")
    
    try:
        results = model.train(
            data=data_yaml,
            epochs=100,
            imgsz=864,
            batch=32,
            device=0,
            workers=8,
            project=os.path.join(base_dir, "logs", "train"),
            name='yolo_finetune_reshuffled',
            exist_ok=True,
            verbose=True,
            save=True,
            plots=True,
            amp=True,
            
            # Freeze backbone layers
            freeze=10,
            
            # Hyperparameters
            lr0=0.001,
            lrf=0.01,
            warmup_epochs=3.0,
            
            # Augmentations (Mild)
            mosaic=0.0,
            mixup=0.0,
            copy_paste=0.0,
            
            degrees=10.0,
            translate=0.1,
            scale=0.5,
            fliplr=0.5,
            hsv_h=0.015,
            hsv_s=0.7,
            hsv_v=0.4,
        )

        print("\n[ГОТОВО] Fine-tuning завершен!")
        print(f"  Результаты: {os.path.join(base_dir, 'logs', 'train', 'yolo_finetune_reshuffled')}")

    except Exception as e:
        print(f"\n[ОШИБКА] При обучении: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
