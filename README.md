<h1 align="center">HỆ THỐNG VƯỜN THÔNG MINH SỬ DỤNG IoT VÀ AI</h1>

<div align="center">

<p align="center">
  <img src="logo.png" alt="DaiNam University Logo" width="200"/>
  <img src="AIoTLab_logo.png" alt="AIoTLab Logo" width="170"/>
</p>

[![Made by AIoTLab](https://img.shields.io/badge/Made%20by%20AIoTLab-blue?style=for-the-badge)](https://www.facebook.com/DNUAIoTLab)
[![Fit DNU](https://img.shields.io/badge/Fit%20DNU-green?style=for-the-badge)](https://fitdnu.net/)
[![DaiNam University](https://img.shields.io/badge/DaiNam%20University-red?style=for-the-badge)](https://dainam.edu.vn)

</div>

<h2 align="center">Hệ thống vườn thông minh sử dụng IoT và AI</h2>

<p align="left">
  Dự án này tập trung vào việc xây dựng một hệ thống vườn thông minh sử dụng IoT và trí tuệ nhân tạo. Bằng cách kết hợp các cảm biến môi trường, vi điều khiển và Machine Learning, hệ thống có thể theo dõi và tự động điều chỉnh các điều kiện phù hợp nhất cho sự phát triển của cây trồng.
</p>

---

## 🌟 Giới thiệu

- **📌 Thu thập dữ liệu:** Sử dụng các cảm biến nhiệt độ, độ ẩm, ánh sáng và độ ẩm đất để theo dõi môi trường cây trồng.
- **🤖 Xử lý bằng AI:** Ứng dụng Machine Learning để phân tích các điều kiện tối ưu và dự đoán nhu cầu tưới nước.
- **🎮 Ứng dụng thực tế:** Tự động điều khiển hệ thống tưới nước, đèn LED và các thiết bị khác để duy trì môi trường lý tưởng.
- **📊 Lưu trữ và quản lý dữ liệu:** Sử dụng tệp CSV để lưu trữ dữ liệu cảm biến, thuận tiện cho xử lý và huấn luyện mô hình.

---
## 🏗️ HỆ THỐNG
<p align="center">
  <img src="Picture1.png" alt="System Architecture" width="800"/>
</p>

---
## 📦 Dự án Vườn Thông Minh  
├── 📁 Mô hình                # Chứa mô hình AI đã huấn luyện  
│   ├── garden_model.pkl           # Mô hình đã lưu  
│   ├── model_train.py     # Notebook huấn luyện mô hình  
│  
├── 📁 dulieududoan           # Dữ liệu đầu vào để dự đoán  
│  
├── 📁 guidulieu              # Hướng dẫn xử lý dữ liệu  
│  
├── 📁 image                  # Hình ảnh minh họa
│  
├── 📁 static                 # CSS, JS, hình ảnh tĩnh phục vụ giao diện web  
│  
├── 📁 templates              # HTML template cho Flask server  
│  
├── 📁 sensors                # Mã nguồn cho các cảm biến và thiết bị  
│  
├── 📁 data                   # Lưu dữ liệu môi trường được ghi nhận  
│  
├── .gitignore                # Danh sách file cần bỏ qua khi push lên Git  
│  
├── main.py                   # Chương trình chính để điều khiển và giám sát vườn thông minh  
│  
├── data_process.py           # Xử lý dữ liệu từ file CSV để huấn luyện mô hình  
│  
├── garden_data.csv           # Dữ liệu mẫu dùng cho huấn luyện  
│  
├── README.md                 # Tài liệu hướng dẫn dự án  



## 🛠️ CÔNG NGHỆ SỬ DỤNG

<div align="center">

### 🔌 Phần cứng
[![ESP32](https://img.shields.io/badge/ESP32-Microcontroller-blue?style=for-the-badge)](https://www.espressif.com/en/products/socs/esp32)
[![Arduino](https://img.shields.io/badge/Arduino-Platform-teal?style=for-the-badge&logo=arduino)](https://www.arduino.cc/)
[![DHT22](https://img.shields.io/badge/DHT22-Temperature/Humidity-green?style=for-the-badge)](https://www.adafruit.com/product/385)
[![Soil Moisture](https://img.shields.io/badge/Soil_Moisture-Sensor-brown?style=for-the-badge)]()
[![Light Sensor](https://img.shields.io/badge/Light-Sensor-yellow?style=for-the-badge)]()
[![Water Pump](https://img.shields.io/badge/Water_Pump-Actuator-blue?style=for-the-badge)]()
[![LED Grow Lights](https://img.shields.io/badge/LED_Grow_Lights-Actuator-purple?style=for-the-badge)]()

### 🖥️ Phần mềm
[![Python](https://img.shields.io/badge/Python-3.x-blue?style=for-the-badge&logo=python)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-Microservice%20API-black?style=for-the-badge&logo=flask)](https://flask.palletsprojects.com/)
[![NumPy](https://img.shields.io/badge/NumPy-Numerical%20Computing-orange?style=for-the-badge)](https://numpy.org/)
[![Pandas](https://img.shields.io/badge/Pandas-Data%20Processing-blue?style=for-the-badge)](https://pandas.pydata.org/)
[![Matplotlib](https://img.shields.io/badge/Matplotlib-Visualization-green?style=for-the-badge)](https://matplotlib.org/)

</div>

## 🛠️ YÊU CẦU HỆ THỐNG

### 🔌 Phần cứng
- **ESP32/ESP8266** để kết nối mạng và điều khiển thiết bị.
- **Arduino** (tùy chọn) để mở rộng khả năng kết nối với nhiều cảm biến.
- **DHT22** - Cảm biến nhiệt độ và độ ẩm không khí.
- **Cảm biến độ ẩm đất** để theo dõi độ ẩm trong đất.
- **Cảm biến ánh sáng** để đo lường cường độ ánh sáng.
- **Bơm nước mini** để tự động tưới cây.
- **Đèn LED trồng cây** để bổ sung ánh sáng khi cần thiết.

### 💻 Phần mềm
- **🐍 Python 3+** (Yêu cầu thư viện: NumPy, Pandas, Flask, TensorFlow, Scikit-learn, Matplotlib).
- **📡 Flask Server** để xử lý dữ liệu và điều khiển từ xa.
- **📊 CSV** để lưu trữ dữ liệu môi trường.

## 📦 CÁC THƯ VIỆN PYTHON CẦN THIẾT

Để chạy dự án, bạn cần cài đặt các thư viện sau bằng lệnh:

```
pip install numpy pandas flask tensorflow scikit-learn matplotlib pyserial
```

## 📖 Hướng dẫn sử dụng  

### 🌱 Theo dõi và chăm sóc vườn thông minh  
1️⃣ **Giám sát môi trường** 🌡️  
   - **Nhiệt độ và độ ẩm không khí** → Hiển thị trên dashboard 📊  
   - **Độ ẩm đất** → Theo dõi và cảnh báo khi quá khô 🔔  
   - **Ánh sáng** → Đo lường và điều chỉnh 💡  

2️⃣ **Điều khiển tự động** 🤖  
   - **Tưới nước tự động** 💧 → Kích hoạt khi độ ẩm đất dưới ngưỡng  
   - **Bật/tắt đèn LED** 💡 → Tự động khi thiếu ánh sáng  

---

### 💡 Điều khiển thủ công  
1️⃣ **Bật/tắt bơm nước** 💧  
   - **Qua giao diện web** → Điều khiển thủ công từ xa  

2️⃣ **Bật/tắt đèn LED** 💡  
   - **Qua giao diện web** → Điều chỉnh độ sáng và thời gian  

---

### ⚙️ Lưu ý  
- Đảm bảo **ESP32/ESP8266** đã kết nối với **WiFi** và nhận tín hiệu từ các cảm biến.  
- Kiểm tra nguồn điện cho bơm nước và đèn LED trước khi vận hành.  
- Nếu hệ thống không phản hồi, kiểm tra kết nối với **Flask Server**.  
 

## 📰 Poster
<p align="center">
  <img src="Poster.JPG" alt="Smart Garden Poster" width="800"/>
</p>

## 🤝 Đóng góp
Dự án được phát triển bởi 4 thành viên:

| Họ và Tên              | Vai trò                                                                 |
|------------------------|------------------------------------------------------------------------|
| Vũ Triệu Phú       | Phát triển toàn bộ mã nguồn, kiểm thử, triển khai dự án, Overleaf, và thực hiện video giới thiệu. |
| Ngô Hữu Hoàng      | Powerpoint, Code giao diện esp32 , edit full video , đề xuất cải tiến, và hỗ trợ bài tập lớn. |
| Nguyễn Quốc Hưng   | Poster, đề xuất cải tiến, và hỗ trợ bài tập lớn.. |
| Đỗ Quốc Việt       |  Poster, thuyết trình , đề xuất cải tiến, và hỗ trợ bài tập lớn. |


© 2025 NHÓM 4, CNTT16-02, TRƯỜNG ĐẠI HỌC ĐẠI NAM


