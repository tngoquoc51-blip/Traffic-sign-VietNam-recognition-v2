"""
Backend Flask cho giao diện web nhận diện & đánh giá mô hình biển báo giao thông VN.
Thay thế cho gui/app.py (Tkinter) — dùng lại đúng model (models/trained/best.pt),
cấu hình (src/config.py) và danh sách lớp (data/data.yaml) sẵn có của project.

Chạy:
    cd webapp
    python app.py
Mở trình duyệt: http://localhost:5000
"""

import os
import sys
import json
import time
from pathlib import Path

from flask import Flask, request, jsonify, render_template, send_from_directory, redirect, url_for, session
from werkzeug.security import check_password_hash
from functools import wraps

WEBAPP_DIR = Path(__file__).resolve().parent
ROOT_DIR = WEBAPP_DIR.parent
sys.path.append(str(ROOT_DIR / "src"))

import config as project_config          # noqa: E402  (src/config.py)
import utils as project_utils             # noqa: E402  (src/utils.py)

from ultralytics import YOLO              # noqa: E402
import cv2                                # noqa: E402

app = Flask(__name__)
# Khoá bí mật để ký session cookie. Nên đặt qua biến môi trường khi triển khai thật:
#   export FLASK_SECRET_KEY="chuoi-bi-mat-cua-ban"
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "doi-khoa-nay-truoc-khi-trien-khai-that")

with open(WEBAPP_DIR / "admin_credentials.json", "r", encoding="utf-8") as f:
    ADMIN_CREDENTIALS = json.load(f)


def login_required(view_func):
    """Chặn truy cập nếu chưa đăng nhập admin, chuyển hướng về /login."""
    @wraps(view_func)
    def wrapped(*args, **kwargs):
        if not session.get("logged_in"):
            return redirect(url_for("login", next=request.path))
        return view_func(*args, **kwargs)
    return wrapped


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "")
        password = request.form.get("password", "")
        if (username == ADMIN_CREDENTIALS["username"]
                and check_password_hash(ADMIN_CREDENTIALS["password_hash"], password)):
            session["logged_in"] = True
            session["username"] = username
            next_url = request.args.get("next") or url_for("index")
            return redirect(next_url)
        return render_template("login.html", error="Tài khoản hoặc mật khẩu không đúng.")
    return render_template("login.html", error=None)


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

UPLOAD_DIR = ROOT_DIR / "outputs" / "predictions" / "web_uploads"
RESULT_DIR = ROOT_DIR / "outputs" / "predictions" / "web_results"
REPORTS_DIR = ROOT_DIR / "outputs" / "reports"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
RESULT_DIR.mkdir(parents=True, exist_ok=True)
REPORTS_DIR.mkdir(parents=True, exist_ok=True)

with open(WEBAPP_DIR / "sign_meanings_vi.json", "r", encoding="utf-8") as f:
    SIGN_MEANINGS = json.load(f)

GROUP_INFO = {
    "P":  {"name": "Biển cấm",       "color": "#E2352F"},
    "W":  {"name": "Biển nguy hiểm", "color": "#FFC53D"},
    "R":  {"name": "Biển hiệu lệnh", "color": "#2F6FED"},
    "I":  {"name": "Biển chỉ dẫn",   "color": "#35C46B"},
    "S":  {"name": "Biển phụ",       "color": "#9AA0A6"},
    "DP": {"name": "Biển phụ",       "color": "#9AA0A6"},
}

_model = None
_eval_cache = {"result": None}


def get_model():
    """Nạp model 1 lần, dùng lại cho các lần gọi sau (tránh load lại chậm mỗi request)."""
    global _model
    if _model is None:
        if not os.path.exists(project_config.TRAINED_MODEL):
            raise FileNotFoundError(
                f"Không tìm thấy model tại {project_config.TRAINED_MODEL}. "
                f"Hãy huấn luyện model trước: python src/train.py"
            )
        _model = YOLO(project_config.TRAINED_MODEL)
    return _model


def sign_info(code: str) -> dict:
    prefix = code.split(".")[0]
    group = GROUP_INFO.get(prefix, {"name": "Không rõ nhóm", "color": "#767065"})
    meaning = SIGN_MEANINGS.get(code, "")
    return {
        "code": code,
        "group": group["name"],
        "group_prefix": prefix,
        "color": group["color"],
        "meaning": meaning or "(chưa có mô tả — cập nhật trong webapp/sign_meanings_vi.json)",
    }


# ----------------------------------------------------------------------
# Trang giao diện
# ----------------------------------------------------------------------
@app.route("/")
@login_required
def index():
    return render_template("index.html", username=session.get("username"))


