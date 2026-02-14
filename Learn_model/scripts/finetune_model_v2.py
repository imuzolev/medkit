"""
finetune_model_v2.py — Скрипт дообучения модели (с чистого листа или last.pt)
Использует dataset_reshuffled.yaml и базовую модель yolov8n.pt.
"""

from ultralytics import YOLO

def main():
    # Загружаем базовую модель (pretrained COCO)
    # Если вы хотите продолжить старое обучение, используйте 'logs/train/yolo_finetune_reshuffled/weights/best.pt'
    # Но для чистоты эксперимента и исправления ошибок (bias) лучше начать с yolov8n.pt
    model = YOLO('models/yolov8n.pt')

    # Запускаем обучение
    results = model.train(
        data='configs/data_reshuffled.yaml',
        epochs=50,
        imgsz=640,
        batch=16,
        project='logs/train',
        name='yolo_retrain_english_3',
        device='0' # GPU 0, если доступен, иначе 'cpu'
    )

if __name__ == '__main__':
    main()
