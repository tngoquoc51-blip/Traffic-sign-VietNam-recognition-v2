"""
count_samples.py
------------------
Đếm số lượng mẫu dữ liệu hiện có cho từng loại biển báo, dựa theo
data/data.yaml và các file nhãn (.txt) trong thư mục labels/.

Cách chạy (đứng ở thư mục gốc project, cùng cấp với thư mục "data/"):

    python count_samples.py

Nếu file data.yaml của bạn nằm chỗ khác, chạy:

    python count_samples.py --data path/to/data.yaml

Kết quả in ra:
  - Tổng số ảnh và tổng số nhãn (bounding box) theo từng tập train/val/test
  - Số lượng mẫu (bounding box) theo TỪNG LỚP biển báo, sắp xếp từ ÍT -> NHIỀU
  - Cảnh báo các lớp có quá ít mẫu (mặc định < 30) — nên bổ sung thêm ảnh
    cho các lớp này trước khi huấn luyện tiếp, nếu không model sẽ học kém
    hẳn ở những lớp đó.
"""

import argparse
from collections import Counter
from pathlib import Path

import yaml

IMG_EXTS = {".jpg", ".jpeg", ".png", ".bmp"}


def load_data_yaml(yaml_path: Path):
    with open(yaml_path, "r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)
    return cfg


def resolve_split_dirs(cfg: dict, yaml_path: Path):
    """
    Xác định thư mục images/labels cho từng split (train/val/test) dựa theo
    nội dung data.yaml. Hỗ trợ cả 2 kiểu cấu trúc phổ biến:
      1) path + train/val/test trỏ tới thư mục images/<split>
      2) train/val/test trỏ thẳng tới thư mục ảnh (không có "path")
    """
    base = yaml_path.parent
    if cfg.get("path"):
        base = (yaml_path.parent / cfg["path"]).resolve()

    splits = {}
    for split in ("train", "val", "test"):
        rel = cfg.get(split)
        if not rel:
            continue
        img_dir = (base / rel).resolve()
        # Thư mục labels thường nằm song song, thay "images" bằng "labels"
        label_dir = Path(str(img_dir).replace("images", "labels"))
        splits[split] = (img_dir, label_dir)
    return splits


def count_split(img_dir: Path, label_dir: Path, num_classes: int):
    class_counts = Counter()
    num_images = 0
    num_labels_files = 0
    num_boxes = 0
    images_without_label = []

    if not img_dir.exists():
        return None

    for img_path in sorted(img_dir.iterdir()):
        if img_path.suffix.lower() not in IMG_EXTS:
            continue
        num_images += 1
        lbl_path = label_dir / (img_path.stem + ".txt")
        if not lbl_path.exists():
            images_without_label.append(img_path.name)
            continue
        num_labels_files += 1
        with open(lbl_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                cls_id = int(line.split()[0])
                if 0 <= cls_id < num_classes:
                    class_counts[cls_id] += 1
                num_boxes += 1

    return {
        "num_images": num_images,
        "num_labels_files": num_labels_files,
        "num_boxes": num_boxes,
        "class_counts": class_counts,
        "images_without_label": images_without_label,
    }


def main():
    ap = argparse.ArgumentParser(description="Đếm số mẫu dữ liệu theo từng lớp biển báo")
    ap.add_argument("--data", type=str, default="data/data.yaml")
    ap.add_argument("--min-samples", type=int, default=30,
                     help="Ngưỡng cảnh báo: lớp có ít hơn số này bị coi là thiếu dữ liệu")
    args = ap.parse_args()

    yaml_path = Path(args.data)
    if not yaml_path.exists():
        raise SystemExit(f"Không tìm thấy {yaml_path}. Dùng --data để chỉ đúng đường dẫn.")

    cfg = load_data_yaml(yaml_path)
    names = cfg["names"]
    if isinstance(names, list):
        names = {i: n for i, n in enumerate(names)}
    num_classes = len(names)

    splits = resolve_split_dirs(cfg, yaml_path)
    if not splits:
        raise SystemExit("Không đọc được train/val/test từ data.yaml.")

    total_counts = Counter()
    print(f"\n=== TỔNG QUAN DATASET ({num_classes} lớp) ===")

    for split_name, (img_dir, label_dir) in splits.items():
        result = count_split(img_dir, label_dir, num_classes)
        if result is None:
            print(f"[{split_name}] KHÔNG TÌM THẤY thư mục ảnh: {img_dir}")
            continue

        total_counts.update(result["class_counts"])
        print(f"\n[{split_name}]  {img_dir}")
        print(f"  Số ảnh          : {result['num_images']}")
        print(f"  Số file nhãn    : {result['num_labels_files']}")
        print(f"  Tổng bounding box: {result['num_boxes']}")
        if result["images_without_label"]:
            print(f"  ⚠ {len(result['images_without_label'])} ảnh KHÔNG có file nhãn tương ứng, ví dụ:")
            for name in result["images_without_label"][:5]:
                print(f"     - {name}")

    print(f"\n=== SỐ MẪU (bounding box) THEO TỪNG LỚP — toàn bộ train+val+test ===")
    print(f"{'Mã biển':<12}{'Số mẫu':>10}   Trạng thái")
    print("-" * 45)

    rows = []
    for cid, code in names.items():
        n = total_counts.get(int(cid), 0)
        rows.append((code, n))

    rows.sort(key=lambda x: x[1])  # ít -> nhiều, để thấy ngay lớp nào thiếu

    zero_classes = []
    low_classes = []
    for code, n in rows:
        if n == 0:
            status = "❌ CHƯA CÓ MẪU NÀO"
            zero_classes.append(code)
        elif n < args.min_samples:
            status = f"⚠ Ít hơn {args.min_samples} — nên bổ sung"
            low_classes.append(code)
        else:
            status = "✓ Đủ dùng"
        print(f"{code:<12}{n:>10}   {status}")

    print("\n=== TÓM TẮT ===")
    print(f"Tổng số lớp             : {num_classes}")
    print(f"Lớp chưa có mẫu nào      : {len(zero_classes)}  {zero_classes if zero_classes else ''}")
    print(f"Lớp có ít mẫu (< {args.min_samples})   : {len(low_classes)}")
    print(f"Tổng bounding box toàn bộ: {sum(total_counts.values())}")


if __name__ == "__main__":
    main()