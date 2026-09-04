"""
Module tiền xử lý dữ liệu: resize ảnh, chia tập train/val/test.

Giả định cấu trúc đầu vào (trước khi chia):
  data/raw/images/*.jpg
  data/raw/labels/*.txt   (nhãn định dạng YOLO: class_id x_center y_center width height)

Sau khi chạy script này, dữ liệu sẽ được chia và copy vào:
  data/train/images, data/train/labels
  data/val/images,   data/val/labels
  data/test/images,  data/test/labels
"""

import os
import shutil
import random
from pathlib import Path

import config

RAW_IMAGES_DIR = os.path.join(config.ROOT_DIR, "data", "raw", "images")
RAW_LABELS_DIR = os.path.join(config.ROOT_DIR, "data", "raw", "labels")

TRAIN_RATIO = 0.7
VAL_RATIO = 0.2
TEST_RATIO = 0.1


def split_dataset(seed: int = 42):
    """Chia dữ liệu thô thành train/val/test và copy vào đúng thư mục."""
    random.seed(seed)

    if not os.path.isdir(RAW_IMAGES_DIR):
        print(f"Không tìm thấy thư mục ảnh gốc: {RAW_IMAGES_DIR}")
        print("Hãy đặt ảnh vào data/raw/images/ và nhãn vào data/raw/labels/ trước.")
        return

    image_files = [
        f for f in os.listdir(RAW_IMAGES_DIR)
        if f.lower().endswith((".jpg", ".jpeg", ".png"))
    ]
    random.shuffle(image_files)

    n_total = len(image_files)
    n_train = int(n_total * TRAIN_RATIO)
    n_val = int(n_total * VAL_RATIO)

    splits = {
        "train": image_files[:n_train],
        "val": image_files[n_train:n_train + n_val],
        "test": image_files[n_train + n_val:],
    }

    for split_name, files in splits.items():
        img_out_dir = os.path.join(config.ROOT_DIR, "data", split_name, "images")
        lbl_out_dir = os.path.join(config.ROOT_DIR, "data", split_name, "labels")
        os.makedirs(img_out_dir, exist_ok=True)
        os.makedirs(lbl_out_dir, exist_ok=True)

        for img_name in files:
            label_name = Path(img_name).stem + ".txt"

            src_img = os.path.join(RAW_IMAGES_DIR, img_name)
            src_lbl = os.path.join(RAW_LABELS_DIR, label_name)

            shutil.copy2(src_img, os.path.join(img_out_dir, img_name))

            if os.path.exists(src_lbl):
                shutil.copy2(src_lbl, os.path.join(lbl_out_dir, label_name))
            else:
                print(f"Cảnh báo: không tìm thấy nhãn cho {img_name}")

        print(f"{split_name}: {len(files)} ảnh")

    print("Chia dữ liệu hoàn tất.")


if __name__ == "__main__":
    split_dataset()
