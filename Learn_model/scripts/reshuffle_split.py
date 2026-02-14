import os
import shutil
import random
import glob
from pathlib import Path

def reshuffle_and_split():
    # Исходные папки
    source_dirs = ['data/raw/train', 'data/raw/valid', 'data/raw/test']
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    # Новая папка для датасета
    target_dir = os.path.join(base_dir, 'data', 'reshuffled')
    
    # Создаем структуру
    for split in ['train', 'valid']:
        os.makedirs(os.path.join(target_dir, split, 'images'), exist_ok=True)
        os.makedirs(os.path.join(target_dir, split, 'labels'), exist_ok=True)
    
    # Сбор всех пар (картинка, лейбл)
    all_pairs = []
    
    print("Сбор файлов...")
    for s_dir in source_dirs:
        img_dir = os.path.join(base_dir, s_dir, 'images')
        lbl_dir = os.path.join(base_dir, s_dir, 'labels')
        
        # Поддерживаемые расширения
        images = []
        for ext in ['*.jpg', '*.jpeg', '*.png', '*.bmp']:
            images.extend(glob.glob(os.path.join(img_dir, ext)))
            
        for img_path in images:
            filename = os.path.basename(img_path)
            name_no_ext = os.path.splitext(filename)[0]
            
            # Ищем соответствующий лейбл
            lbl_path = os.path.join(lbl_dir, name_no_ext + '.txt')
            
            if os.path.exists(lbl_path):
                all_pairs.append((img_path, lbl_path))
            else:
                print(f"Внимание: нет лейбла для {filename}")

    total_images = len(all_pairs)
    print(f"Всего найдено пар изображений и лейблов: {total_images}")
    
    if total_images == 0:
        print("Ошибка: изображения не найдены!")
        return

    # Перемешиваем
    random.shuffle(all_pairs)
    
    # Разбиваем 80/20
    split_idx = int(total_images * 0.8)
    train_pairs = all_pairs[:split_idx]
    valid_pairs = all_pairs[split_idx:]
    
    print(f"Распределение: Train={len(train_pairs)}, Valid={len(valid_pairs)}")
    
    # Функция копирования
    def copy_files(pairs, split_name):
        print(f"Копирование файлов в {split_name}...")
        for img_src, lbl_src in pairs:
            fname = os.path.basename(img_src)
            lname = os.path.basename(lbl_src)
            
            shutil.copy2(img_src, os.path.join(target_dir, split_name, 'images', fname))
            shutil.copy2(lbl_src, os.path.join(target_dir, split_name, 'labels', lname))

    copy_files(train_pairs, 'train')
    copy_files(valid_pairs, 'valid')
    
    print(f"\nГотово! Новый датасет создан в: {target_dir}")

if __name__ == "__main__":
    reshuffle_and_split()
