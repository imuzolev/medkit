import os
import shutil
import cv2
import numpy as np
import albumentations as A
from tqdm import tqdm
import glob
import random
from collections import Counter, defaultdict
import yaml

# Constants
TARGET_COUNT = 1000
INPUT_DIR = "data/raw/train"
OUTPUT_DIR = "data/augmented"
VALID_DIR = "data/raw/valid"
TEST_DIR = "data/raw/test"

def load_data_yaml(path="configs/data.yaml"):
    with open(path, 'r') as f:
        return yaml.safe_load(f)

def get_class_distribution(label_dir):
    class_counts = Counter()
    image_classes = defaultdict(set)
    label_files = glob.glob(os.path.join(label_dir, "*.txt"))
    
    for file_path in label_files:
        filename = os.path.basename(file_path)
        image_name = filename.replace('.txt', '.jpg') # Assuming jpg
        # Verify image exists with other extensions if needed, but robust for now
        
        with open(file_path, 'r') as f:
            lines = f.readlines()
            for line in lines:
                parts = line.strip().split()
                if not parts: continue
                class_id = int(parts[0])
                class_counts[class_id] += 1
                image_classes[filename].add(class_id)
                
    return class_counts, image_classes

def get_augmentation_pipeline():
    # Geometric - SAFE, preserves object identity and quality
    geometric = A.Compose([
        A.HorizontalFlip(p=0.5),
        A.VerticalFlip(p=0.5),
        A.Rotate(limit=15, p=0.5), # Reduced limit slightly
        A.RandomScale(scale_limit=0.15, p=0.5), # Reduced scale limit
        A.Perspective(scale=(0.02, 0.05), p=0.3), # Reduced perspective distortion
        A.Affine(shear=(-5, 5), p=0.3) # Reduced shear
    ])
    
    # Color/Noise - REDUCED significantly to keep images clean
    color_noise = A.Compose([
        A.RandomBrightnessContrast(brightness_limit=0.1, contrast_limit=0.1, p=0.3), # Very mild
        # Removed GaussNoise
        # Removed Blur
        A.CLAHE(clip_limit=2.0, tile_grid_size=(8, 8), p=0.2), # Mild contrast enhancement
        A.HueSaturationValue(hue_shift_limit=10, sat_shift_limit=15, val_shift_limit=10, p=0.3), # Mild color shift
    ])
    
    # Removed Weather augmentations (SunFlare, Fog) as they destroy quality

    # Combine
    return A.Compose([
        geometric,
        color_noise,
    ], bbox_params=A.BboxParams(format='yolo', min_visibility=0.3, label_fields=['class_labels']))

