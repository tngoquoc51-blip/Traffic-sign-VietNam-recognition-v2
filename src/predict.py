from ultralytics import YOLO
import config
import argparse


def predict_image(image_path, model_path=config.TRAINED_MODEL):
    model = YOLO(model_path)
    results = model.predict(
        source=image_path,
        conf=config.CONF_THRESHOLD,
        save=True,
        project="outputs/predictions",
        name="result"
    )

    for result in results:
        boxes = result.boxes
        print(f"Phát hiện {len(boxes)} biển báo:")
        for box in boxes:
            cls_id = int(box.cls[0])
            conf = float(box.conf[0])
            class_name = model.names[cls_id]
            print(f"  - {class_name} (độ tin cậy: {conf:.2f})")

    print("Ảnh kết quả đã lưu trong outputs/predictions/result/")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--image", type=str, required=True, help="Đường dẫn ảnh cần nhận diện")
    args = parser.parse_args()
    predict_image(args.image)
