"""
Đánh giá model đã huấn luyện trên tập test/val.
In ra các chỉ số: precision, recall, mAP50, mAP50-95.
Đồng thời lưu lại tóm tắt ra file JSON để trang web /metrics đọc và hiển thị
mà không cần chạy lại model mỗi lần xem (việc đánh giá khá tốn thời gian).
"""

import os
import json
import shutil
from datetime import datetime

from ultralytics import YOLO
import config

REPORT_DIR = os.path.join("outputs", "reports", "evaluation")


def evaluate_model(model_path=config.TRAINED_MODEL):
    model = YOLO(model_path)

    metrics = model.val(
        data=config.DATA_YAML,
        split="test",
        project="outputs/reports",
        name="evaluation",
        exist_ok=True,   # ghi đè lần chạy trước, để luôn có 1 bộ kết quả mới nhất
        plots=True,       # BẮT BUỘC để YOLO vẽ confusion matrix, PR curve, F1 curve... ra file ảnh
    )

    print("=== KẾT QUẢ ĐÁNH GIÁ MODEL ===")
    print(f"mAP50:     {metrics.box.map50:.4f}")
    print(f"mAP50-95:  {metrics.box.map:.4f}")
    print(f"Precision: {metrics.box.mp:.4f}")
    print(f"Recall:    {metrics.box.mr:.4f}")

    # -----------------------------------------------------------------
    # Ultralytics tự ý chèn thêm "runs/detect/" vào trước đường dẫn project
    # ta chỉ định, nên ảnh biểu đồ (confusion matrix, PR curve...) không nằm
    # cùng chỗ với JSON tóm tắt bên dưới. Copy các ảnh đó sang đúng REPORT_DIR
    # để trang web /metrics (chỉ đọc 1 chỗ duy nhất) luôn tìm thấy đầy đủ.
    # -----------------------------------------------------------------
    os.makedirs(REPORT_DIR, exist_ok=True)
    actual_save_dir = str(metrics.save_dir)
    if os.path.isdir(actual_save_dir) and os.path.abspath(actual_save_dir) != os.path.abspath(REPORT_DIR):
        copied = 0
        for fname in os.listdir(actual_save_dir):
            if fname.lower().endswith(".png"):
                shutil.copy2(os.path.join(actual_save_dir, fname), os.path.join(REPORT_DIR, fname))
                copied += 1
        print(f"Đã copy {copied} ảnh biểu đồ từ {actual_save_dir} sang {REPORT_DIR}")
    else:
        print(f"Biểu đồ đã nằm sẵn trong {REPORT_DIR}")

    # -----------------------------------------------------------------
    # Lưu tóm tắt ra JSON: chỉ số tổng thể + chỉ số theo từng lớp biển
    # -----------------------------------------------------------------
    per_class = []
    class_indices = metrics.box.ap_class_index.tolist() if hasattr(metrics.box.ap_class_index, "tolist") else list(metrics.box.ap_class_index)
    ap50_list = metrics.box.ap50.tolist() if hasattr(metrics.box.ap50, "tolist") else list(metrics.box.ap50)
    ap_list = metrics.box.ap.tolist() if hasattr(metrics.box.ap, "tolist") else list(metrics.box.ap)
    p_list = metrics.box.p.tolist() if hasattr(metrics.box.p, "tolist") else list(metrics.box.p)
    r_list = metrics.box.r.tolist() if hasattr(metrics.box.r, "tolist") else list(metrics.box.r)

    for i, cls_id in enumerate(class_indices):
        per_class.append({
            "class_name": model.names[int(cls_id)],
            "precision": round(p_list[i], 4) if i < len(p_list) else None,
            "recall": round(r_list[i], 4) if i < len(r_list) else None,
            "ap50": round(ap50_list[i], 4) if i < len(ap50_list) else None,
            "ap50_95": round(ap_list[i], 4) if i < len(ap_list) else None,
        })

    # Xếp theo AP50 tăng dần -> lớp yếu nhất hiện lên đầu, dễ biết cần bổ sung ảnh cho lớp nào
    per_class.sort(key=lambda x: (x["ap50"] if x["ap50"] is not None else 0))

    summary = {
        "evaluated_at": datetime.now().isoformat(timespec="seconds"),
        "model_path": model_path,
        "map50": round(float(metrics.box.map50), 4),
        "map50_95": round(float(metrics.box.map), 4),
        "precision": round(float(metrics.box.mp), 4),
        "recall": round(float(metrics.box.mr), 4),
        "num_classes_evaluated": len(class_indices),
        "per_class": per_class,
    }

    summary_path = os.path.join(REPORT_DIR, "metrics_summary.json")
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)

    print(f"Đã lưu tóm tắt JSON tại: {summary_path}")
    return summary


if __name__ == "__main__":
    evaluate_model()