def process_train(input_dir, output_dir, pipeline):
    images_dir = os.path.join(input_dir, "images")
    labels_dir = os.path.join(input_dir, "labels")
    
    out_images_dir = os.path.join(output_dir, "train", "images")
    out_labels_dir = os.path.join(output_dir, "train", "labels")
    
    os.makedirs(out_images_dir, exist_ok=True)
    os.makedirs(out_labels_dir, exist_ok=True)
    
    print("Analyzing class distribution...")
    class_counts, image_classes = get_class_distribution(labels_dir)
    
    print("Class counts:", dict(sorted(class_counts.items())))
    
    # Calculate augmentation factors per class
    class_factors = {}
    for cls, count in class_counts.items():
        if count == 0:
            class_factors[cls] = 1
        else:
            class_factors[cls] = max(1, TARGET_COUNT / count)
            
    print("Augmentation factors:", {k: f"{v:.2f}" for k, v in sorted(class_factors.items())})
    
    label_files = glob.glob(os.path.join(labels_dir, "*.txt"))
    
    for label_file in tqdm(label_files, desc="Augmenting images"):
        base_name = os.path.basename(label_file)
        name_no_ext = os.path.splitext(base_name)[0]
        
        # Find corresponding image
        image_file = None
        for ext in ['.jpg', '.jpeg', '.png', '.bmp']:
            p = os.path.join(images_dir, name_no_ext + ext)
            if os.path.exists(p):
                image_file = p
                break
        
        if not image_file:
            continue
            
        # Determine number of augmentations for this image
        # Strategy: Max factor among classes present in this image
        classes_in_img = image_classes[base_name]
        if not classes_in_img:
            num_augments = 0 # No labels, just copy original? or 0? Let's copy original once.
            max_factor = 1.0
        else:
            max_factor = max(class_factors.get(c, 1.0) for c in classes_in_img)
        
        # We always keep the original
        num_new_copies = int(round(max_factor)) - 1
        if num_new_copies < 0: num_new_copies = 0
        
        # Read image
        image = cv2.imread(image_file)
        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        h, w, _ = image.shape
        
        # Read labels
        bboxes = []
        class_labels = []
        with open(label_file, 'r') as f:
            for line in f:
                parts = line.strip().split()
                cls_id = int(parts[0])
                # yolo: x_center, y_center, width, height
                coords = [float(x) for x in parts[1:]]
                # Ensure strictly 4 coordinates (some formats might have confidence)
                if len(coords) > 4:
                    coords = coords[:4]
                if len(coords) == 4:
                    # Clip coordinates to be within [0, 1] essentially
                    # But wait, albumentations validates validity.
                    # Let's clean the bbox.
                    xc, yc, w, h = coords
                    
                    # Ensure w and h are positive
                    w = max(0.0001, w)
                    h = max(0.0001, h)
                    
                    x1 = xc - w/2
                    y1 = yc - h/2
                    x2 = xc + w/2
                    y2 = yc + h/2
                    
                    x1 = max(0, min(1, x1))
                    y1 = max(0, min(1, y1))
                    x2 = max(0, min(1, x2))
                    y2 = max(0, min(1, y2))
                    
                    # Recompute yolo
                    new_w = x2 - x1
                    new_h = y2 - y1
                    new_xc = x1 + new_w/2
                    new_yc = y1 + new_h/2
                    
                    if new_w > 0 and new_h > 0:
                        bboxes.append([new_xc, new_yc, new_w, new_h])
                        class_labels.append(cls_id)
        
        if not bboxes:
             # Just copy original if no bboxes (augmentations might fail without bboxes if not handled)
             shutil.copy(image_file, os.path.join(out_images_dir, base_name.replace('.txt', '.jpg')))
             shutil.copy(label_file, os.path.join(out_labels_dir, base_name))
             continue

        # Save Original
        shutil.copy(image_file, os.path.join(out_images_dir, base_name.replace('.txt', '.jpg'))) # Normalize to jpg
        shutil.copy(label_file, os.path.join(out_labels_dir, base_name))
        
        # Generate augmentations
        for i in range(num_new_copies):
            try:
                transformed = pipeline(image=image, bboxes=bboxes, class_labels=class_labels)
                aug_image = transformed['image']
                aug_bboxes = transformed['bboxes']
                aug_labels = transformed['class_labels']
                
                # Check if image is valid (sometimes aug removes all bboxes if crop/visibility is bad)
                if len(aug_bboxes) == 0 and len(bboxes) > 0:
                    # If we lost all boxes, maybe skip saving this one or try again? 
                    # For simplicity, we skip empty augmented images if original wasn't empty
                    continue
                
                # Save Augmented
                aug_filename = f"{name_no_ext}_aug_{i}.jpg"
                aug_labelname = f"{name_no_ext}_aug_{i}.txt"
                
                # Convert back to BGR for opencv save
                aug_image_bgr = cv2.cvtColor(aug_image, cv2.COLOR_RGB2BGR)
                cv2.imwrite(os.path.join(out_images_dir, aug_filename), aug_image_bgr)
                
                with open(os.path.join(out_labels_dir, aug_labelname), 'w') as f:
                    for cls, bbox in zip(aug_labels, aug_bboxes):
                        # Clip to [0, 1] just in case
                        bbox = [min(max(x, 0.0), 1.0) for x in bbox]
                        line = f"{cls} {' '.join(map(str, bbox))}\n"
                        f.write(line)
                        
            except Exception as e:
                print(f"Error augmenting {base_name}: {e}")

def copy_folder(src, dst):
    if os.path.exists(dst):
        shutil.rmtree(dst)
    shutil.copytree(src, dst)

def main():
    # Setup Output Directories
    if os.path.exists(OUTPUT_DIR):
        shutil.rmtree(OUTPUT_DIR)
    os.makedirs(OUTPUT_DIR)
    
    # 1. Copy Valid and Test
    print("Copying valid and test sets...")
    copy_folder(VALID_DIR, os.path.join(OUTPUT_DIR, "valid"))
    copy_folder(TEST_DIR, os.path.join(OUTPUT_DIR, "test"))
    
    # 2. Augment Train
    print("Augmenting train set...")
    pipeline = get_augmentation_pipeline()
    process_train(INPUT_DIR, OUTPUT_DIR, pipeline)
    
    print("Done! Augmentation complete.")

if __name__ == "__main__":
    main()
