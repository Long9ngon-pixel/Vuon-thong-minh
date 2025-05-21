import os
import cv2
import numpy as np
import pickle
import threading
import queue
import json
import time
import base64
import io
from datetime import datetime
from flask import Flask, request, jsonify, render_template, send_from_directory, Response
from flask_cors import CORS
import speech_recognition as sr
import pyaudio
import wave
import serial
import serial.tools.list_ports
from insightface.app import FaceAnalysis
from ultralytics import YOLO  # Thêm YOLOv8

# Cấu hình Flask phù hợp với cấu trúc thư mục
app = Flask(__name__, 
            static_folder='static',
            template_folder='templates')
CORS(app)  # Enable CORS

# Load face database
face_db = {}
if os.path.exists("face_db.pkl"):
    with open("face_db.pkl", "rb") as f:
        face_db = pickle.load(f)

# Initialize InsightFace
face_app = FaceAnalysis(providers=['CPUExecutionProvider'])
face_app.prepare(ctx_id=0, det_size=(640, 640))

# Initialize YOLOv8 model
yolo_model = None
try:
    yolo_model = YOLO("yolov8n.pt")
    print("✅ YOLO model loaded successfully")
except Exception as e:
    print(f"❌ Failed to load YOLO model: {e}")

# Authentication status
auth_status = {
    "authenticated": False,
    "user": None,
    "last_update": None
}

# Sensor data
sensor_data = {
    "temperature": "28",
    "soil_moisture": "60%",
    "light": "750",
    "water_level": "75%"
}

# Pump state
pump_state = {
    "state": False
}

# Camera and face recognition variables
camera = None
face_recognition_active = False
frame_queue = queue.Queue(maxsize=1)

# ESP32-CAM variables
esp32cam_ip = "192.168.164.55"  # Cập nhật địa chỉ IP mặc định của ESP32-CAM
esp32cam_port = "81"            # Cổng mặc định
esp32cam_url = f"http://{esp32cam_ip}:{esp32cam_port}/stream"
esp32cam_active = False
esp32cam_queue = queue.Queue(maxsize=5)
esp32cam_processed_frame = None
esp32cam_lock = threading.Lock()
esp32cam_stats = {
    "detections": 0,
    "objects": {},
    "fps": 0,
    "connection_healthy": False,
    "url": esp32cam_url
}

# Voice recognition variables
recognizer = sr.Recognizer()
voice_recognition_active = False
arduino = None
arduino_port = None
arduino_connected = False

# ESP32 Static IP Configuration - Đã cập nhật sang mạng 192.168.162.x
esp32_ip = "192.168.162.10"  # Địa chỉ IP tĩnh mới của ESP32

# ===== Face Recognition Functions =====

def initialize_camera():
    global camera
    if camera is None:
        camera = cv2.VideoCapture(0)
        camera.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    return camera

def release_camera():
    global camera
    if camera is not None:
        camera.release()
        camera = None

def camera_reader():
    global camera, face_recognition_active
    initialize_camera()
    
    while face_recognition_active:
        ret, frame = camera.read()
        if not ret:
            time.sleep(0.1)
            continue
            
        if not frame_queue.empty():
            frame_queue.get_nowait()  # Keep only the latest frame
        
        frame_queue.put(frame)
        time.sleep(0.03)  # ~30 FPS

