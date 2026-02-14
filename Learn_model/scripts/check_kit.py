"""
check_kit.py — Medical Kit Inspection (English Version).

Logic:
  - Low confidence detection with TTA.
  - Two-tier filtering (High conf > Low conf).
  - Bandage classification based on area size.
  - Hallucination filter (max box size).
"""

import os
import sys
import cv2
import numpy as np
from collections import Counter
from ultralytics import YOLO

# ========================= SETTINGS =========================

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

WEIGHTS_DIR = os.path.join(BASE_DIR, 'logs', 'train', 'yolo_retrain_english_3', 'weights')
MODEL_PATH = os.path.join(WEIGHTS_DIR, 'best.pt')
if not os.path.exists(MODEL_PATH):
    MODEL_PATH = os.path.join(WEIGHTS_DIR, 'last.pt')

INPUT_DIR  = os.path.join(BASE_DIR, 'inference', 'input')
OUTPUT_DIR = os.path.join(BASE_DIR, 'inference', 'output')
REPORT_FILE = os.path.join(OUTPUT_DIR, 'report.txt')

IMG_SIZE = 1280
IMAGE_EXTENSIONS = ('.png', '.jpg', '.jpeg', '.bmp', '.webp')

# Thresholds
LOW_CONF  = 0.05   # Minimum confidence to consider (Tier 2 floor — nothing below 5%)
HIGH_CONF = 0.25   # High confidence threshold (Tier 1)

# Hallucination filter (max box area ratio)
MAX_BOX_AREA_RATIO = 0.85

# Bandage size gap threshold (area ratio between consecutive items)
# Must be >= 2.0 to confirm a real Large/Small boundary
BANDAGE_GAP_THRESHOLD = 2.0

# ============ REQUIRED ITEMS ============
REQUIRED_ITEMS = {
    'Large bandage':                3,
    'small bandage':                3,
    'wipes':                        2,
    'Adhesive plaster':             1,
    'Artificial respiration device': 2,
    'Instruction leaflet':          1,
    'pencil':                       1,
    'Thermal blanket':              1,
    'Medical mask':                 1,
    'Gloves':                       1,
    'Scissors':                     1,
    'Notepad':                      1,
    'Tourniquet':                   1,
}

# Colors (BGR)
CLASS_COLORS = {
    'Large bandage':                (0, 0, 200),
    'small bandage':                (0, 140, 255),
    'wipes':                        (0, 200, 0),
    'Adhesive plaster':             (255, 0, 0),
    'Artificial respiration device': (200, 200, 0),
    'Instruction leaflet':          (200, 0, 200),
    'pencil':                       (0, 255, 255),
    'Thermal blanket':              (255, 0, 128),
    'Medical mask':                 (128, 128, 0),
    'Gloves':                       (0, 128, 128),
    'Scissors':                     (128, 0, 128),
    'Notepad':                      (128, 128, 128),
    'Tourniquet':                   (0, 200, 200),
}

# ========================= CLASSES =========================

class DetectedObject:
    def __init__(self, cls_name: str, conf: float, box: np.ndarray):
        self.cls_name = cls_name
        self.conf = conf
        self.box = box  # [x1, y1, x2, y2]

    @property
    def area(self) -> float:
        return float((self.box[2] - self.box[0]) * (self.box[3] - self.box[1]))


# ========================= FUNCTIONS =========================

def load_model() -> YOLO:
    if not os.path.exists(MODEL_PATH):
        print(f"[ERROR] Weights not found: {MODEL_PATH}")
        sys.exit(1)
    print(f"[INFO] Model: {MODEL_PATH}")
    return YOLO(MODEL_PATH)


def get_image_files() -> list:
    if not os.path.isdir(INPUT_DIR):
        os.makedirs(INPUT_DIR, exist_ok=True)
        return []
    files = sorted(f for f in os.listdir(INPUT_DIR) if f.lower().endswith(IMAGE_EXTENSIONS))
    if not files:
        print(f"[WARNING] No images found in {INPUT_DIR}")
    return files


def raw_detect(model: YOLO, img_path: str, img_area: float) -> list:
    results = model.predict(
        img_path,
        conf=LOW_CONF,
        iou=0.5,
        imgsz=IMG_SIZE,
        augment=True,
        verbose=False,
    )[0]

    relevant_classes = set(REQUIRED_ITEMS.keys())
    objects = []

    for box in results.boxes:
        cls_id = int(box.cls[0])
        cls_name = model.names[cls_id]
        conf = float(box.conf[0])
        xyxy = box.xyxy[0].cpu().numpy()

        if cls_name not in relevant_classes:
            continue

        obj = DetectedObject(cls_name, conf, xyxy)

        # Filter hallucinations (too large)
        if obj.area > img_area * MAX_BOX_AREA_RATIO:
            continue

        objects.append(obj)

    return objects


