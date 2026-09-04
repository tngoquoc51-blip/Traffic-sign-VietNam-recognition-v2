# -*- coding: utf-8 -*-
"""
auth.py — Xác thực quản trị viên (Admin) cho TrafficVision AI
- Đăng nhập / đăng xuất admin
- Quên mật khẩu: gửi mã xác nhận 6 số qua Gmail, xác thực mã, đặt lại mật khẩu
- Dùng chung SQLite database với detections.db (thêm 2 bảng: admins, password_resets)

CẤU HÌNH GMAIL (bắt buộc để tính năng "Quên mật khẩu" hoạt động):
    Gmail đã tắt đăng nhập bằng mật khẩu thường cho ứng dụng bên ngoài, bạn cần tạo
    "Mật khẩu ứng dụng" (App Password) cho Gmail:
    1. Bật xác minh 2 bước cho tài khoản Gmail: https://myaccount.google.com/security
    2. Tạo App Password tại: https://myaccount.google.com/apppasswords
    3. Điền email Gmail + App Password (16 ký tự) vào 2 biến MAIL_SENDER_EMAIL và
       MAIL_APP_PASSWORD bên dưới, HOẶC set biến môi trường trước khi chạy:
           set TRAFFICVISION_MAIL_EMAIL=your_email@gmail.com        (Windows)
           set TRAFFICVISION_MAIL_APP_PASSWORD=xxxxxxxxxxxxxxxx
       hoặc trên macOS/Linux dùng lệnh export thay cho set.
"""

import os
import sqlite3
import random
import smtplib
import string
from email.mime.text import MIMEText
from datetime import datetime, timedelta
from functools import wraps

from flask import session, redirect, url_for, request, flash
from werkzeug.security import generate_password_hash, check_password_hash

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # thư mục gốc dự án
AUTH_DB_PATH = os.path.join(BASE_DIR, "gui", "detections.db")  # dùng chung DB với lịch sử nhận diện

# ---------------------------------------------------------------------------
# CẤU HÌNH GỬI EMAIL QUA GMAIL — SỬA 2 DÒNG DƯỚI ĐÂY THEO GMAIL CỦA BẠN
# ---------------------------------------------------------------------------
MAIL_SENDER_EMAIL = os.environ.get("TRAFFICVISION_MAIL_EMAIL", "tngoquoc51@gmail.com")
MAIL_APP_PASSWORD = os.environ.get("TRAFFICVISION_MAIL_APP_PASSWORD", "xrgu spud kuog oqej")
MAIL_SMTP_HOST = "smtp.gmail.com"
MAIL_SMTP_PORT = 587

RESET_CODE_LENGTH = 6
RESET_CODE_EXPIRY_MINUTES = 10

# Tài khoản admin mặc định được tạo tự động lần đầu chạy hệ thống (nếu chưa có admin nào)
DEFAULT_ADMIN_USERNAME = "admin"
DEFAULT_ADMIN_PASSWORD = "admin123"
DEFAULT_ADMIN_EMAIL = "admin@example.com"  # ĐỔI thành email Gmail thật của bạn để nhận mã khôi phục


