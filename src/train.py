from ultralytics import YOLO
import config


def train_model():
    # Load model YOLOv8 pretrained (nano - nhẹ, phù hợp máy yếu/không GPU)
    model = YOLO("yolov8n.pt")  # tự động tải về nếu chưa có

    # Bắt đầu huấn luyện
    results = model.train(
        data=config.DATA_YAML,
        epochs=config.EPOCHS,
        imgsz=config.IMG_SIZE,
        batch=config.BATCH_SIZE,
        project="runs/train",
        name="traffic_sign_vn",
        patience=20,          # dừng sớm nếu không cải thiện sau 20 epoch
        save=True,
        workers=2,             # giảm số luồng load dữ liệu để tiết kiệm bộ nhớ
        cache=False,           # không cache ảnh vào RAM
        amp=True               # giữ mixed precision để tiết kiệm VRAM
    )

    print("Huấn luyện hoàn tất. Model tốt nhất lưu tại: runs/train/traffic_sign_vn/weights/best.pt")


if __name__ == "__main__":
    train_model()