def process_face_recognition():
    global auth_status, face_recognition_active
    
    while face_recognition_active:
        if frame_queue.empty():
            time.sleep(0.1)
            continue
            
        frame = frame_queue.get()
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        # Detect faces
        faces = face_app.get(rgb_frame)
        
        for face in faces:
            bbox = face.bbox.astype(int)
            face_embedding = face.embedding
            
            best_match = None
            best_score = -1
            
            # Compare with database
            for img_name, data in face_db.items():
                db_embedding = data["embeddings"]
                similarity = np.dot(face_embedding, db_embedding) / (np.linalg.norm(face_embedding) * np.linalg.norm(db_embedding))
                
                if similarity > best_score:
                    best_score = similarity
                    best_match = img_name
            
            # If face matched (threshold 0.5)
            if best_score > 0.5:
                auth_status["authenticated"] = True
                auth_status["user"] = best_match
                auth_status["last_update"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                print(f"✅ Authentication successful: {best_match} with score {best_score:.2f}")
                face_recognition_active = False
                break
        
        time.sleep(0.1)

def start_face_recognition():
    global face_recognition_active
    if face_recognition_active:
        return {"status": "already_running"}
    
    face_recognition_active = True
    
    # Start camera reader thread
    camera_thread = threading.Thread(target=camera_reader)
    camera_thread.daemon = True
    camera_thread.start()
    
    # Start face recognition thread
    face_thread = threading.Thread(target=process_face_recognition)
    face_thread.daemon = True
    face_thread.start()
    
    return {"status": "started"}

def stop_face_recognition():
    global face_recognition_active
    face_recognition_active = False
    time.sleep(0.5)  # Allow threads to clean up
    release_camera()
    return {"status": "stopped"}

# ===== ESP32-CAM Object Detection Functions =====

def esp32cam_reader_thread():
    """Thread to continuously read frames from ESP32-CAM"""
    global esp32cam_active, esp32cam_stats, esp32cam_url
    print(f"🎥 Starting ESP32-CAM reader thread with URL: {esp32cam_url}")
    retry_count = 0
    
    # Danh sách các đường dẫn stream có thể sử dụng
    stream_paths = ["/stream", "/video", "/capture", "/mjpeg/1"]
    current_path_index = 0
    base_url = f"http://{esp32cam_ip}:{esp32cam_port}"
    
    while esp32cam_active:
        try:
            # Lấy đường dẫn stream hiện tại
            current_path = stream_paths[current_path_index]
            current_url = f"{base_url}{current_path}"
            
            print(f"🔍 Thử kết nối đến ESP32-CAM với URL: {current_url}")
            
            # Thiết lập các tùy chọn cho VideoCapture
            # CAP_PROP_OPEN_TIMEOUT_MSEC: thời gian timeout khi mở stream (5 giây)
            # CAP_PROP_READ_TIMEOUT_MSEC: thời gian timeout khi đọc frame (5 giây)
            cap = cv2.VideoCapture(current_url, cv2.CAP_FFMPEG)
            cap.set(cv2.CAP_PROP_OPEN_TIMEOUT_MSEC, 5000)  # 5 giây timeout
            cap.set(cv2.CAP_PROP_READ_TIMEOUT_MSEC, 5000)  # 5 giây timeout
            
            # Thử đọc một frame để kiểm tra kết nối
            ret, frame = cap.read()
            
            if not ret or not cap.isOpened():
                # Thử đường dẫn kế tiếp
                current_path_index = (current_path_index + 1) % len(stream_paths)
                
                retry_count += 1
                if retry_count > len(stream_paths) * 2:  # Thử mỗi đường dẫn nhiều lần
                    print(f"⚠️ Không thể kết nối đến ESP32-CAM sau {retry_count} lần thử. Chờ lâu hơn...")
                    time.sleep(5)  # Chờ lâu hơn giữa các lần thử
                    retry_count = 0
                else:
                    print(f"⚠️ Không thể mở stream ESP32-CAM tại {current_url}. Thử lại {retry_count}/{len(stream_paths) * 2}...")
                    time.sleep(2)  # Chờ giữa các lần thử
                
                # Đảm bảo giải phóng tài nguyên
                cap.release()
                
                with esp32cam_lock:
                    esp32cam_stats["connection_healthy"] = False
                    esp32cam_stats["url"] = current_url
                continue
                
            # Kết nối thành công, cập nhật URL
            esp32cam_url = current_url
            print(f"✅ Kết nối thành công đến ESP32-CAM tại {esp32cam_url}")
            
            with esp32cam_lock:
                esp32cam_stats["connection_healthy"] = True
                esp32cam_stats["url"] = esp32cam_url
            
            retry_count = 0
            frame_count = 0
            start_time = time.time()
            
            while esp32cam_active and cap.isOpened():
                ret, frame = cap.read()
                if not ret:
                    print(f"⚠️ Mất kết nối đến ESP32-CAM tại {esp32cam_url}")
                    break
                
                # Try to add to queue, skip if full
                try:
                    if not esp32cam_queue.full():
                        esp32cam_queue.put(frame.copy(), block=False)
                        frame_count += 1
                except queue.Full:
                    pass
                
                # Calculate FPS
                elapsed = time.time() - start_time
                if elapsed >= 1.0:
                    with esp32cam_lock:
                        esp32cam_stats["fps"] = frame_count / elapsed
                    frame_count = 0
                    start_time = time.time()
            
            print(f"⚠️ Stream kết nối bị mất từ {esp32cam_url}")
            cap.release()
            with esp32cam_lock:
                esp32cam_stats["connection_healthy"] = False
                
        except Exception as e:
            print(f"❌ Lỗi trong ESP32-CAM reader: {e}")
            with esp32cam_lock:
                esp32cam_stats["connection_healthy"] = False
            time.sleep(2)
            
            print("✅ ESP32-CAM stream connection established")
            with esp32cam_lock:
                esp32cam_stats["connection_healthy"] = True
            
            retry_count = 0
            frame_count = 0
            start_time = time.time()
            
            while esp32cam_active and cap.isOpened():
                ret, frame = cap.read()
                if not ret:
                    print("⚠️ Failed to receive frame from ESP32-CAM")
                    break
                
                # Try to add to queue, skip if full
                try:
                    if not esp32cam_queue.full():
                        esp32cam_queue.put(frame.copy(), block=False)
                        frame_count += 1
                except queue.Full:
                    pass
                
                # Calculate FPS
                elapsed = time.time() - start_time
                if elapsed >= 1.0:
                    with esp32cam_lock:
                        esp32cam_stats["fps"] = frame_count / elapsed
                    frame_count = 0
                    start_time = time.time()
            
            print("⚠️ ESP32-CAM stream connection lost")
            cap.release()
            with esp32cam_lock:
                esp32cam_stats["connection_healthy"] = False
                
        except Exception as e:
            print(f"❌ Error in ESP32-CAM reader: {e}")
            with esp32cam_lock:
                esp32cam_stats["connection_healthy"] = False
            time.sleep(3)

def object_detection_thread():
    """Thread to run YOLOv8 object detection on ESP32-CAM frames"""
    global esp32cam_active, esp32cam_processed_frame, esp32cam_stats, yolo_model
    
    print("🔍 Starting YOLOv8 object detection thread")
    if yolo_model is None:
        print("❌ YOLOv8 model not loaded, cannot start detection thread")
        return
    
    while esp32cam_active:
        try:
            if esp32cam_queue.empty():
                time.sleep(0.01)
                continue
            
            # Get a frame from the queue
            frame = esp32cam_queue.get()
            
            # Run object detection
            results = yolo_model(frame, conf=0.5, verbose=False)
            annotated_frame = results[0].plot()
            
            # Update statistics
            detections = results[0].boxes.data.cpu().numpy()
            with esp32cam_lock:
                esp32cam_processed_frame = annotated_frame
                esp32cam_stats["detections"] += len(detections)
                
                # Count object classes
                for det in detections:
                    cls_id = int(det[5])
                    cls_name = yolo_model.names[cls_id]
                    if cls_name in esp32cam_stats["objects"]:
                        esp32cam_stats["objects"][cls_name] += 1
                    else:
                        esp32cam_stats["objects"][cls_name] = 1
            
            time.sleep(0.1)  # Detection interval
            
        except Exception as e:
            print(f"❌ Error in YOLOv8 object detection: {e}")
            time.sleep(0.5)

def create_no_signal_image():
    """Create a 'No Signal' image"""
    img = np.zeros((480, 640, 3), dtype=np.uint8)
    img[:] = (70, 70, 70)  # Dark gray background
    
    font = cv2.FONT_HERSHEY_SIMPLEX
    cv2.putText(img, 'NO SIGNAL', (180, 240), font, 1.5, (255, 255, 255), 2)
    cv2.putText(img, 'Đang kết nối đến ESP32-CAM...', (150, 280), font, 0.7, (200, 200, 200), 1)
    
    return img

def add_status_overlay(frame):
    """Add status overlay to the frame"""
    h, w = frame.shape[:2]
    overlay = frame.copy()
    
    # Draw semi-transparent background
    # cv2.rectangle(overlay, (10, 10), (300, 120), (0, 0, 0), -1)
    # cv2.addWeighted(overlay, 0.6, frame, 0.4, 0, frame)
    
    # # Add status text
    # font = cv2.FONT_HERSHEY_SIMPLEX
    # with esp32cam_lock:
    #     cv2.putText(frame, f"FPS: {esp32cam_stats['fps']:.1f}", (20, 40), font, 0.7, (50, 230, 50), 2)
    #     cv2.putText(frame, f"Kết nối: {'GOOD' if esp32cam_stats['connection_healthy'] else 'LOST'}", 
    #                (20, 70), font, 0.7, (50, 230, 50) if esp32cam_stats['connection_healthy'] else (50, 50, 230), 2)
        
    #     # Get top 3 detected objects
    #     top_objects = ""
    #     if esp32cam_stats["objects"]:
    #         sorted_objs = sorted(esp32cam_stats["objects"].items(), key=lambda x: x[1], reverse=True)[:3]
    #         top_objects = ", ".join([f"{obj}: {count}" for obj, count in sorted_objs])
    
    # cv2.putText(frame, f"Đối tượng: {top_objects}", (20, 100), font, 0.6, (230, 230, 50), 2)
    
    # # Add timestamp
    # timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    # cv2.putText(frame, timestamp, (w - 220, h - 20), font, 0.6, (255, 255, 255), 1)

def generate_esp32cam_frames():
    """Generate frames for the ESP32-CAM video stream"""
    no_signal_img = create_no_signal_image()
    
    while True:
        try:
            with esp32cam_lock:
                if esp32cam_processed_frame is not None and esp32cam_stats["connection_healthy"]:
                    frame = esp32cam_processed_frame.copy()
                else:
                    frame = no_signal_img.copy()
            
            # Add status information
            add_status_overlay(frame)
            
            # Encode and stream
            _, buffer = cv2.imencode('.jpg', frame)
            frame_bytes = buffer.tobytes()
            
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
                
        except Exception as e:
            print(f"❌ Error generating ESP32-CAM frames: {e}")
            time.sleep(0.5)

def start_esp32cam_detection():
    """Start ESP32-CAM detection threads"""
    global esp32cam_active
    if esp32cam_active:
        return {"status": "already_running"}
    
    esp32cam_active = True
    
    # Start ESP32-CAM reader thread
    esp32cam_reader = threading.Thread(target=esp32cam_reader_thread)
    esp32cam_reader.daemon = True
    esp32cam_reader.start()
    
    # Start object detection thread
    detection_thread = threading.Thread(target=object_detection_thread)
    detection_thread.daemon = True
    detection_thread.start()
    
    return {"status": "started"}

def stop_esp32cam_detection():
    """Stop ESP32-CAM detection threads"""
    global esp32cam_active
    esp32cam_active = False
    time.sleep(0.5)  # Allow threads to clean up
    return {"status": "stopped"}

# ===== Voice Recognition Functions =====

def initialize_arduino():
    global arduino, arduino_port, arduino_connected
    
    if arduino_connected:
        return True
        
    # Find available ports
    ports = list(serial.tools.list_ports.comports())
    
    # Try to connect to Arduino
    if arduino_port:
        try:
            arduino = serial.Serial(arduino_port, 9600, timeout=1)
            time.sleep(2)  # Wait for Arduino to initialize
            arduino_connected = True
            print(f"✅ Connected to Arduino on {arduino_port}")
            return True
        except Exception as e:
            print(f"⚠️ Failed to connect to Arduino on {arduino_port}: {e}")
    
    # Try each available port
    for port in ports:
        try:
            test_port = port.device
            print(f"Trying {test_port}...")
            test_connection = serial.Serial(test_port, 9600, timeout=1)
            time.sleep(2)
            test_connection.close()
            arduino = serial.Serial(test_port, 9600, timeout=1)
            arduino_port = test_port
            arduino_connected = True
            print(f"✅ Connected to Arduino on {test_port}")
            return True
        except Exception as e:
            print(f"⚠️ Failed to connect to port {port.device}: {e}")
    
    print("⚠️ Could not connect to any Arduino")
    return False

def close_arduino():
    global arduino, arduino_connected
    if arduino and arduino.is_open:
        arduino.close()
        arduino_connected = False

def process_voice_command(command):
    global pump_state
    
    command = command.lower()
    
    if "bật bơm" in command or "mở bơm" in command:
        pump_state["state"] = True
        if arduino and arduino.is_open:
            arduino.write(b'ON\n')
        return {"action": "pump_on", "message": "Đã bật máy bơm"}
        
    elif "tắt bơm" in command or "ngừng bơm" in command:
        pump_state["state"] = False
        if arduino and arduino.is_open:
            arduino.write(b'OFF\n')
        return {"action": "pump_off", "message": "Đã tắt máy bơm"}
        
    elif "dừng lại" in command:
        return {"action": "stop_listening", "message": "Đã dừng nghe lệnh"}
        
    return {"action": "unknown", "message": "Không hiểu lệnh"}

def listen_voice_command(duration=5):
    try:
        with sr.Microphone() as source:
            recognizer.adjust_for_ambient_noise(source, duration=1)
            print("🎙️ Listening...")
            audio = recognizer.listen(source, timeout=duration, phrase_time_limit=duration)
            
            try:
                text = recognizer.recognize_google(audio, language="vi-VN")
                print(f"🎙️ Heard: {text}")
                return process_voice_command(text)
            except sr.UnknownValueError:
                return {"action": "error", "message": "Không nhận diện được lời nói"}
            except sr.RequestError as e:
                return {"action": "error", "message": f"Lỗi Google Speech Recognition: {e}"}
                
    except Exception as e:
        return {"action": "error", "message": f"Lỗi: {str(e)}"}

def record_voice(duration=5):
    FORMAT = pyaudio.paInt16
    CHANNELS = 1
    RATE = 16000
    CHUNK = 1024
    
    try:
        audio = pyaudio.PyAudio()
        stream = audio.open(format=FORMAT, channels=CHANNELS, rate=RATE, input=True, frames_per_buffer=CHUNK)
        
        print(f"🎙️ Recording for {duration} seconds...")
        frames = []
        
        for _ in range(0, int(RATE / CHUNK * duration)):
            data = stream.read(CHUNK)
            frames.append(data)
        
        stream.stop_stream()
        stream.close()
        audio.terminate()
        
        # Create in-memory file
        audio_data = io.BytesIO()
        waveFile = wave.open(audio_data, 'wb')
        waveFile.setnchannels(CHANNELS)
        waveFile.setsampwidth(audio.get_sample_size(FORMAT))
        waveFile.setframerate(RATE)
        waveFile.writeframes(b''.join(frames))
        waveFile.close()
        
        # Process the recorded audio
        audio_data.seek(0)
        with sr.AudioFile(audio_data) as source:
            recorded_audio = recognizer.record(source)
            
            try:
                text = recognizer.recognize_google(recorded_audio, language="vi-VN")
                print(f"🎙️ Recognized: {text}")
                return process_voice_command(text)
            except sr.UnknownValueError:
                return {"action": "error", "message": "Không nhận diện được lời nói"}
            except sr.RequestError as e:
                return {"action": "error", "message": f"Lỗi Google Speech Recognition: {e}"}
                
    except Exception as e:
        return {"action": "error", "message": f"Lỗi: {str(e)}"}

# ===== Flask Routes =====

# Route chính cho index.html
@app.route('/')
def index():
    # Đầu tiên, kiểm tra xem file có trong thư mục templates không
    try:
        return render_template('index.html')
    except:
        # Nếu không thấy trong templates, thử tìm ở thư mục gốc
        print("Không tìm thấy index.html trong templates, thử tìm ở thư mục gốc")
        return send_from_directory('.', 'index.html')

# Route cho giao diện camera (hỗ trợ cả '/camera' và '/camera/')
@app.route('/camera')
@app.route('/camera/')
def camera_page():
    try:
        return render_template('camera.html')
    except Exception as e:
        print(f"❌ Lỗi khi render camera.html: {str(e)}")
        return "Không tìm thấy trang camera.html. Vui lòng tạo file này trong thư mục templates."

# Route rõ ràng cho static files
@app.route('/static/js/<path:filename>')
def serve_js(filename):
    return send_from_directory('static/js', filename)

@app.route('/data')
def get_data():
    return jsonify(sensor_data)

@app.route('/auth_status')
def get_auth_status():
    return jsonify(auth_status)

@app.route('/pump', methods=['GET', 'POST'])
def update_pump():
    if request.method == 'POST':
        data = request.json
        if 'state' in data:
            pump_state["state"] = data["state"]
            
            # Không cần gửi trực tiếp lệnh đến Arduino
            # ESP32 sẽ tự gửi lệnh qua UART
                
            return jsonify({"status": "success", "state": data["state"]})
        return jsonify({"status": "error", "message": "Invalid data"})
    else:
        # Thêm phương thức GET để ESP32 có thể lấy trạng thái
        return jsonify({"state": pump_state["state"]})

# Route cho ESP32-CAM video feed
@app.route('/video_feed')
def video_feed():
    """Video streaming route"""
    return Response(
        generate_esp32cam_frames(),
        mimetype='multipart/x-mixed-replace; boundary=frame'
    )

# Route để lấy thông tin thống kê từ ESP32-CAM
@app.route('/esp32cam/stats')
def get_esp32cam_stats():
    """API endpoint for ESP32-CAM detection statistics"""
    with esp32cam_lock:
        stats_copy = esp32cam_stats.copy()
    return jsonify(stats_copy)

# Route để điều khiển ESP32-CAM
@app.route('/esp32cam/control', methods=['POST'])
def esp32cam_control():
    """Control ESP32-CAM detection"""
    global esp32cam_url, esp32cam_ip, esp32cam_port
    data = request.json
    action = data.get('action')
    
    if action == 'start':
        return jsonify(start_esp32cam_detection())
    elif action == 'stop':
        return jsonify(stop_esp32cam_detection())
    elif action == 'update_url':
        # Cập nhật URL của ESP32-CAM
        new_ip = data.get('ip')
        new_port = data.get('port', '81')
        
        if new_ip:
            # Dừng detection hiện tại
            if esp32cam_active:
                stop_esp32cam_detection()
                
            # Cập nhật URL
            esp32cam_ip = new_ip
            esp32cam_port = new_port
            esp32cam_url = f"http://{esp32cam_ip}:{esp32cam_port}/stream"
            
            with esp32cam_lock:
                esp32cam_stats["url"] = esp32cam_url
                
            print(f"✅ Đã cập nhật URL ESP32-CAM thành: {esp32cam_url}")
            
            # Khởi động lại detection
            start_esp32cam_detection()
            
            return jsonify({
                "status": "success", 
                "message": f"Đã cập nhật URL thành {esp32cam_url}",
                "url": esp32cam_url
            })
        else:
            return jsonify({"status": "error", "message": "Thiếu địa chỉ IP"})
    else:
        return jsonify({"status": "error", "message": "Invalid action"})

@app.route('/face_auth', methods=['POST'])
def face_authentication():
    data = request.json
    action = data.get('action')
    
    if action == 'start':
        return jsonify(start_face_recognition())
    elif action == 'stop':
        return jsonify(stop_face_recognition())
    else:
        return jsonify({"status": "error", "message": "Invalid action"})

@app.route('/voice', methods=['POST'])
def voice_control():
    data = request.json
    action = data.get('action')
    
    if action == 'listen':
        # Initialize Arduino connection if needed
        if not arduino_connected:
            initialize_arduino()
            
        duration = data.get('duration', 5)
        return jsonify(listen_voice_command(duration))
    
    elif action == 'record':
        # Initialize Arduino connection if needed
        if not arduino_connected:
            initialize_arduino()
            
        duration = data.get('duration', 5)
        return jsonify(record_voice(duration))
    
    else:
        return jsonify({"status": "error", "message": "Invalid action"})

@app.route('/arduino', methods=['POST'])
def arduino_control():
    data = request.json
    action = data.get('action')
    
    if action == 'connect':
        port = data.get('port')
        global arduino_port
        arduino_port = port
        success = initialize_arduino()
        return jsonify({"status": "success" if success else "error", "connected": success})
    
    elif action == 'disconnect':
        close_arduino()
        return jsonify({"status": "success", "connected": False})
    
    elif action == 'list_ports':
        ports = [port.device for port in serial.tools.list_ports.comports()]
        return jsonify({"status": "success", "ports": ports})
    
    else:
        return jsonify({"status": "error", "message": "Invalid action"})

# Điều chỉnh route '/update' để nhận dữ liệu từ ESP32 mới (192.168.162.10)
@app.route('/update', methods=['POST'])
def update_sensor_data():
    global sensor_data
    try:
        data = request.json
        
        # Kiểm tra IP nguồn (tùy chọn, nếu muốn xác thực nguồn)
        # request_ip = request.remote_addr
        # if request_ip != esp32_ip:
        #     print(f"⚠️ Nhận dữ liệu từ IP không xác định: {request_ip}")
        
        # Cập nhật dữ liệu cảm biến
        if "temperature" in data:
            sensor_data["temperature"] = f"{data['temperature']:.1f}"
        
        if "humidity" in data and isinstance(data["humidity"], (int, float)):
            sensor_data["humidity"] = f"{data['humidity']:.1f}%"
        
        if "soil_moisture" in data:
            # Nhận giá trị độ ẩm đất từ ESP32 (đã được Arduino đo)
            moisture_value = data["soil_moisture"]
            if moisture_value > 0:  # Đảm bảo giá trị hợp lệ
                # Giả sử giá trị đầu vào là 0-1023 từ analog sensor
                moisture_percent = 100 - ((moisture_value / 1023) * 100)
                sensor_data["soil_moisture"] = f"{moisture_percent:.0f}%"
        
        if "light" in data:
            sensor_data["light"] = str(data["light"])
            
        if "water_level" in data:
            # Chuyển đổi từ giá trị thô sang phần trăm nếu cần
            water_level = data["water_level"]
            # Giả sử giá trị đầu vào là 0-1023 từ analog sensor
            water_percent = (water_level / 1023) * 100
            sensor_data["water_level"] = f"{water_percent:.0f}%"
            
        print(f"✅ Đã cập nhật dữ liệu cảm biến từ ESP32 ({esp32_ip}): {sensor_data}")
        return jsonify({"status": "success"})
    except Exception as e:
        print(f"❌ Lỗi khi cập nhật dữ liệu cảm biến: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 400

# Start the server
if __name__ == '__main__':
    # In ra thông tin hữu ích về thư mục để debug
    print("\n" + "="*50)
    print("🚀 KHỞI ĐỘNG SMART GARDEN SERVER")
    print("="*50)
    print("🔍 Thư mục hiện tại:", os.getcwd())
    print("🔍 Thư mục templates:", os.path.join(os.getcwd(), 'templates'))
    print("🔍 Thư mục static:", os.path.join(os.getcwd(), 'static'))
    print(f"🔍 ESP32 Static IP: {esp32_ip}")
    print(f"🔍 ESP32-CAM URL ban đầu: {esp32cam_url}")
    print("="*50)
    
    # Kiểm tra xem index.html tồn tại ở đâu
    if os.path.exists('templates/index.html'):
        print("✅ index.html được tìm thấy trong thư mục templates")
    elif os.path.exists('index.html'):
        print("⚠️ index.html được tìm thấy trong thư mục gốc, không trong templates")
    else:
        print("❌ index.html không được tìm thấy!")
    
    # Kiểm tra trang camera.html
    if os.path.exists('templates/camera.html'):
        print("✅ camera.html được tìm thấy trong thư mục templates")
    else:
        print("❌ camera.html không được tìm thấy, cần tạo file này!")
    
    # Kiểm tra file JavaScript
    if os.path.exists('static/js/integration.js'):
        print("✅ integration.js được tìm thấy")
    else:
        print("❌ integration.js không được tìm thấy trong static/js/")
    
    if os.path.exists('static/js/camera.js'):
        print("✅ camera.js được tìm thấy")
    else:
        print("❌ camera.js không được tìm thấy trong static/js/")
    print("="*50)
    
    # Tự động bắt đầu phát hiện đối tượng trên ESP32-CAM
    if yolo_model is not None:
        print("🚀 Khởi động tự động chức năng phát hiện đối tượng trên ESP32-CAM...")
        # Khởi chạy trong một thread riêng để không chặn quá trình khởi động server
        esp32cam_autostart = threading.Thread(target=start_esp32cam_detection)
        esp32cam_autostart.daemon = True
        esp32cam_autostart.start()
    else:
        print("⚠️ Không thể khởi động tự động chức năng phát hiện đối tượng do không tìm thấy model YOLO")
    
    # Initialize InsightFace
    print("🚀 Khởi động Smart Garden Server HTTP...")
    app.run(host='0.0.0.0', port=6005, debug=True)