def classify_bandages(bandages: list) -> list:
    """Classify bandages into Large/Small with strict rules:
    - Only accept bandage detections with conf >= HIGH_CONF.
    - Split by area gap ONLY when there is a clear size difference (ratio >= 2.0).
    - Rebalance ONLY when the gap-split confirmed both types exist.
    - If no gap found — trust the model's original predictions as-is.
    - Strict cap: never more than 3 Large + 3 Small.
    """
    if not bandages:
        return []

    # 0. STRICT: Only trust bandage detections with HIGH confidence.
    bandages = [b for b in bandages if b.conf >= HIGH_CONF]
    if not bandages:
        return []

    # 1. Sort by Area Descending (for gap detection)
    bandages.sort(key=lambda x: x.area, reverse=True)

    # 2. Find the biggest area ratio gap between consecutive items
    areas = [b.area for b in bandages]
    max_gap = 0.0
    split_idx = -1
    gap_confirmed = False  # Did we find a real Large/Small boundary?

    if len(bandages) > 1:
        for i in range(len(areas) - 1):
            denom = areas[i + 1] if areas[i + 1] > 0 else 1e-6
            ratio = areas[i] / denom
            if ratio > max_gap:
                max_gap = ratio
                split_idx = i

    # 3. Classification logic
    if max_gap >= BANDAGE_GAP_THRESHOLD:
        # A real size gap was found — reclassify based on area
        gap_confirmed = True
        for i, b in enumerate(bandages):
            b.cls_name = 'Large bandage' if i <= split_idx else 'small bandage'
    else:
        # No significant gap — all bandages are roughly the same physical size.
        # Use majority voting to decide the single type.
        # If tied, compare average area: larger → Large bandage.
        votes_large = sum(1 for b in bandages if 'Large' in b.cls_name)
        votes_small = len(bandages) - votes_large

        if votes_large > votes_small:
            winner = 'Large bandage'
        elif votes_small > votes_large:
            winner = 'small bandage'
        else:
            # Tied — use average area as tiebreaker
            avg_large = np.mean([b.area for b in bandages if 'Large' in b.cls_name]) if votes_large > 0 else 0
            avg_small = np.mean([b.area for b in bandages if 'small' in b.cls_name]) if votes_small > 0 else 0
            winner = 'Large bandage' if avg_large >= avg_small else 'small bandage'

        for b in bandages:
            b.cls_name = winner

    # 4. Rebalancing — ONLY if gap-split confirmed both types.
    #    If no gap was found, we trust the model: if it says all are Large,
    #    they ARE all Large. We don't invent Small bandages that aren't there.
    large_group = [b for b in bandages if 'Large' in b.cls_name]
    small_group = [b for b in bandages if 'small' in b.cls_name]

    if gap_confirmed:
        # Gap split may have created an imbalance (e.g. 5 Large + 1 Small).
        # Rebalance borderline items by moving them across the boundary.
        large_group.sort(key=lambda x: x.area, reverse=True)
        small_group.sort(key=lambda x: x.area, reverse=True)

        while len(large_group) > 3 and len(small_group) < 3:
            item = large_group.pop()  # smallest Large → becomes Small
            item.cls_name = 'small bandage'
            small_group.insert(0, item)

        while len(small_group) > 3 and len(large_group) < 3:
            item = small_group.pop(0)  # largest Small → becomes Large
            item.cls_name = 'Large bandage'
            large_group.append(item)

    # 5. Strict cap: max 3 of each, keep highest confidence
    large_group.sort(key=lambda x: x.conf, reverse=True)
    small_group.sort(key=lambda x: x.conf, reverse=True)

    return large_group[:3] + small_group[:3]


def two_tier_filter(objects: list) -> list:
    grouped: dict[str, list] = {}
    for obj in objects:
        grouped.setdefault(obj.cls_name, []).append(obj)

    result = []

    for cls_name, limit in REQUIRED_ITEMS.items():
        if 'bandage' in cls_name.lower():
            continue

        candidates = grouped.get(cls_name, [])
        candidates.sort(key=lambda x: x.conf, reverse=True)

        # Tier 1: High confidence
        high = [o for o in candidates if o.conf >= HIGH_CONF][:limit]
        selected = list(high)

        # Tier 2: Fill gaps with Low confidence
        remaining = limit - len(selected)
        if remaining > 0:
            low = [o for o in candidates if o.conf < HIGH_CONF][:remaining]
            selected.extend(low)

        result.extend(selected)

    return result


