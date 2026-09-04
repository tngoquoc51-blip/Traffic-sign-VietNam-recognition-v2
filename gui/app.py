"""
Web Dashboard - Hệ thống nhận diện và phân loại biển báo giao thông Việt Nam
Chạy: python gui/web_app.py (từ thư mục gốc dự án)
Truy cập: http://127.0.0.1:5000
"""

import os
import sys
import sqlite3
import time
import uuid
import threading
from datetime import datetime, date

import json
import cv2
import numpy as np
from flask import Flask, render_template, request, redirect, url_for, flash, Response, jsonify, session, send_file
from werkzeug.utils import secure_filename
import io
import yaml
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill
from fpdf import FPDF
import unicodedata
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "src"))
import config
from sign_info import get_sign_info  # NEW: tra cứu tên + ý nghĩa chi tiết từng mã biển
import auth  # NEW: đăng nhập admin, quên mật khẩu qua Gmail
import telegram_notify  # NEW: gửi thông báo Telegram cho admin

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "detections.db")
UPLOAD_DIR = os.path.join(BASE_DIR, "static", "uploads")
RESULT_DIR = os.path.join(BASE_DIR, "static", "results")

app = Flask(__name__)
app.secret_key = "traffic-sign-vn-dev-key"

# ---------------------------------------------------------------------------
# NEW: Chỉ cho phép truy cập từ MỘT địa chỉ IP duy nhất (bảo mật thêm ngoài đăng nhập)
# ---------------------------------------------------------------------------
ALLOWED_IP = "127.0.0.1"  # ĐỔI thành IP máy bạn muốn cho phép truy cập
app.config["MAX_CONTENT_LENGTH"] = 200 * 1024 * 1024  # 200MB (đủ cho video ngắn)

_model = None  # lazy-loaded YOLO model

# Xử lý 1 khung hình cho mỗi VIDEO_FRAME_SKIP khung để tăng tốc trên GPU yếu
VIDEO_FRAME_SKIP = 3
# Giới hạn số khung xử lý tối đa để tránh video quá dài làm treo máy
VIDEO_MAX_FRAMES = 1800

# Bộ nhớ tạm lưu trạng thái từng phiên xem video trực tiếp (session_id -> dict)
VIDEO_SESSIONS = {}

# Thứ tự hiển thị cột theo nhóm biển trong thư viện kết quả (cố định để giao diện ổn định)
GROUP_ORDER = ["Biển cấm", "Biển nguy hiểm", "Biển hiệu lệnh", "Biển chỉ dẫn", "Biển phụ"]


# ---------------------------------------------------------------------------
# Nhóm biển báo theo tiền tố mã (chuẩn QCVN 41:2019)
# ---------------------------------------------------------------------------
GROUP_MAP = {
    "P": ("Biển cấm", "danger"),
    "W": ("Biển nguy hiểm", "warning"),
    "R": ("Biển hiệu lệnh", "info"),
    "S": ("Biển chỉ dẫn", "success"),
    "DP": ("Biển phụ", "neutral"),
}

GROUP_DESCRIPTIONS = {
    "Biển cấm": "Biểu thị các điều cấm mà người tham gia giao thông không được vi phạm.",
    "Biển nguy hiểm": "Báo trước tình huống nguy hiểm phía trước để chủ động phòng ngừa.",
    "Biển hiệu lệnh": "Báo các hiệu lệnh bắt buộc phải chấp hành.",
    "Biển chỉ dẫn": "Cung cấp thông tin chỉ dẫn cần thiết trên đường.",
    "Biển phụ": "Bổ sung, làm rõ nội dung cho biển chính đi kèm.",
}


def get_group_description(group_label: str) -> str:
    return GROUP_DESCRIPTIONS.get(group_label, "")


def get_group(class_name: str):
    prefix = class_name.split(".")[0]
    return GROUP_MAP.get(prefix, ("Khác", "neutral"))


def build_sign_payload(class_name: str, conf: float, thumb_url=None) -> dict:
    """Gộp mọi thông tin cần hiển thị cho MỘT biển báo đã phát hiện:
    nhóm, tên chi tiết, ý nghĩa chi tiết theo đúng mã biển (không chỉ mô tả nhóm chung)."""
    label, badge = get_group(class_name)
    info = get_sign_info(class_name)
    payload = {
        "class_name": class_name,
        "sign_name": info["name"],
        "meaning": info["meaning"],
        "group_label": label,
        "badge": badge,
        "group_description": get_group_description(label),
        "confidence": round(conf * 100, 1),
    }
    if thumb_url is not None:
        payload["thumbnail_url"] = thumb_url
    return payload


def group_signs_into_columns(signs: list) -> list:
    """Nhận danh sách sign payload (đã có group_label) và trả về danh sách cột
    theo thứ tự GROUP_ORDER, mỗi cột gồm {label, badge, signs: [...]}.
    Chỉ trả về các cột có ít nhất 1 biển để giao diện không hiển thị cột trống."""
    buckets = {}
    for s in signs:
        buckets.setdefault(s["group_label"], []).append(s)

    columns = []
    ordered_labels = GROUP_ORDER + [l for l in buckets.keys() if l not in GROUP_ORDER]
    for label in ordered_labels:
        if label in buckets and buckets[label]:
            badge = buckets[label][0]["badge"]
            columns.append({"label": label, "badge": badge, "signs": buckets[label]})
    return columns


