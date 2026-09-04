"""
check_new_images.py
---------------------
Kiểm tra thư mục ảnh mới (VD: 85 ảnh bạn mới chụp/thu thập) TRƯỚC khi gộp
vào dataset chính, để chắc chắn:
  1. Ảnh nào đã có nhãn (.txt YOLO), ảnh nào chưa.
  2. Nếu đã có nhãn: các mã lớp trong đó có khớp với data.yaml không,
     và có đúng là đang bổ sung cho các lớp đang thiếu mẫu không.

Cấu trúc thư mục mong đợi (đặt 85 ảnh + nhãn vào đây trước):

    new_data/
      images/   <- các file .jpg/.png
      labels/   <- các file .txt cùng tên (nếu đã gán nhãn), theo format YOLO:
                   <class_id> <x_center> <y_center> <w> <h>  (đã chuẩn hoá 0-1)

Chạy:
    python check_new_images.py
    python check_new_images.py --new-dir duong/dan/khac --data data/data.yaml
"""

import argparse
from collections import Counter
from pathlib import Path

import yaml

IMG_EXTS = {".jpg", ".jpeg", ".png", ".bmp"}


def load_class_names(yaml_path: Path):
    with open(yaml_path, "r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)
    names = cfg["names"]
    if isinstance(names, list):
        names = {i: n for i, n in enumerate(names)}
    return {int(k): v for k, v in names.items()}


def main():
    ap = argparse.ArgumentParser(description="Kiểm tra ảnh mới trước khi gộp vào dataset")
    ap.add_argument("--new-dir", type=str, default="new_data",
                     help="Thư mục chứa ảnh mới, có 2 thư mục con images/ và labels/")
    ap.add_argument("--data", type=str, default="data/data.yaml")
    ap.add_argument("--min-samples", type=int, default=30,
                     help="Ngưỡng để coi 1 lớp là 'đang thiếu mẫu' (khớp với count_samples.py)")
    args = ap.parse_args()

    new_dir = Path(args.new_dir)
    img_dir = new_dir / "images"
    lbl_dir = new_dir / "labels"

    if not img_dir.exists():
        raise SystemExit(
            f"Không tìm thấy {img_dir}.\n"
            f"Hãy tạo thư mục '{args.new_dir}/images' và bỏ 85 ảnh mới vào đó "
            f"(nếu đã có nhãn thì thêm '{args.new_dir}/labels' chứa các file .txt cùng tên)."
        )

    yaml_path = Path(args.data)
    names = load_class_names(yaml_path)

    images = sorted([p for p in img_dir.iterdir() if p.suffix.lower() in IMG_EXTS])
    if not images:
        raise SystemExit(f"Thư mục {img_dir} không có ảnh nào (.jpg/.png).")

    labeled, unlabeled = [], []
    class_counts = Counter()
    invalid_class_ids = set()

    for img_path in images:
        lbl_path = lbl_dir / (img_path.stem + ".txt")
        if lbl_path.exists() and lbl_path.stat().st_size > 0:
            labeled.append(img_path.name)
            with open(lbl_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    parts = line.split()
                    cls_id = int(parts[0])
                    if cls_id in names:
                        class_counts[cls_id] += 1
                    else:
                        invalid_class_ids.add(cls_id)
        else:
            unlabeled.append(img_path.name)

    print(f"\n=== KIỂM TRA {len(images)} ẢNH TRONG '{args.new_dir}' ===")
    print(f"Đã gán nhãn : {len(labeled)}")
    print(f"CHƯA gán nhãn: {len(unlabeled)}")

    if unlabeled:
        print(f"\n⚠ {len(unlabeled)} ảnh chưa có nhãn — cần gán nhãn trước khi gộp vào dataset.")
        print("  Gợi ý công cụ gán nhãn miễn phí:")
        print("   - LabelImg (offline, xuất thẳng định dạng YOLO): https://github.com/HumanSignal/labelImg")
        print("   - Roboflow (online, dễ dùng, có thể xuất YOLOv8 trực tiếp): https://roboflow.com")
        for name in unlabeled[:10]:
            print(f"     - {name}")
        if len(unlabeled) > 10:
            print(f"     ... và {len(unlabeled) - 10} ảnh khác")

    if invalid_class_ids:
        print(f"\n❌ Có {len(invalid_class_ids)} class_id trong file nhãn KHÔNG khớp với data.yaml: {sorted(invalid_class_ids)}")
        print("   Kiểm tra lại — có thể bạn gán nhãn bằng tool khác, thứ tự lớp không trùng data.yaml.")

    if class_counts:
        print(f"\n=== 85 ẢNH MỚI ĐANG BỔ SUNG CHO CÁC LỚP SAU ===")
        print(f"{'Mã biển':<12}{'Số mẫu mới':>12}   So với ngưỡng {args.min_samples}")
        print("-" * 50)
        for cid, n in sorted(class_counts.items(), key=lambda x: -x[1]):
            code = names.get(cid, f"id={cid}")
            print(f"{code:<12}{n:>12}   (+{n} mẫu)")

        weak_targeted = set(names[cid] for cid in class_counts if cid in names)
        print(f"\nSố lớp được bổ sung: {len(weak_targeted)}")
        print("→ Sau khi gộp, chạy lại count_samples.py để xem lớp nào đã đủ 30 mẫu, lớp nào vẫn còn thiếu.")

    print("\n=== BƯỚC TIẾP THEO ===")
    if unlabeled:
        print("1. Gán nhãn cho các ảnh còn thiếu ở trên.")
    print("2. Chạy: python merge_new_data.py   (gộp ảnh+nhãn hợp lệ vào data/train)")
    print("3. Chạy: python finetune.py         (huấn luyện tiếp từ models/trained/best.pt)")


if __name__ == "__main__":
    main()