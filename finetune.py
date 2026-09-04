"""
finetune.py
-------------
Huấn luyện TIẾP từ model đã train (models/trained/best.pt) với dữ liệu đã
gộp thêm — KHÔNG train lại từ đầu (from scratch), để tận dụng toàn bộ những
gì model đã học được từ 5.894 mẫu cũ, chỉ "học thêm" trên dữ liệu mới.

Vì sao dùng finetune.py thay vì train.py cho lần này:
  - train.py (huấn luyện từ đầu) phù hợp khi bạn có dataset lớn, ổn định.
  - finetune.py phù hợp khi bạn CHỈ bổ sung thêm một lượng nhỏ ảnh (85 ảnh)
    cho các lớp đang thiếu — học ít epoch hơn, tốc độ học (learning rate)
    thấp hơn, để tránh "quên" những gì model đã học tốt ở các lớp nhiều dữ
    liệu (P.127, P.130, P.131a...).

⚠ LƯU Ý QUAN TRỌNG VỀ QUY MÔ DỮ LIỆU:
  85 ảnh mới chia cho 27 lớp đang thiếu ~ trung bình 3 ảnh/lớp. Con số này
  RẤT ít — sau khi fine-tune, các lớp cực hiếm (1-5 mẫu cũ) nhiều khả năng
  vẫn chưa đạt độ chính xác cao. Đây không phải lỗi script, mà là giới hạn
  thực tế của dữ liệu — nên nói rõ điều này trong phần "Hạn chế và hướng
  phát triển" của báo cáo đồ án, kèm đề xuất thu thập thêm ảnh cho các lớp
  đó (mục tiêu tối thiểu ~30-50 ảnh/lớp).

Chạy:
    python finetune.py
    python finetune.py --epochs 40 --lr0 0.001
"""

import argparse
from pathlib import Path

from ultralytics import YOLO

import config  # src/config.py — sửa đường dẫn import nếu file này không nằm cùng cấp src/


def main():
    ap = argparse.ArgumentParser(description="Fine-tune model biển báo giao thông VN")
    ap.add_argument("--weights", type=str, default=config.TRAINED_MODEL,
                     help="Model xuất phát để học tiếp (mặc định: models/trained/best.pt)")
    ap.add_argument("--data", type=str, default=config.DATA_YAML)
    ap.add_argument("--epochs", type=int, default=50,
                     help="Ít hơn train từ đầu (config.EPOCHS=100) vì chỉ học thêm, tránh overfit")
    ap.add_argument("--imgsz", type=int, default=config.IMG_SIZE)
    ap.add_argument("--batch", type=int, default=config.BATCH_SIZE)
    ap.add_argument("--lr0", type=float, default=0.0015,
                     help="Learning rate thấp hơn train từ đầu, để 'học thêm' nhẹ nhàng, không phá vỡ trọng số cũ")
    ap.add_argument("--patience", type=int, default=15)
    ap.add_argument("--device", type=str, default="0", help="'0' cho GPU, 'cpu' nếu không có GPU")
    args = ap.parse_args()

    if not Path(args.weights).exists():
        raise SystemExit(f"Không tìm thấy model tại {args.weights}.")

    print(f"Fine-tune từ: {args.weights}")
    print(f"Dữ liệu     : {args.data}")
    print(f"Epochs      : {args.epochs} (thấp hơn train từ đầu vì chỉ học thêm)")

    model = YOLO(args.weights)

    model.train(
        data=args.data,
        epochs=args.epochs,
        imgsz=args.imgsz,
        batch=args.batch,
        lr0=args.lr0,
        patience=args.patience,
        device=args.device,

        # Augmentation — giữ nguyên nguyên tắc như train.py gốc:
        # KHÔNG lật ảnh (biển rẽ trái/phải sẽ sai ý nghĩa nếu lật)
        hsv_h=0.02, hsv_s=0.6, hsv_v=0.5,
        degrees=10, translate=0.1, scale=0.4, shear=3.0,
        perspective=0.0005,
        flipud=0.0,
        fliplr=0.0,
        mosaic=1.0,
        mixup=0.1,
        # copy_paste giúp tăng số lần các đối tượng hiếm xuất hiện trong batch
        # (dán vật thể từ ảnh khác vào) — hữu ích khi vài lớp có rất ít mẫu
        copy_paste=0.15,

        project="runs/detect",
        name="finetune_v2",   # lưu riêng, KHÔNG ghi đè lên lần train gốc
        exist_ok=True,
        verbose=True,
    )

    best_path = Path("runs/detect/finetune_v2/weights/best.pt")
    print("\n=== FINE-TUNE HOÀN TẤT ===")
    print(f"Model mới: {best_path.resolve() if best_path.exists() else '(chưa thấy file)'}")
    print("\nBước tiếp theo — SO SÁNH trước khi thay model cũ:")
    print("  1. python src/evaluate.py                      # đánh giá model CŨ (nếu chưa đánh giá lần nào)")
    print(f"  2. cp {best_path} models/trained/best_v2.pt     # copy model mới sang tên khác, KHÔNG ghi đè best.pt")
    print("  3. Sửa tạm config.TRAINED_MODEL trỏ tới best_v2.pt, chạy lại src/evaluate.py")
    print("  4. So sánh Precision/Recall/mAP hai model — chỉ thay hẳn best.pt nếu model mới TỐT HƠN")
    print("     (fine-tune trên dữ liệu ít có rủi ro làm giảm điểm ở các lớp vốn đã tốt, nên phải so sánh, không thay mù quáng)")


if __name__ == "__main__":
    main()