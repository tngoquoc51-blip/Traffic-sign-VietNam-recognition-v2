from ultralytics import YOLO
import config
import cv2


def run_webcam(model_path=config.TRAINED_MODEL, camera_index=0):
    model = YOLO(model_path)
    cap = cv2.VideoCapture(camera_index)

    if not cap.isOpened():
        print("Không mở được webcam.")
        return

    print("Nhấn 'q' để thoát.")
    while True:
        ret, frame = cap.read()
        if not ret:
            break

        results = model.predict(frame, conf=config.CONF_THRESHOLD, verbose=False)
        annotated_frame = results[0].plot()  # vẽ bounding box lên frame

        cv2.imshow("Nhan dien bien bao giao thong VN", annotated_frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    run_webcam()