# ----------------------------------------------------------------------
# API: danh sách lớp (đọc trực tiếp từ data/data.yaml thật)
# ----------------------------------------------------------------------
@app.route("/api/classes")
@login_required
def api_classes():
    names = project_utils.load_class_names(project_config.DATA_YAML)
    out = []
    for cid, code in sorted(names.items(), key=lambda x: int(x[0])):
        info = sign_info(code)
        info["id"] = cid
        out.append(info)
    return jsonify({"count": len(out), "classes": out})


# ----------------------------------------------------------------------
# API: nhận diện 1 ảnh — chạy model.predict() thật trên ảnh người dùng tải lên
# ----------------------------------------------------------------------
@app.route("/api/predict", methods=["POST"])
@login_required
def api_predict():
    if "image" not in request.files:
        return jsonify({"error": "Thiếu file ảnh (field 'image')."}), 400

    file = request.files["image"]
    if file.filename == "":
        return jsonify({"error": "Chưa chọn file."}), 400

    ts = int(time.time() * 1000)
    safe_name = "".join(c for c in file.filename if c.isalnum() or c in "._-")
    in_path = UPLOAD_DIR / f"{ts}_{safe_name}"
    file.save(in_path)

    try:
        model = get_model()
    except FileNotFoundError as e:
        return jsonify({"error": str(e)}), 500

    conf_thres = float(request.form.get("conf", project_config.CONF_THRESHOLD))

    t0 = time.time()
    results = model.predict(source=str(in_path), conf=conf_thres, verbose=False)
    infer_ms = round((time.time() - t0) * 1000, 1)
    result = results[0]

    annotated_bgr = result.plot()
    out_name = f"{ts}_result.jpg"
    cv2.imwrite(str(RESULT_DIR / out_name), annotated_bgr)

    detections = []
    for box in result.boxes:
        cls_id = int(box.cls[0])
        conf = float(box.conf[0])
        code = model.names[cls_id]
        x1, y1, x2, y2 = [round(v, 1) for v in box.xyxy[0].tolist()]
        det = sign_info(code)
        det.update({"confidence": round(conf, 4), "bbox": [x1, y1, x2, y2]})
        detections.append(det)

    detections.sort(key=lambda d: -d["confidence"])
    avg_conf = round(sum(d["confidence"] for d in detections) / len(detections), 4) if detections else None

    return jsonify({
        "filename": file.filename,
        "detections": detections,
        "count": len(detections),
        "avg_confidence": avg_conf,
        "inference_ms": infer_ms,
        "result_image_url": f"/media/results/{out_name}",
    })


@app.route("/media/results/<path:filename>")
def serve_result_image(filename):
    return send_from_directory(RESULT_DIR, filename)


# ----------------------------------------------------------------------
# API: đánh giá model thật trên tập test/val bằng model.val() (Ultralytics)
# Kết quả được cache lại vì chạy trên toàn bộ tập test khá tốn thời gian.
# ----------------------------------------------------------------------
@app.route("/api/evaluate", methods=["POST"])
@login_required
def api_evaluate():
    force = request.args.get("force", "false").lower() == "true"
    split = request.args.get("split", "test")

    if _eval_cache["result"] is not None and not force:
        return jsonify(_eval_cache["result"])

    try:
        model = get_model()
    except FileNotFoundError as e:
        return jsonify({"error": str(e)}), 500

    metrics = model.val(
        data=project_config.DATA_YAML,
        split=split,
        project=str(REPORTS_DIR),
        name="web_evaluation",
        exist_ok=True,
        plots=True,
    )

    names = model.names
    per_class = []
    try:
        ap50_per_class = metrics.box.ap50
        for idx, ap in enumerate(ap50_per_class):
            code = names[idx]
            info = sign_info(code)
            info["ap50"] = round(float(ap), 4)
            per_class.append(info)
        per_class.sort(key=lambda d: d["ap50"])
    except Exception:
        per_class = []

    save_dir = Path(metrics.save_dir)
    cm_candidates = ["confusion_matrix_normalized.png", "confusion_matrix.png"]
    cm_url = None
    for name in cm_candidates:
        if (save_dir / name).exists():
            cm_url = f"/media/reports/web_evaluation/{name}"
            break

    result = {
        "split": split,
        "precision": round(float(metrics.box.mp), 4),
        "recall": round(float(metrics.box.mr), 4),
        "map50": round(float(metrics.box.map50), 4),
        "map50_95": round(float(metrics.box.map), 4),
        "num_classes": len(names),
        "worst_classes": per_class[:10],
        "confusion_matrix_url": cm_url,
        "evaluated_at": time.strftime("%H:%M:%S %d/%m/%Y"),
    }

    _eval_cache["result"] = result
    return jsonify(result)


@app.route("/media/reports/<path:filename>")
def serve_report_file(filename):
    return send_from_directory(REPORTS_DIR, filename)


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
