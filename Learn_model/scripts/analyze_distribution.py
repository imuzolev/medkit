import os
from collections import Counter
import glob

def analyze_distribution(label_dir):
    class_counts = Counter()
    label_files = glob.glob(os.path.join(label_dir, "*.txt"))
    
    print(f"Found {len(label_files)} label files in {label_dir}")
    
    for file_path in label_files:
        with open(file_path, 'r') as f:
            lines = f.readlines()
            for line in lines:
                try:
                    class_id = int(line.split()[0])
                    class_counts[class_id] += 1
                except (ValueError, IndexError):
                    pass
    
    return class_counts

if __name__ == "__main__":
    train_labels = "data/raw/train/labels"
    if os.path.exists(train_labels):
        counts = analyze_distribution(train_labels)
        print("\nClass Distribution:")
        for cls, count in sorted(counts.items()):
            print(f"Class {cls}: {count}")
    else:
        print(f"Directory {train_labels} not found.")