def filter_detections(raw_objects: list) -> list:
    bandages = [o for o in raw_objects if 'bandage' in o.cls_name.lower()]
    others   = [o for o in raw_objects if 'bandage' not in o.cls_name.lower()]

    filtered_bandages = classify_bandages(bandages)
    filtered_others   = two_tier_filter(others)

    return filtered_bandages + filtered_others


def draw_results(img_path: str, objects: list, save_path: str):
    img = cv2.imread(img_path)
    if img is None:
        return

    for obj in objects:
        x1, y1, x2, y2 = map(int, obj.box)
        color = CLASS_COLORS.get(obj.cls_name, (255, 255, 255))
        label = f"{obj.cls_name} {obj.conf:.2f}"

        cv2.rectangle(img, (x1, y1), (x2, y2), color, 3)

        (tw, th), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.7, 2)
        cv2.rectangle(img, (x1, max(y1 - th - 10, 0)), (x1 + tw, y1), color, -1)
        cv2.putText(img, label, (x1, max(y1 - 5, th + 5)),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

    cv2.imwrite(save_path, img)


# English -> Russian name mapping for report
ITEM_NAME_RU = {
    'Large bandage':                'Бинт большой',
    'small bandage':                'Бинт малый',
    'wipes':                        'Салфетки',
    'Adhesive plaster':             'Лейкопластырь',
    'Artificial respiration device': 'Устройство для ИВЛ',
    'Instruction leaflet':          'Инструкция',
    'pencil':                       'Карандаш',
    'Thermal blanket':              'Термоодеяло',
    'Medical mask':                 'Медицинская маска',
    'Gloves':                       'Перчатки',
    'Scissors':                     'Ножницы',
    'Notepad':                      'Блокнот',
    'Tourniquet':                   'Жгут',
}


def build_report_entry(img_name: str, found: Counter) -> str:
    missing = []
    for item, req in REQUIRED_ITEMS.items():
        curr = found.get(item, 0)
        ru_name = ITEM_NAME_RU.get(item, item)
        if curr < req:
            missing.append(f"{ru_name} — не хватает {req - curr} шт.")

    if not missing:
        status = "СТАТУС: КОМПЛЕКТ ПОЛНЫЙ"
    else:
        status = "СТАТУС: НЕКОМПЛЕКТ! Отсутствует:\n  " + "\n  ".join(missing)

    return f"Файл: {img_name}\n{status}\n" + "-" * 40


# ========================= MAIN =========================

def check_kit():
    model = load_model()
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    image_files = get_image_files()
    if not image_files:
        return
    print(f"[INFO] Images found: {len(image_files)}\n")

    report_lines = []
    complete_count = 0

    for idx, img_name in enumerate(image_files, 1):
        img_path = os.path.join(INPUT_DIR, img_name)
        print(f"[{idx}/{len(image_files)}] {img_name} ... ", end="")

        img = cv2.imread(img_path)
        if img is None:
            print("READ ERROR")
            continue
        img_area = img.shape[0] * img.shape[1]

        raw_objects = raw_detect(model, img_path, img_area)
        filtered = filter_detections(raw_objects)
        found = Counter(o.cls_name for o in filtered)
        
        entry = build_report_entry(img_name, found)
        report_lines.append(entry)

        if "STATUS: COMPLETE" in entry:
            complete_count += 1
            print("OK")
        else:
            print("INCOMPLETE")

        # Detailed log: show detected items with confidence
        for obj in sorted(filtered, key=lambda x: x.conf, reverse=True):
            print(f"    {obj.cls_name:30s}  conf={obj.conf:.3f}  area={obj.area:.0f}")
        # Show what's missing
        for item, req in REQUIRED_ITEMS.items():
            curr = found.get(item, 0)
            if curr < req:
                print(f"    [MISSING] {item} ({req - curr} of {req})")
        print()

        draw_results(img_path, filtered, os.path.join(OUTPUT_DIR, img_name))

    with open(REPORT_FILE, 'w', encoding='utf-8') as f:
        f.write("\n".join(report_lines) + "\n")

    print(f"\n[DONE] Complete: {complete_count}, Incomplete: {len(image_files) - complete_count}")
    print(f"Report: {REPORT_FILE}")


if __name__ == "__main__":
    check_kit()
