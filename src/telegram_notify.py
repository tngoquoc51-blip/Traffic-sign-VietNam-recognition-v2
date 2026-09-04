# -*- coding: utf-8 -*-
"""
telegram_notify.py — Gửi thông báo tự động về Telegram cho Admin
- Thông báo khi có ai đăng nhập vào hệ thống (giám sát bảo mật)
- Thông báo kết quả mỗi lần nhận diện ảnh / video (biển báo gì, nhóm gì, độ tin cậy)

CẤU HÌNH TELEGRAM BOT (bắt buộc để tính năng này hoạt động):
    1. Mở Telegram, tìm và nhắn chuyện với tài khoản @BotFather
    2. Gửi lệnh: /newbot
    3. Đặt tên bot tùy ý (vd: TrafficVision Notify), rồi đặt username kết thúc bằng "bot"
       (vd: trafficvision_notify_bot)
    4. BotFather trả về 1 chuỗi TOKEN dạng: 123456789:AAExxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
       -> Dán vào biến TELEGRAM_BOT_TOKEN bên dưới
    5. Lấy CHAT_ID (ID cuộc trò chuyện của bạn với bot):
       a. Mở bot vừa tạo, bấm "Start" hoặc gửi bất kỳ tin nhắn nào (vd: "hi") cho bot
       b. Mở trình duyệt, truy cập:
          https://api.telegram.org/bot<TOKEN_CỦA_BẠN>/getUpdates
          (thay <TOKEN_CỦA_BẠN> bằng token thật ở bước 4)
       c. Tìm trong kết quả JSON trả về, có đoạn "chat":{"id": 123456789, ...}
          -> Số đó chính là CHAT_ID, dán vào biến TELEGRAM_CHAT_ID bên dưới
    6. Cài thư viện requests nếu chưa có: pip install requests
"""

import os
import time
import threading
from datetime import datetime

try:
    import requests
except ImportError:
    requests = None  # sẽ báo lỗi rõ ràng khi thực sự gửi, không làm crash lúc import

# ---------------------------------------------------------------------------
# CẤU HÌNH TELEGRAM BOT — SỬA 2 DÒNG DƯỚI ĐÂY THEO BOT CỦA BẠN
# ---------------------------------------------------------------------------
TELEGRAM_BOT_TOKEN = os.environ.get("TRAFFICVISION_TELEGRAM_TOKEN", "8824892780:AAEFDoEU3fOqO0V76aFqH3vijLlDd283T0o")
TELEGRAM_CHAT_ID = os.environ.get("TRAFFICVISION_TELEGRAM_CHAT_ID", "7511794727")

TELEGRAM_API_BASE = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}"

# Giới hạn số biển báo liệt kê chi tiết trong 1 tin nhắn, tránh tin nhắn quá dài
MAX_SIGNS_LISTED = 15


def _is_configured() -> bool:
    return (
        TELEGRAM_BOT_TOKEN not in ("", "your_bot_token_here")
        and TELEGRAM_CHAT_ID not in ("", "your_chat_id_here")
        and requests is not None
    )


def send_message(text: str, retries: int = 3) -> bool:
    """Gửi tin nhắn văn bản. Tự động thử lại nếu thất bại (mạng chập chờn). Trả về True nếu thành công."""
    if not _is_configured():
        print("[Telegram] Chưa cấu hình TOKEN/CHAT_ID (hoặc thiếu thư viện requests) — bỏ qua gửi thông báo.")
        return False
    for attempt in range(1, retries + 1):
        try:
            resp = requests.post(
                f"{TELEGRAM_API_BASE}/sendMessage",
                data={"chat_id": TELEGRAM_CHAT_ID, "text": text, "parse_mode": "HTML"},
                timeout=10,
            )
            if resp.ok:
                return True
            print(f"[Telegram] Gửi tin nhắn thất bại (lần {attempt}/{retries}): {resp.status_code} {resp.text}")
        except Exception as e:
            print(f"[Telegram] Lỗi khi gửi tin nhắn (lần {attempt}/{retries}): {e}")
        if attempt < retries:
            time.sleep(2)  # chờ 2 giây trước khi thử lại
    return False


