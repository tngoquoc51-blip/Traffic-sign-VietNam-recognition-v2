import os

# Đường dẫn thư mục gốc dự án
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Đường dẫn dữ liệu
DATA_YAML = os.path.join(ROOT_DIR, "data", "data.yaml")

# Đường dẫn model
PRETRAINED_MODEL = os.path.join(ROOT_DIR, "models", "pretrained", "yolov8n.pt")
TRAINED_MODEL = os.path.join(ROOT_DIR, "models", "trained", "best.pt")

# Tham số huấn luyện
EPOCHS = 100
IMG_SIZE = 640
BATCH_SIZE = 4
# Ngưỡng tin cậy khi nhận diện (confidence threshold)
CONF_THRESHOLD = 0.5
