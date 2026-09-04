"""
merge_new_data.py
--------------------
Gộp ảnh + nhãn mới (đã gán nhãn, đã kiểm tra bằng check_new_images.py) vào
thẳng tập TRAIN của dataset chính — vì mục tiêu là bổ sung mẫu cho các lớp
đang thiếu, nên ưu tiên đưa hết vào train để model học được nhiều nhất.

(Không chia bớt vào val/test vì số lượng mẫu mới quá ít — chia nhỏ ra sẽ
làm val/test không đủ đại diện; giữ val/test hiện tại nguyên vẹn để so sánh
công bằng "trước / sau" khi đánh giá model.)

Chạy:
    python merge_new_data.py
    python merge_new_data.py --new-dir new_data --data-dir data
"""

import argparse
import shutil
from pathlib import Path

IMG_EXTS = {".jpg", ".jpeg", ".png", ".bmp"}


def main():
    ap = argparse.ArgumentParser(description="Gộp ảnh/nhãn mới vào data/train")
    ap.add_argument("--new-dir", type=str, default="new_data",
                     help="Thư mục chứa ảnh+nhãn mới (images/ và labels/ bên trong)")
    ap.add_argument("--data-dir", type=str, default="data",
                     help="Thư mục dataset chính (chứa train/val/test)")
    ap.add_argument("--prefix", type=str, default="new_",
                     help="Tiền tố thêm vào tên file để tránh trùng tên với ảnh cũ")
    args = ap.parse_args()

    new_dir = Path(args.new_dir)
    src_img_dir = new_dir / "images"
    src_lbl_dir = new_dir / "labels"

    train_img_dir = Path(args.data_dir) / "train" / "images"
    train_lbl_dir = Path(args.data_dir) / "train" / "labels"
    train_img_dir.mkdir(parents=True, exist_ok=True)
    train_lbl_dir.mkdir(parents=True, exist_ok=True)

    if not src_img_dir.exists():
        raise SystemExit(f"Không tìm thấy {src_img_dir}. Chạy check_new_images.py trước.")

    merged, skipped_no_label = 0, []

    for img_path in sorted(src_img_dir.iterdir()):
        if img_path.suffix.lower() not in IMG_EXTS:
            continue
        lbl_path = src_lbl_dir / (img_path.stem + ".txt")
        if not lbl_path.exists() or lbl_path.stat().st_size == 0:
            skipped_no_label.append(img_path.name)
            continue

        new_img_name = f"{args.prefix}{img_path.name}"
        new_lbl_name = f"{args.prefix}{img_path.stem}.txt"

        dest_img = train_img_dir / new_img_name
        dest_lbl = train_lbl_dir / new_lbl_name

        if dest_img.exists():
            print(f"⚠ Bỏ qua (đã tồn tại): {new_img_name}")
            continue

        shutil.copy2(img_path, dest_img)
        shutil.copy2(lbl_path, dest_lbl)
        merged += 1

    print(f"\n=== HOÀN TẤT GỘP DỮ LIỆU ===")
    print(f"Đã gộp vào train : {merged} ảnh (+ nhãn tương ứng)")
    print(f"Bỏ qua (chưa có nhãn): {len(skipped_no_label)}")
    if skipped_no_label:
        print("  → Các ảnh này KHÔNG được gộp, cần gán nhãn rồi chạy lại:")
        for name in skipped_no_label[:10]:
            print(f"     - {name}")

    print(f"\nThư mục train hiện tại: {train_img_dir}")
    print("Bước tiếp theo:")
    print("  1. Chạy lại: python count_samples.py   (để xem số mẫu mới đã cập nhật)")
    print("  2. Chạy:     python finetune.py          (huấn luyện tiếp từ model cũ)")


if __name__ == "__main__":
    main()