# ---------------------------------------------------------------------------
# Database helpers
# ---------------------------------------------------------------------------
def _get_conn():
    conn = sqlite3.connect(AUTH_DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_auth_db():
    """Tạo bảng admins / password_resets nếu chưa có, và tạo admin mặc định lần đầu."""
    conn = _get_conn()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS admins (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS password_resets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT NOT NULL,
            code TEXT NOT NULL,
            expires_at TEXT NOT NULL,
            used INTEGER NOT NULL DEFAULT 0,
            created_at TEXT NOT NULL
        )
    """)
    conn.commit()

    existing = conn.execute("SELECT COUNT(*) AS c FROM admins").fetchone()["c"]
    if existing == 0:
        conn.execute(
            "INSERT INTO admins (username, email, password_hash, created_at) VALUES (?, ?, ?, ?)",
            (
                DEFAULT_ADMIN_USERNAME,
                DEFAULT_ADMIN_EMAIL,
                generate_password_hash(DEFAULT_ADMIN_PASSWORD),
                datetime.now().isoformat(timespec="seconds"),
            ),
        )
        conn.commit()
        print("=" * 72)
        print("  Đã tạo tài khoản ADMIN mặc định cho lần chạy đầu tiên:")
        print(f"     Tài khoản : {DEFAULT_ADMIN_USERNAME}")
        print(f"     Mật khẩu  : {DEFAULT_ADMIN_PASSWORD}")
        print(f"     Email     : {DEFAULT_ADMIN_EMAIL}")
        print("  Hãy đăng nhập rồi đổi mật khẩu/email này ngay để bảo mật!")
        print("  (Email dùng để nhận mã khôi phục mật khẩu qua Gmail)")
        print("=" * 72)
    conn.close()


def verify_admin(username_or_email: str, password: str):
    """Kiểm tra tài khoản/mật khẩu đăng nhập. Trả về dict admin nếu đúng, None nếu sai."""
    conn = _get_conn()
    row = conn.execute(
        "SELECT * FROM admins WHERE username = ? OR email = ?",
        (username_or_email, username_or_email),
    ).fetchone()
    conn.close()
    if row and check_password_hash(row["password_hash"], password):
        return dict(row)
    return None


def get_admin_by_email(email: str):
    conn = _get_conn()
    row = conn.execute("SELECT * FROM admins WHERE email = ?", (email,)).fetchone()
    conn.close()
    return dict(row) if row else None


def update_admin_account(admin_id: int, username: str = None, email: str = None, new_password: str = None):
    """Cho phép admin tự đổi username / email / mật khẩu sau khi đăng nhập."""
    conn = _get_conn()
    if username:
        conn.execute("UPDATE admins SET username = ? WHERE id = ?", (username, admin_id))
    if email:
        conn.execute("UPDATE admins SET email = ? WHERE id = ?", (email, admin_id))
    if new_password:
        conn.execute(
            "UPDATE admins SET password_hash = ? WHERE id = ?",
            (generate_password_hash(new_password), admin_id),
        )
    conn.commit()
    conn.close()


# ---------------------------------------------------------------------------
# Quên mật khẩu — sinh mã, xác thực mã, đặt lại mật khẩu
# ---------------------------------------------------------------------------
def generate_reset_code(email: str) -> str:
    code = "".join(random.choices(string.digits, k=RESET_CODE_LENGTH))
    expires_at = (datetime.now() + timedelta(minutes=RESET_CODE_EXPIRY_MINUTES)).isoformat(timespec="seconds")
    conn = _get_conn()
    conn.execute(
        "INSERT INTO password_resets (email, code, expires_at, used, created_at) VALUES (?, ?, ?, 0, ?)",
        (email, code, expires_at, datetime.now().isoformat(timespec="seconds")),
    )
    conn.commit()
    conn.close()
    return code


def verify_reset_code(email: str, code: str) -> bool:
    conn = _get_conn()
    row = conn.execute(
        "SELECT * FROM password_resets WHERE email = ? AND code = ? AND used = 0 ORDER BY id DESC LIMIT 1",
        (email, code),
    ).fetchone()
    conn.close()
    if not row:
        return False
    try:
        expires_at = datetime.fromisoformat(row["expires_at"])
    except ValueError:
        return False
    return datetime.now() <= expires_at


def mark_code_used(email: str, code: str):
    conn = _get_conn()
    conn.execute(
        "UPDATE password_resets SET used = 1 WHERE email = ? AND code = ?", (email, code)
    )
    conn.commit()
    conn.close()


def update_admin_password(email: str, new_password: str):
    conn = _get_conn()
    conn.execute(
        "UPDATE admins SET password_hash = ? WHERE email = ?",
        (generate_password_hash(new_password), email),
    )
    conn.commit()
    conn.close()


def send_reset_email(to_email: str, code: str) -> tuple:
    """Gửi mã xác nhận đặt lại mật khẩu qua Gmail SMTP.
    Trả về (thành_công: bool, thông_báo_lỗi: str hoặc None)."""
    subject = "TrafficVision AI - Mã xác nhận đặt lại mật khẩu"
    body = (
        "Xin chào,\n\n"
        "Bạn (hoặc ai đó) vừa yêu cầu đặt lại mật khẩu quản trị cho hệ thống TrafficVision AI.\n\n"
        f"Mã xác nhận của bạn là: {code}\n\n"
        f"Mã có hiệu lực trong {RESET_CODE_EXPIRY_MINUTES} phút. "
        "Nếu bạn không yêu cầu điều này, vui lòng bỏ qua email này.\n\n"
        "Trân trọng,\nTrafficVision AI"
    )
    msg = MIMEText(body, "plain", "utf-8")
    msg["Subject"] = subject
    msg["From"] = MAIL_SENDER_EMAIL
    msg["To"] = to_email

    try:
        with smtplib.SMTP(MAIL_SMTP_HOST, MAIL_SMTP_PORT, timeout=15) as server:
            server.starttls()
            server.login(MAIL_SENDER_EMAIL, MAIL_APP_PASSWORD)
            server.sendmail(MAIL_SENDER_EMAIL, [to_email], msg.as_string())
        return True, None
    except Exception as e:
        return False, str(e)


# ---------------------------------------------------------------------------
# Decorator bảo vệ route — chỉ admin đã đăng nhập mới được truy cập
# ---------------------------------------------------------------------------
def login_required(view_func):
    @wraps(view_func)
    def wrapped_view(*args, **kwargs):
        if not session.get("admin_logged_in"):
            flash("Vui lòng đăng nhập để tiếp tục.")
            return redirect(url_for("login", next=request.path))
        return view_func(*args, **kwargs)
    return wrapped_view