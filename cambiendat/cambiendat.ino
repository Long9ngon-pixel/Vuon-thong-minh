#define SOIL_SENSOR A0  // Cảm biến độ ẩm đất
#define RELAY_PIN 4     // Chân điều khiển máy bơm

boolean autoMode = true;  // Chế độ tự động theo độ ẩm
int dryThreshold = 1008;   // Ngưỡng độ ẩm để tưới

void setup() {
    Serial.begin(9600);  // UART với ESP32 hoặc máy tính
    pinMode(SOIL_SENSOR, INPUT);
    pinMode(RELAY_PIN, OUTPUT);
    digitalWrite(RELAY_PIN, LOW);  // Đảm bảo máy bơm tắt ban đầu
    
    Serial.println("Hệ thống tưới cây khởi động...");
}

void loop() {
    // Kiểm tra nếu có lệnh từ Python
    if (Serial.available() > 0) {
        String command = Serial.readStringUntil('\n');
        command.trim();  // Loại bỏ khoảng trắng và ký tự xuống dòng
        
        if (command == "ON") {
            digitalWrite(RELAY_PIN, HIGH);  // Bật máy bơm
            Serial.println("Đã BẬT máy bơm theo lệnh");
            autoMode = false;  // Tắt chế độ tự động
        } 
        else if (command == "OFF") {
            digitalWrite(RELAY_PIN, LOW);   // Tắt máy bơm
            Serial.println("Đã TẮT máy bơm theo lệnh");
            autoMode = false;  // Tắt chế độ tự động
        }
        else if (command == "AUTO") {
            autoMode = true;  // Bật lại chế độ tự động
            Serial.println("Đã chuyển sang chế độ TỰ ĐỘNG");
        }
    }
    
    // Đọc giá trị độ ẩm đất
    int soilMoisture = analogRead(SOIL_SENSOR);
    
    // Gửi giá trị độ ẩm lên Serial để debug
    Serial.print("Độ ẩm đất: ");
    Serial.println(soilMoisture);
    
    // Chỉ điều khiển máy bơm tự động nếu đang ở chế độ tự động
    if (autoMode) {
        if (soilMoisture > dryThreshold) {  // Đất khô
            digitalWrite(RELAY_PIN, HIGH);  // Bật máy bơm
            Serial.println("Máy bơm: BẬT (tự động)");
        } else {
            digitalWrite(RELAY_PIN, LOW);   // Tắt máy bơm
            Serial.println("Máy bơm: TẮT (tự động)");
        }
    }
    
    delay(2000);  // Chờ 2 giây trước khi đọc lại
}