def send_photo(photo_path: str, caption: str = "", retries: int = 3) -> bool:
    """Gửi 1 ảnh kèm chú thích. Tự động thử lại nếu thất bại. Trả về True nếu thành công."""
    if not _is_configured():
        print("[Telegram] Chưa cấu hình TOKEN/CHAT_ID (hoặc thiếu thư viện requests) — bỏ qua gửi ảnh.")
        return False
    if not os.path.exists(photo_path):
        print(f"[Telegram] Không tìm thấy file ảnh: {photo_path}")
        return False
    for attempt in range(1, retries + 1):
        try:
            with open(photo_path, "rb") as f:
                resp = requests.post(
                    f"{TELEGRAM_API_BASE}/sendPhoto",
                    data={"chat_id": TELEGRAM_CHAT_ID, "caption": caption[:1024], "parse_mode": "HTML"},
                    files={"photo": f},
                    timeout=20,
                )
            if resp.ok:
                return True
            print(f"[Telegram] Gửi ảnh thất bại (lần {attempt}/{retries}): {resp.status_code} {resp.text}")
        except Exception as e:
            print(f"[Telegram] Lỗi khi gửi ảnh (lần {attempt}/{retries}): {e}")
        if attempt < retries:
            time.sleep(2)
    return False


def _run_async(func, *args, **kwargs):
    """Chạy hàm gửi trong luồng nền, không làm chậm phản hồi của web app."""
    threading.Thread(target=func, args=args, kwargs=kwargs, daemon=True).start()


# ---------------------------------------------------------------------------
# Thông báo giám sát đăng nhập — biết AI đang dùng hệ thống
# ---------------------------------------------------------------------------
def notify_admin_login(username: str, ip_address: str):
    text = (
        f"🔐 <b>Có người đăng nhập vào hệ thống</b>\n"
        f"Tài khoản: <b>{username}</b>\n"
        f"Địa chỉ IP: <code>{ip_address}</code>\n"
        f"Thời gian: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}"
    )
    _run_async(send_message, text)


# ---------------------------------------------------------------------------
# Thông báo kết quả nhận diện — biết ai đã quét gì, phân loại ra sao
# ---------------------------------------------------------------------------
def notify_detection_result(username: str, source_type: str, signs: list, image_path: str = None):
    """
    username: người thực hiện (lấy từ session admin_username)
    source_type: 'ảnh' hoặc 'video'
    signs: list các dict có ít nhất class_name, sign_name, group_label, confidence
    image_path: đường dẫn ảnh minh họa (ảnh gốc/annotated hoặc ảnh cắt biển báo), có thể None
    """
    timestamp = datetime.now().strftime("%d/%m/%Y %H:%M:%S")

    if not signs:
        text = (
            f"📷 <b>Kết quả nhận diện {source_type}</b>\n"
            f"Người thực hiện: <b>{username}</b>\n"
            f"Thời gian: {timestamp}\n"
            f"Kết quả: Không phát hiện biển báo nào."
        )
        _run_async(send_message, text)
        return

    lines = [
        f"📷 <b>Kết quả nhận diện {source_type}</b>",
        f"Người thực hiện: <b>{username}</b>",
        f"Thời gian: {timestamp}",
        f"Số biển phát hiện: <b>{len(signs)}</b>",
        "",
        "<b>Chi tiết:</b>",
    ]
    for s in signs[:MAX_SIGNS_LISTED]:
        lines.append(
            f"• {s.get('class_name','?')} — {s.get('sign_name','?')} "
            f"({s.get('group_label','?')}) — {s.get('confidence','?')}%"
        )
    if len(signs) > MAX_SIGNS_LISTED:
        lines.append(f"... và {len(signs) - MAX_SIGNS_LISTED} biển khác")

    text = "\n".join(lines)

    if image_path and os.path.exists(image_path):
        _run_async(send_photo, image_path, text)
    else:
        _run_async(send_message, text)