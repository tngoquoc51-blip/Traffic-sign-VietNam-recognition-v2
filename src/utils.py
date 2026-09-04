"""Các hàm phụ trợ dùng chung cho dự án."""

import os
import yaml


def load_class_names(data_yaml_path):
    """Đọc danh sách tên lớp từ file data.yaml."""
    with open(data_yaml_path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return data.get("names", {})


def ensure_dir(path):
    """Tạo thư mục nếu chưa tồn tại."""
    os.makedirs(path, exist_ok=True)
    return path


def count_images(folder_path, extensions=(".jpg", ".jpeg", ".png")):
    """Đếm số lượng ảnh trong một thư mục."""
    if not os.path.isdir(folder_path):
        return 0
    return len([f for f in os.listdir(folder_path) if f.lower().endswith(extensions)])