# ---------------------------------------------------------------------------
# Database
# ---------------------------------------------------------------------------
def init_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS detections (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            source_image TEXT,
            result_image TEXT,
            class_name TEXT NOT NULL,
            confidence REAL NOT NULL
        )
    """)
    conn.commit()
    conn.close()


def save_detections(source_image, result_image, detections):
    conn = sqlite3.connect(DB_PATH)
    now = datetime.now().isoformat(timespec="seconds")
    for class_name, conf in detections:
        conn.execute(
            "INSERT INTO detections (timestamp, source_image, result_image, class_name, confidence) "
            "VALUES (?, ?, ?, ?, ?)",
            (now, source_image, result_image, class_name, conf),
        )
    conn.commit()
    conn.close()


def get_model():
    global _model
    if _model is None:
        from ultralytics import YOLO
        if not os.path.exists(config.TRAINED_MODEL):
            raise FileNotFoundError(
                f"Chưa tìm thấy model đã huấn luyện tại {config.TRAINED_MODEL}. "
                "Hãy chạy src/train.py và copy best.pt vào models/trained/ trước."
            )
        _model = YOLO(config.TRAINED_MODEL)
    return _model


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------
def get_system_info():
    """Thông tin hệ thống thật: GPU, trạng thái model, kích thước dataset."""
    info = {
        "model_loaded": os.path.exists(config.TRAINED_MODEL),
        "gpu_name": "Không phát hiện GPU",
        "gpu_available": False,
        "num_classes": 58,
    }
    try:
        import torch
        if torch.cuda.is_available():
            info["gpu_available"] = True
            info["gpu_name"] = torch.cuda.get_device_name(0)
    except Exception:
        pass

    try:
        import yaml
        with open(config.DATA_YAML, "r", encoding="utf-8") as f:
            data_cfg = yaml.safe_load(f)
        info["num_classes"] = data_cfg.get("nc", 58)
    except Exception:
        pass

    return info

def load_all_classes():
    with open(config.DATA_YAML, "r", encoding="utf-8") as f:
        data_cfg = yaml.safe_load(f)
    names = data_cfg["names"]
    if isinstance(names, list):
        names = {i: n for i, n in enumerate(names)}
    result = []
    for cid, code in sorted(names.items(), key=lambda x: int(x[0])):
        group_label, badge = get_group(code)
        info = get_sign_info(code)
        result.append({
            "id": int(cid), "code": code,
            "meaning": info.get("meaning") or info.get("name") or "",
            "sign_name": info.get("name", ""),
            "group": group_label, "badge": badge,
        })
    return result


def load_history_from_db(date_from=None, date_to=None, group=None, min_conf=0.0):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    query = "SELECT class_name, confidence, timestamp FROM detections WHERE confidence >= ?"
    params = [min_conf]
    if date_from:
        query += " AND timestamp >= ?"; params.append(date_from)
    if date_to:
        query += " AND timestamp <= ?"; params.append(date_to + " 23:59:59")
    if group and group != "all":
        query += " AND class_name LIKE ?"; params.append(f"{group}.%")
    query += " ORDER BY timestamp DESC"
    rows = conn.execute(query, params).fetchall()
    conn.close()
    records = []
    for r in rows:
        label, badge = get_group(r["class_name"])
        records.append({
            "code": r["class_name"], "confidence": r["confidence"],
            "timestamp": r["timestamp"].replace("T", " "), "group_label": label,
        })
    return records


def build_excel(records):
    wb = Workbook()
    ws = wb.active
    ws.title = "Lich su nhan dien"
    headers = ["Mã biển", "Nhóm", "Độ tin cậy (%)", "Thời gian"]
    ws.append(headers)
    header_fill = PatternFill(start_color="8B5CF6", end_color="8B5CF6", fill_type="solid")
    for col in range(1, len(headers) + 1):
        cell = ws.cell(row=1, column=col)
        cell.font = Font(bold=True, color="FFFFFF")
        cell.fill = header_fill
    for r in records:
        ws.append([r["code"], r["group_label"], round(r["confidence"] * 100, 1), r["timestamp"]])
    for col_cells in ws.columns:
        length = max((len(str(c.value)) for c in col_cells if c.value is not None), default=8)
        ws.column_dimensions[col_cells[0].column_letter].width = length + 4
    buf = io.BytesIO()
    wb.save(buf)
    buf.seek(0)
    return buf

def strip_accents(text: str) -> str:
    """Bỏ dấu tiếng Việt — vì font PDF mặc định (Helvetica) chỉ hỗ trợ Latin-1,
    ghi thẳng chữ có dấu sẽ làm crash thư viện fpdf, gây lỗi 500."""
    if not text:
        return text
    nfkd = unicodedata.normalize("NFKD", text)
    return "".join(c for c in nfkd if not unicodedata.combining(c))

def _get_unicode_font_path():
    """Tìm 1 font TrueType hỗ trợ tiếng Việt có sẵn trên Windows."""
    candidates = [
        r"C:\Windows\Fonts\arial.ttf",
        r"C:\Windows\Fonts\tahoma.ttf",
        r"C:\Windows\Fonts\segoeui.ttf",
    ]
    for path in candidates:
        if os.path.exists(path):
            return path
    return None


def build_pdf(records):
    pdf = FPDF()
    pdf.add_page()

    font_path = _get_unicode_font_path()
    if font_path:
        pdf.add_font("VNFont", "", font_path)
        font_name = "VNFont"
    else:
        font_name = "Helvetica"  # dự phòng, sẽ lỗi dấu tiếng Việt nếu không có font nào ở trên

    pdf.set_font(font_name, size=16)
    pdf.cell(0, 12, "BÁO CÁO NHẬN DIỆN BIỂN BÁO GIAO THÔNG", ln=True, align="C")
    pdf.set_font(font_name, size=10)
    pdf.cell(0, 8, f"TrafficVision AI - Xuất lúc {datetime.now().strftime('%H:%M %d/%m/%Y')}", ln=True, align="C")
    pdf.ln(6)

    group_counts = {}
    for r in records:
        g = r["group_label"]
        group_counts[g] = group_counts.get(g, 0) + 1

    pdf.set_font(font_name, size=12)
    pdf.cell(0, 8, "Thống kê theo nhóm biển", ln=True)
    pdf.set_font(font_name, size=10)
    for g, n in group_counts.items():
        pdf.cell(0, 7, f"  - {g}: {n} lượt", ln=True)
    pdf.ln(4)

    pdf.set_font(font_name, size=12)
    pdf.cell(0, 8, f"Chi tiết ({len(records)} bản ghi)", ln=True)
    pdf.set_font(font_name, size=9)
    col_w = [40, 60, 40, 50]
    for w, h in zip(col_w, ["Mã biển", "Nhóm", "Tin cậy (%)", "Thời gian"]):
        pdf.cell(w, 8, h, border=1)
    pdf.ln()
    pdf.ln()
    for r in records:
        pdf.cell(col_w[0], 7, r["code"], border=1)
        pdf.cell(col_w[1], 7, r["group_label"], border=1)
        pdf.cell(col_w[2], 7, f"{r['confidence']*100:.1f}", border=1)
        pdf.cell(col_w[3], 7, r["timestamp"], border=1)
        pdf.ln()

    output = pdf.output(dest="S")
    if isinstance(output, str):
        output = output.encode("latin1")
    buf = io.BytesIO(bytes(output))
    buf.seek(0)
    return buf

@app.before_request
def require_admin_login():
    """Bắt buộc đăng nhập admin cho mọi trang, trừ login/quên mật khẩu."""
    allowed_endpoints = {"login", "forgot_password", "reset_password", "static"}
    if request.endpoint in allowed_endpoints or request.endpoint is None:
        return  # cho qua, không cần đăng nhập
    if not session.get("admin_logged_in"):
        return redirect(url_for("login", next=request.path))


@app.route("/login", methods=["GET", "POST"])
def login():
    if session.get("admin_logged_in"):
        return redirect(url_for("dashboard"))
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        admin = auth.verify_admin(username, password)
        if admin:
            session["admin_logged_in"] = True
            session["admin_id"] = admin["id"]
            session["admin_username"] = admin["username"]
            telegram_notify.notify_admin_login(admin["username"], request.remote_addr)  # NEW
            return redirect(request.args.get("next") or url_for("dashboard"))
        flash("Tài khoản hoặc mật khẩu không đúng.")
        return redirect(url_for("login"))
    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


@app.route("/forgot-password", methods=["GET", "POST"])
def forgot_password():
    if request.method == "POST":
        email = request.form.get("email", "").strip()
        admin = auth.get_admin_by_email(email)
        if not admin:
            flash("Nếu email tồn tại trong hệ thống, mã xác nhận đã được gửi.", "success")
            return redirect(url_for("reset_password", email=email))
        code = auth.generate_reset_code(email)
        ok, err = auth.send_reset_email(email, code)
        if ok:
            flash(f"Đã gửi mã xác nhận đến {email}. Vui lòng kiểm tra hộp thư.", "success")
        else:
            flash(f"Không gửi được email (kiểm tra cấu hình Gmail trong src/auth.py). Lỗi: {err}")
        return redirect(url_for("reset_password", email=email))
    return render_template("forgot_password.html")


@app.route("/reset-password", methods=["GET", "POST"])
def reset_password():
    if request.method == "POST":
        email = request.form.get("email", "").strip()
        code = request.form.get("code", "").strip()
        new_password = request.form.get("new_password", "")
        confirm_password = request.form.get("confirm_password", "")
        if new_password != confirm_password:
            flash("Mật khẩu xác nhận không khớp.")
            return redirect(url_for("reset_password", email=email))
        if len(new_password) < 6:
            flash("Mật khẩu mới phải có ít nhất 6 ký tự.")
            return redirect(url_for("reset_password", email=email))
        if not auth.verify_reset_code(email, code):
            flash("Mã xác nhận không đúng hoặc đã hết hạn. Vui lòng yêu cầu gửi lại.")
            return redirect(url_for("reset_password", email=email))
        auth.update_admin_password(email, new_password)
        auth.mark_code_used(email, code)
        flash("Đặt lại mật khẩu thành công! Hãy đăng nhập bằng mật khẩu mới.", "success")
        return redirect(url_for("login"))
    prefill_email = request.args.get("email", "")
    return render_template("reset_password.html", prefill_email=prefill_email)


@app.route("/")
def dashboard():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    today_str = date.today().isoformat()

    total_today = conn.execute(
        "SELECT COUNT(*) AS c FROM detections WHERE timestamp LIKE ?", (f"{today_str}%",)
    ).fetchone()["c"]

    total_all = conn.execute("SELECT COUNT(*) AS c FROM detections").fetchone()["c"]

    avg_conf_row = conn.execute("SELECT AVG(confidence) AS a FROM detections").fetchone()
    avg_conf = round((avg_conf_row["a"] or 0) * 100, 1)

    prohibition_count = conn.execute(
        "SELECT COUNT(*) AS c FROM detections WHERE class_name LIKE 'P.%'"
    ).fetchone()["c"]

    recent = conn.execute(
        "SELECT * FROM detections ORDER BY id DESC LIMIT 8"
    ).fetchall()

    all_rows = conn.execute("SELECT class_name FROM detections").fetchall()

    # Xu hướng 7 ngày gần nhất (số lượt nhận diện mỗi ngày) — dữ liệu thật từ database
    trend = []
    for i in range(6, -1, -1):
        day = date.fromordinal(date.today().toordinal() - i)
        day_str = day.isoformat()
        count = conn.execute(
            "SELECT COUNT(*) AS c FROM detections WHERE timestamp LIKE ?", (f"{day_str}%",)
        ).fetchone()["c"]
        trend.append({"label": day.strftime("%d/%m"), "count": count})
    max_trend = max((t["count"] for t in trend), default=0) or 1

    conn.close()

    group_counts = {"Biển cấm": 0, "Biển nguy hiểm": 0, "Biển hiệu lệnh": 0, "Biển chỉ dẫn": 0, "Biển phụ": 0}
    for row in all_rows:
        label, _ = get_group(row["class_name"])
        if label in group_counts:
            group_counts[label] += 1
        else:
            group_counts[label] = group_counts.get(label, 0) + 1
    max_group = max(group_counts.values()) if any(group_counts.values()) else 1

    recent_rows = []
    for r in recent:
        label, badge = get_group(r["class_name"])
        recent_rows.append({
            "class_name": r["class_name"],
            "group_label": label,
            "badge": badge,
            "confidence": round(r["confidence"] * 100, 1),
            "timestamp": r["timestamp"].replace("T", " "),
        })

    system_info = get_system_info()

    return render_template(
        "dashboard.html",
        total_today=total_today,
        total_all=total_all,
        avg_conf=avg_conf,
        prohibition_count=prohibition_count,
        group_counts=group_counts,
        max_group=max_group,
        recent_rows=recent_rows,
        num_classes=system_info["num_classes"],
        system_info=system_info,
        trend=trend,
        max_trend=max_trend,
    )


@app.route("/detect", methods=["GET", "POST"])
def detect():
    if request.method == "GET":
        return render_template("detect.html", result=None)

    file = request.files.get("image")
    if not file or file.filename == "":
        flash("Vui lòng chọn một ảnh trước khi nhận diện.")
        return redirect(url_for("detect"))

    filename = secure_filename(file.filename)
    stamped_name = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{filename}"
    upload_path = os.path.join(UPLOAD_DIR, stamped_name)
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    os.makedirs(RESULT_DIR, exist_ok=True)
    file.save(upload_path)

    try:
        model = get_model()
    except FileNotFoundError as e:
        flash(str(e))
        return redirect(url_for("detect"))

    results = model.predict(source=upload_path, conf=config.CONF_THRESHOLD, save=False)
    result = results[0]

    result_filename = f"result_{stamped_name}"
    result_path = os.path.join(RESULT_DIR, result_filename)
    annotated = result.plot()
    cv2.imwrite(result_path, annotated)

    thumb_dir = os.path.join(RESULT_DIR, "thumbs")
    os.makedirs(thumb_dir, exist_ok=True)
    original_frame = cv2.imread(upload_path)

    detections = []
    detected_signs = []
    for idx, box in enumerate(result.boxes):
        cls_id = int(box.cls[0])
        conf = float(box.conf[0])
        class_name = model.names[cls_id]
        detections.append((class_name, conf))

        thumb_url = None
        if original_frame is not None:
            x1, y1, x2, y2 = [int(v) for v in box.xyxy[0].tolist()]
            h, w = original_frame.shape[:2]
            pad = 12
            x1p, y1p = max(0, x1 - pad), max(0, y1 - pad)
            x2p, y2p = min(w, x2 + pad), min(h, y2 + pad)
            crop = original_frame[y1p:y2p, x1p:x2p]
            if crop.size > 0:
                safe_class = class_name.replace(".", "_")
                thumb_filename = f"{stamped_name}_{idx}_{safe_class}.jpg"
                cv2.imwrite(os.path.join(thumb_dir, thumb_filename), crop)
                thumb_url = url_for("static", filename=f"results/thumbs/{thumb_filename}")

        detected_signs.append(build_sign_payload(class_name, conf, thumb_url=thumb_url))

    save_detections(f"uploads/{stamped_name}", f"results/{result_filename}", detections)

    # NEW: gửi thông báo Telegram kèm ảnh kết quả
    telegram_notify.notify_detection_result(
        username=session.get("admin_username", "admin"),
        source_type="ảnh",
        signs=detected_signs,
        image_path=result_path,
    )

    # Phân nhóm theo cột để giao diện hiển thị theo từng loại biển
    sign_columns = group_signs_into_columns(detected_signs)

    system_info = get_system_info()

    return render_template(
        "detect.html",
        result={
            "image_url": url_for("static", filename=f"results/{result_filename}"),
            "signs": detected_signs,
            "columns": sign_columns,
            "count": len(detected_signs),
        },
        num_classes=system_info["num_classes"],
    )


@app.route("/video", methods=["GET"])
def video():
    return render_template("video.html")


@app.route("/video/upload", methods=["POST"])
def video_upload():
    """Nhận file video, lưu lại, tạo phiên xử lý mới và trả về session_id."""
    file = request.files.get("video")
    if not file or file.filename == "":
        return jsonify({"error": "Vui lòng chọn một video."}), 400

    try:
        get_model()
    except FileNotFoundError as e:
        return jsonify({"error": str(e)}), 400

    filename = secure_filename(file.filename)
    stamped_name = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{filename}"
    upload_path = os.path.join(UPLOAD_DIR, stamped_name)
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    file.save(upload_path)

    # Đọc nhanh thời lượng video (giây) để hiển thị thanh tua đúng tổng thời gian
    probe = cv2.VideoCapture(upload_path)
    probe_fps = probe.get(cv2.CAP_PROP_FPS) or 25
    probe_frame_count = probe.get(cv2.CAP_PROP_FRAME_COUNT) or 0
    duration_sec = round(probe_frame_count / probe_fps, 1) if probe_fps else 0
    probe.release()

    session_id = uuid.uuid4().hex[:12]
    THUMB_DIR = os.path.join(RESULT_DIR, "thumbs")
    os.makedirs(THUMB_DIR, exist_ok=True)
    VIDEO_SESSIONS[session_id] = {
        "upload_path": upload_path,
        "stamped_name": stamped_name,
        "status": "streaming",  # streaming -> done
        "processed_frames": 0,
        "start_time": time.time(),
        "elapsed": 0,
        "best_per_class": {},  # class_name -> confidence cao nhất
        "thumbnails": {},  # class_name -> tên file ảnh cắt (crop) đã chụp
        "order": [],  # thứ tự phát hiện lần đầu, để hiển thị theo dòng thời gian
        "paused": False,  # đang tạm dừng hay không
        "seek_to": None,  # thời điểm tuyệt đối (giây) cần nhảy tới khi kéo thanh tua
        "current_pos_sec": 0,  # vị trí hiện tại trong video (giây)
        "duration_sec": duration_sec,
        "admin_username": session.get("admin_username", "admin"),  # lưu sẵn để dùng khi gửi Telegram
    }
    return jsonify({
        "session_id": session_id,
        "filename": stamped_name,
        "duration_sec": duration_sec,
    })


@app.route("/video/control/<session_id>", methods=["POST"])
def video_control(session_id):
    """Điều khiển phiên đang quét: tạm dừng / tiếp tục / tua tới vị trí bất kỳ."""
    session = VIDEO_SESSIONS.get(session_id)
    if session is None:
        return jsonify({"error": "not found"}), 404

    payload = request.get_json(silent=True) or {}
    action = payload.get("action")

    if action == "pause":
        session["paused"] = True
    elif action == "resume":
        session["paused"] = False
    elif action == "seek_to":
        try:
            session["seek_to"] = float(payload.get("time", 0))
        except (TypeError, ValueError):
            return jsonify({"error": "invalid time"}), 400
    else:
        return jsonify({"error": "unknown action"}), 400

    return jsonify({"ok": True, "paused": session["paused"]})


@app.route("/video/reset/<session_id>", methods=["POST"])
def video_reset(session_id):
    """Quét lại video từ đầu, xoá kết quả cũ để bắt đầu phiên mới sạch sẽ."""
    session = VIDEO_SESSIONS.get(session_id)
    if session is None:
        return jsonify({"error": "not found"}), 404

    session["status"] = "streaming"
    session["processed_frames"] = 0
    session["start_time"] = time.time()
    session["elapsed"] = 0
    session["best_per_class"] = {}
    session["thumbnails"] = {}
    session["order"] = []
    session["paused"] = False
    session["seek_to"] = 0
    session["current_pos_sec"] = 0

    return jsonify({"ok": True})


def _generate_mjpeg(session_id):
    session = VIDEO_SESSIONS.get(session_id)
    if session is None:
        return

    model = get_model()
    thumb_dir = os.path.join(RESULT_DIR, "thumbs")
    os.makedirs(thumb_dir, exist_ok=True)

    cap = cv2.VideoCapture(session["upload_path"])
    fps = cap.get(cv2.CAP_PROP_FPS) or 25
    frame_interval = 1.0 / fps

    frame_idx = 0
    last_annotated = None

    try:
        while True:
            if session.get("paused"):
                if last_annotated is not None:
                    ok, buffer = cv2.imencode(".jpg", last_annotated, [int(cv2.IMWRITE_JPEG_QUALITY), 80])
                    if ok:
                        yield (b"--frame\r\n"
                               b"Content-Type: image/jpeg\r\n\r\n" + buffer.tobytes() + b"\r\n")
                time.sleep(0.2)
                continue

            seek_to = session.get("seek_to")
            if seek_to is not None:
                session["seek_to"] = None
                cap.set(cv2.CAP_PROP_POS_MSEC, max(0, seek_to * 1000))

            loop_start = time.time()
            ret, frame = cap.read()
            if not ret or frame_idx >= VIDEO_MAX_FRAMES:
                break

            session["current_pos_sec"] = round(cap.get(cv2.CAP_PROP_POS_MSEC) / 1000, 1)

            if frame_idx % VIDEO_FRAME_SKIP == 0:
                results = model.predict(source=frame, conf=config.CONF_THRESHOLD, verbose=False)
                result = results[0]
                last_annotated = result.plot()
                session["processed_frames"] += 1

                for box in result.boxes:
                    cls_id = int(box.cls[0])
                    conf = float(box.conf[0])
                    class_name = model.names[cls_id]

                    is_new = class_name not in session["best_per_class"]
                    is_better = is_new or conf > session["best_per_class"][class_name]

                    if is_new:
                        session["order"].append(class_name)

                    if is_better:
                        session["best_per_class"][class_name] = conf

                        x1, y1, x2, y2 = [int(v) for v in box.xyxy[0].tolist()]
                        h, w = frame.shape[:2]
                        pad = 12
                        x1p, y1p = max(0, x1 - pad), max(0, y1 - pad)
                        x2p, y2p = min(w, x2 + pad), min(h, y2 + pad)
                        crop = frame[y1p:y2p, x1p:x2p].copy()

                        if crop.size > 0:
                            safe_class = class_name.replace(".", "_")
                            thumb_filename = f"{session_id}_{safe_class}.jpg"
                            thumb_path = os.path.join(thumb_dir, thumb_filename)
                            cv2.imwrite(thumb_path, crop)
                            session["thumbnails"][class_name] = thumb_filename

                            if is_new:
                                admin_username = session.get("admin_username", "admin")
                                threading.Thread(
                                    target=telegram_notify.notify_detection_result,
                                    kwargs={
                                        "username": admin_username,
                                        "source_type": "video",
                                        "signs": [build_sign_payload(class_name, conf)],
                                        "image_path": thumb_path,
                                    },
                                    daemon=True,
                                ).start()

            show_frame = last_annotated if last_annotated is not None else frame
            ok, buffer = cv2.imencode(".jpg", show_frame, [int(cv2.IMWRITE_JPEG_QUALITY), 80])
            if ok:
                yield (b"--frame\r\n"
                       b"Content-Type: image/jpeg\r\n\r\n" + buffer.tobytes() + b"\r\n")

            session["elapsed"] = round(time.time() - session["start_time"], 1)

            remaining = frame_interval - (time.time() - loop_start)
            if remaining > 0:
                time.sleep(remaining)

            frame_idx += 1

    finally:
        cap.release()
        session["status"] = "done"

        detections = list(session["best_per_class"].items())
        if detections:
            result_filename = f"result_{session['stamped_name']}"
            save_detections(f"uploads/{session['stamped_name']}", result_filename, detections)


@app.route("/video/stream/<session_id>")
def video_stream(session_id):
    if session_id not in VIDEO_SESSIONS:
        return "Không tìm thấy phiên video.", 404
    return Response(_generate_mjpeg(session_id), mimetype="multipart/x-mixed-replace; boundary=frame")


@app.route("/video/status/<session_id>")
def video_status(session_id):
    session = VIDEO_SESSIONS.get(session_id)
    if session is None:
        return jsonify({"error": "not found"}), 404

    detected_signs = []
    for class_name in session["order"]:
        conf = session["best_per_class"][class_name]
        thumb_filename = session["thumbnails"].get(class_name)
        thumb_url = url_for("static", filename=f"results/thumbs/{thumb_filename}") if thumb_filename else None
        detected_signs.append(build_sign_payload(class_name, conf, thumb_url=thumb_url))

    group_summary = {}
    for sign in detected_signs:
        group_summary[sign["group_label"]] = group_summary.get(sign["group_label"], 0) + 1

    # NEW: phân nhóm theo cột (mỗi cột = 1 nhóm biển), kèm đầy đủ tên + ý nghĩa từng biển
    sign_columns = group_signs_into_columns(detected_signs)

    return jsonify({
        "status": session["status"],
        "processed_frames": session["processed_frames"],
        "elapsed": session["elapsed"],
        "current_pos_sec": session.get("current_pos_sec", 0),
        "duration_sec": session.get("duration_sec", 0),
        "count": len(detected_signs),
        "signs": detected_signs,
        "group_summary": group_summary,
        "columns": sign_columns,
    })


VN_WEEKDAYS = ["Thứ Hai", "Thứ Ba", "Thứ Tư", "Thứ Năm", "Thứ Sáu", "Thứ Bảy", "Chủ Nhật"]


def format_vn_date(date_str: str) -> str:
    """'2026-08-09' -> 'Thứ Bảy, 09/08/2026' """
    try:
        d = datetime.strptime(date_str, "%Y-%m-%d").date()
        return f"{VN_WEEKDAYS[d.weekday()]}, {d.strftime('%d/%m/%Y')}"
    except Exception:
        return date_str


@app.route("/history")
def history():
    page = max(1, request.args.get("page", 1, type=int))
    per_page = 10

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    all_rows = conn.execute("SELECT * FROM detections ORDER BY id ASC").fetchall()
    conn.close()

    sessions_map = {}
    session_order = []
    for r in all_rows:
        key = (r["timestamp"], r["source_image"])
        if key not in sessions_map:
            sessions_map[key] = {
                "timestamp": r["timestamp"],
                "source_image": r["source_image"],
                "result_image": r["result_image"],
                "rows": [],
            }
            session_order.append(key)
        sessions_map[key]["rows"].append(r)

    session_order.sort(key=lambda k: sessions_map[k]["timestamp"], reverse=True)

    total_sessions = len(session_order)
    total_pages = max(1, (total_sessions + per_page - 1) // per_page)
    page = min(page, total_pages)
    start = (page - 1) * per_page
    page_keys = session_order[start:start + per_page]

    sessions = []
    for key in page_keys:
        s = sessions_map[key]
        source_image = s["source_image"] or ""
        is_video = source_image.lower().endswith((".mp4", ".avi", ".mov", ".mkv"))
        source_type = "Video" if is_video else "Ảnh"

        result_image_rel = s["result_image"]
        image_exists = False
        image_url = None
        if result_image_rel:
            full_path = os.path.join(BASE_DIR, "static", result_image_rel)
            if os.path.exists(full_path):
                image_exists = True
                image_url = url_for("static", filename=result_image_rel)

        sign_payloads = []
        group_counts = {}
        group_badges = {}
        for r in s["rows"]:
            label, badge = get_group(r["class_name"])
            info = get_sign_info(r["class_name"])
            sign_payloads.append({
                "class_name": r["class_name"],
                "sign_name": info["name"],
                "meaning": info["meaning"],
                "group_label": label,
                "badge": badge,
                "confidence": round(r["confidence"] * 100, 1),
            })
            group_counts[label] = group_counts.get(label, 0) + 1
            group_badges[label] = badge

        ts_norm = s["timestamp"].replace("T", " ")
        date_part, time_part = ts_norm.split(" ", 1)

        sessions.append({
            "session_id": f"{key[0]}_{start}_{len(sessions)}".replace(":", "").replace(" ", "_"),
            "date": date_part,
            "time": time_part,
            "source_name": os.path.basename(source_image) if source_image else "(không rõ nguồn)",
            "source_type": source_type,
            "image_url": image_url,
            "has_image": image_exists,
            "sign_count": len(sign_payloads),
            "signs": sign_payloads,
            "group_counts": group_counts,
            "group_badges": group_badges,
        })

    days = []
    current_day = None
    for s in sessions:
        if current_day is None or current_day["date"] != s["date"]:
            current_day = {
                "date": s["date"],
                "display_date": format_vn_date(s["date"]),
                "sessions": [],
            }
            days.append(current_day)
        current_day["sessions"].append(s)

    window = 2
    page_numbers = [p for p in range(page - window, page + window + 1) if 1 <= p <= total_pages]

    return render_template(
        "history.html",
        days=days,
        page=page,
        total_pages=total_pages,
        total_sessions=total_sessions,
        page_numbers=page_numbers,
    )


# ============================================================================
# NEW: Giám sát trực tiếp qua webcam trình duyệt (kiểu camera phạt nguội)
# ============================================================================
WEBCAM_SESSIONS = {}


@app.route("/webcam")
def webcam():
    return render_template("webcam.html")


@app.route("/webcam/start", methods=["POST"])
def webcam_start():
    session_id = uuid.uuid4().hex[:12]
    WEBCAM_SESSIONS[session_id] = {
        "start_time": time.time(),
        "best_per_class": {},
        "thumbnails": {},
        "order": [],
        "frame_count": 0,
    }
    return jsonify({"session_id": session_id})


@app.route("/webcam/detect/<session_id>", methods=["POST"])
def webcam_detect(session_id):
    sess = WEBCAM_SESSIONS.get(session_id)
    if sess is None:
        return jsonify({"error": "not found"}), 404

    file = request.files.get("frame")
    if not file:
        return jsonify({"error": "missing frame"}), 400

    npimg = np.frombuffer(file.read(), np.uint8)
    frame = cv2.imdecode(npimg, cv2.IMREAD_COLOR)
    if frame is None:
        return jsonify({"error": "invalid image"}), 400

    try:
        model = get_model()
    except FileNotFoundError as e:
        return jsonify({"error": str(e)}), 400

    results = model.predict(source=frame, conf=config.CONF_THRESHOLD, verbose=False)
    result = results[0]
    sess["frame_count"] += 1

    thumb_dir = os.path.join(RESULT_DIR, "thumbs")
    os.makedirs(thumb_dir, exist_ok=True)

    boxes_payload = []
    for box in result.boxes:
        cls_id = int(box.cls[0])
        conf = float(box.conf[0])
        class_name = model.names[cls_id]
        x1, y1, x2, y2 = [int(v) for v in box.xyxy[0].tolist()]

        boxes_payload.append({
            "class_name": class_name,
            "confidence": round(conf * 100, 1),
            "box": [x1, y1, x2, y2],
        })

        is_new = class_name not in sess["best_per_class"]
        is_better = is_new or conf > sess["best_per_class"][class_name]
        if is_new:
            sess["order"].append(class_name)

        if is_better:
            sess["best_per_class"][class_name] = conf
            h, w = frame.shape[:2]
            pad = 12
            x1p, y1p = max(0, x1 - pad), max(0, y1 - pad)
            x2p, y2p = min(w, x2 + pad), min(h, y2 + pad)
            crop = frame[y1p:y2p, x1p:x2p].copy()
            if crop.size > 0:
                safe_class = class_name.replace(".", "_")
                thumb_filename = f"webcam_{session_id}_{safe_class}.jpg"
                thumb_path = os.path.join(thumb_dir, thumb_filename)
                cv2.imwrite(thumb_path, crop)
                sess["thumbnails"][class_name] = thumb_filename

                if is_new:
                    admin_username = session.get("admin_username", "admin")
                    threading.Thread(
                        target=telegram_notify.notify_detection_result,
                        kwargs={
                            "username": admin_username,
                            "source_type": "webcam trực tiếp",
                            "signs": [build_sign_payload(class_name, conf)],
                            "image_path": thumb_path,
                        },
                        daemon=True,
                    ).start()
    detected_signs = []
    for class_name in sess["order"]:
        conf = sess["best_per_class"][class_name]
        thumb_filename = sess["thumbnails"].get(class_name)
        thumb_url = url_for("static", filename=f"results/thumbs/{thumb_filename}") if thumb_filename else None
        detected_signs.append(build_sign_payload(class_name, conf, thumb_url=thumb_url))

    group_summary = {}
    for sign in detected_signs:
        group_summary[sign["group_label"]] = group_summary.get(sign["group_label"], 0) + 1

    return jsonify({
        "boxes": boxes_payload,
        "signs": detected_signs,
        "group_summary": group_summary,
        "frame_count": sess["frame_count"],
        "elapsed": round(time.time() - sess["start_time"], 1),
    })


@app.route("/webcam/stop/<session_id>", methods=["POST"])
def webcam_stop(session_id):
    sess = WEBCAM_SESSIONS.get(session_id)
    if sess is None:
        return jsonify({"error": "not found"}), 404

    detections = list(sess["best_per_class"].items())
    if detections:
        save_detections("webcam_live", "", detections)

    WEBCAM_SESSIONS.pop(session_id, None)
    return jsonify({"ok": True, "saved": len(detections)})


# ============================================================================
# NEW: Đánh giá hiệu suất model (mAP, precision, recall, confusion matrix)
# ============================================================================
REPORT_DIR = os.path.join(BASE_DIR, "..", "outputs", "reports", "evaluation")


@app.route("/metrics")
def metrics():
    """Hiển thị kết quả đánh giá model được sinh ra bởi src/evaluate.py.
    Chỉ đọc file JSON/ảnh có sẵn — không chạy lại model."""
    summary_path = os.path.join(REPORT_DIR, "metrics_summary.json")

    if not os.path.exists(summary_path):
        return render_template("metrics.html", has_data=False)

    with open(summary_path, "r", encoding="utf-8") as f:
        summary = json.load(f)

    chart_files = {"confusion_matrix": None, "confusion_matrix_normalized": None,
                   "pr_curve": None, "f1_curve": None}
    if os.path.isdir(REPORT_DIR):
        for fname in os.listdir(REPORT_DIR):
            lower = fname.lower()
            if not lower.endswith(".png"):
                continue
            if "confusion_matrix_normalized" in lower:
                chart_files["confusion_matrix_normalized"] = fname
            elif "confusion_matrix" in lower:
                chart_files["confusion_matrix"] = fname
            elif "pr_curve" in lower:
                chart_files["pr_curve"] = fname
            elif "f1_curve" in lower:
                chart_files["f1_curve"] = fname

    return render_template(
        "metrics.html",
        has_data=True,
        summary=summary,
        charts=chart_files,
    )


@app.route("/metrics/chart/<filename>")
def metrics_chart(filename):
    """Phục vụ ảnh biểu đồ từ outputs/reports/evaluation/."""
    from flask import send_from_directory
    return send_from_directory(REPORT_DIR, filename)

@app.route("/about")
def about():
    system_info = get_system_info()
    return render_template("about.html", system_info=system_info, num_classes=system_info["num_classes"])


@app.route("/classes")
def classes():
    return render_template("classes.html", classes=load_all_classes())


@app.route("/api/classes.json")
def api_classes_json():
    return jsonify(load_all_classes())


@app.route("/reports")
def reports():
    return render_template("reports.html")


@app.route("/api/history_preview")
def api_history_preview():
    date_from = request.args.get("from")
    date_to = request.args.get("to")
    group = request.args.get("group")
    min_conf = float(request.args.get("min_conf", 0))
    limit = int(request.args.get("limit", 10))
    records = load_history_from_db(date_from, date_to, group, min_conf)
    return jsonify({"total": len(records), "records": records[:limit]})


@app.route("/export/excel")
def export_excel():
    records = load_history_from_db(
        request.args.get("from"), request.args.get("to"),
        request.args.get("group"), float(request.args.get("min_conf", 0)),
    )
    buf = build_excel(records)
    return send_file(buf, as_attachment=True,
        download_name=f"lich_su_nhan_dien_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx",
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")


@app.route("/export/pdf")
def export_pdf():
    records = load_history_from_db(
        request.args.get("from"), request.args.get("to"),
        request.args.get("group"), float(request.args.get("min_conf", 0)),
    )
    buf = build_pdf(records)
    return send_file(buf, as_attachment=True,
        download_name=f"bao_cao_nhan_dien_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf",
        mimetype="application/pdf")
@app.route("/api/chat_verify", methods=["POST"])
def chat_verify():
    """Nhận 1 ảnh dán vào chatbot, chạy qua model thật để xác nhận đúng biển gì."""
    file = request.files.get("image")
    if not file:
        return jsonify({"error": "Thiếu ảnh"}), 400

    npimg = np.frombuffer(file.read(), np.uint8)
    frame = cv2.imdecode(npimg, cv2.IMREAD_COLOR)
    if frame is None:
        return jsonify({"error": "Ảnh không hợp lệ"}), 400

    try:
        model = get_model()
    except FileNotFoundError as e:
        return jsonify({"error": str(e)}), 400

    results = model.predict(source=frame, conf=config.CONF_THRESHOLD, verbose=False)
    result = results[0]

    thumb_dir = os.path.join(RESULT_DIR, "thumbs")
    os.makedirs(thumb_dir, exist_ok=True)
    session_tag = uuid.uuid4().hex[:8]

    signs = []
    for idx, box in enumerate(result.boxes):
        cls_id = int(box.cls[0])
        conf = float(box.conf[0])
        class_name = model.names[cls_id]

        x1, y1, x2, y2 = [int(v) for v in box.xyxy[0].tolist()]
        h, w = frame.shape[:2]
        pad = 12
        x1p, y1p = max(0, x1 - pad), max(0, y1 - pad)
        x2p, y2p = min(w, x2 + pad), min(h, y2 + pad)
        crop = frame[y1p:y2p, x1p:x2p]

        thumb_url = None
        if crop.size > 0:
            safe_class = class_name.replace(".", "_")
            thumb_filename = f"chat_{session_tag}_{idx}_{safe_class}.jpg"
            cv2.imwrite(os.path.join(thumb_dir, thumb_filename), crop)
            thumb_url = url_for("static", filename=f"results/thumbs/{thumb_filename}")

        signs.append(build_sign_payload(class_name, conf, thumb_url=thumb_url))

    return jsonify({"signs": signs})
if __name__ == "__main__":
    init_db()
    auth.init_auth_db()  # NEW: tạo bảng admin + tài khoản admin mặc định nếu chưa có
    print("Dashboard chạy tại: http://127.0.0.1:5000")
    print("Trang đăng nhập  : http://127.0.0.1:5000/login")
    app.run(host="0.0.0.0", debug=True, port=5000, use_reloader=False, threaded=True)