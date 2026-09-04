from src.train import train_model
from src.predict import predict_image
from src.webcam_detect import run_webcam
from src.evaluate import evaluate_model

def main():
    print("=== HỆ THỐNG NHẬN DIỆN BIỂN BÁO GIAO THÔNG VIỆT NAM ===")
    print("1. Huấn luyện model")
    print("2. Nhận diện trên ảnh")
    print("3. Nhận diện qua webcam")
    print("4. Đánh giá model")
    choice = input("Chọn chức năng (1/2/3/4): ")

    if choice == "1":
        train_model()
    elif choice == "2":
        img_path = input("Nhập đường dẫn ảnh: ")
        predict_image(img_path)
    elif choice == "3":
        run_webcam()
    elif choice == "4":
        evaluate_model()
    else:
        print("Lựa chọn không hợp lệ.")


if __name__ == "__main__":
    main()
