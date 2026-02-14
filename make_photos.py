"""
Extract frames every 2 seconds from each video in the script root folder
and save them into the photo directory.
"""

import os
import cv2


VIDEO_EXTENSIONS = (".mp4", ".mov", ".avi", ".mkv", ".flv", ".wmv", ".webm")
INTERVAL_SEC = 2


def extract_frames(video_path: str, output_dir: str, interval_sec: int = INTERVAL_SEC) -> None:
    name = os.path.splitext(os.path.basename(video_path))[0]
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise RuntimeError(f"Cannot open video: {video_path}")

    fps = cap.get(cv2.CAP_PROP_FPS) or 0
    frame_count = cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0
    duration_sec = int(frame_count / fps) if fps else 0

    os.makedirs(output_dir, exist_ok=True)

    for second in range(0, duration_sec + 1, interval_sec):
        # Seek by timestamp in milliseconds.
        cap.set(cv2.CAP_PROP_POS_MSEC, second * 1000)
        success, frame = cap.read()
        if not success:
            continue
        filename = f"{name}_{second:05d}.jpg"
        cv2.imwrite(os.path.join(output_dir, filename), frame)

    cap.release()


def main() -> None:
    # Корень = папка, где лежит этот скрипт
    root_dir = os.path.dirname(os.path.abspath(__file__))
    output_dir = os.path.join(root_dir, "photo")

    # Обрабатываем все видео из корня по очереди (стабильный порядок)
    videos = sorted([f for f in os.listdir(root_dir) if f.lower().endswith(VIDEO_EXTENSIONS)])
    if not videos:
        raise SystemExit("No video files found in the root directory.")

    for video in videos:
        extract_frames(os.path.join(root_dir, video), output_dir, interval_sec=INTERVAL_SEC)


if __name__ == "__main__":
    main()



