# Hệ thống nhận diện và phân loại biển báo giao thông Việt Nam

Dự án sử dụng YOLOv8 (Ultralytics) để phát hiện (detect) và phân loại (classify) biển báo giao thông Việt Nam từ ảnh, video hoặc webcam.

## 1. Cài đặt

```bash
pip install -r requirements.txt
```

## 2. Cấu trúc dự án

```
data/            Dữ liệu ảnh và nhãn (train/val/test)
models/          Model pretrained và model đã huấn luyện
src/             Mã nguồn chính (train, predict, evaluate, webcam...)
gui/             Giao diện demo đơn giản (Tkinter)
notebooks/       Notebook thử nghiệm, phân tích dữ liệu
runs/            Log và kết quả huấn luyện (Ultralytics tự tạo)
outputs/         Ảnh kết quả nhận diện, báo cáo đánh giá
```

## 3. Chuẩn bị dữ liệu

1. Đặt ảnh gốc vào `data/raw/images/` và nhãn (định dạng YOLO `.txt`) vào `data/raw/labels/`.
2. Chạy lệnh sau để tự động chia train/val/test (tỉ lệ 70/20/10):

```bash
python src/data_preprocessing.py
```

3. Mở `data/data.yaml`, cập nhật đúng **số lượng lớp** (`nc`) và **tên các lớp** (`names`) theo bộ dữ liệu thực tế của bạn.

### Định dạng nhãn YOLO

Mỗi ảnh `ten_anh.jpg` cần một file nhãn tương ứng `ten_anh.txt` với mỗi dòng là một đối tượng:

```
class_id x_center y_center width height
```

Các giá trị tọa độ được chuẩn hóa trong khoảng 0–1 (chia cho chiều rộng/chiều cao ảnh).

## 4. Huấn luyện model

```bash
python src/train.py
```

Model tốt nhất sẽ được lưu tại `runs/train/traffic_sign_vn/weights/best.pt`. Sau khi train xong, copy file này vào `models/trained/best.pt` để các script khác (predict, webcam, gui) sử dụng.

## 5. Đánh giá model

```bash
python src/evaluate.py
```

## 6. Nhận diện trên ảnh

```bash
python src/predict.py --image duong_dan_anh.jpg
```

## 7. Nhận diện qua webcam (real-time)

```bash
python src/webcam_detect.py
```

Nhấn phím `q` để thoát.

## 8. Giao diện demo (Tkinter)

```bash
python gui/app.py
```

## 9. Chạy qua menu chính

```bash
python main.py
```

## Ghi chú

- Nếu máy không có GPU rời (NVIDIA), nên train model trên Google Colab hoặc Kaggle (có GPU miễn phí) để tiết kiệm thời gian, sau đó tải file `best.pt` về máy để dùng cho các bước còn lại.
- Model `yolov8n.pt` (nano) là bản nhẹ nhất, phù hợp máy cấu hình thấp. Có thể đổi sang `yolov8s.pt`, `yolov8m.pt`... trong `src/train.py` nếu muốn độ chính xác cao hơn (cần máy mạnh hơn).
