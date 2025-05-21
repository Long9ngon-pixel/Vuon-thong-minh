// File: integration.js
// Đây là file script bổ sung để tích hợp face_recognition và record.py với ứng dụng web

document.addEventListener('DOMContentLoaded', function() {
    // Bổ sung sự kiện cho phần xác thực khuôn mặt
    const authSection = document.getElementById('authSection');
    if (authSection) {
        // Thêm nút "Xác thực bằng khuôn mặt" vào phần xác thực
        const authButton = document.createElement('button');
        authButton.className = 'btn btn-primary';
        authButton.innerHTML = '<i class="fas fa-camera"></i> Xác thực bằng khuôn mặt';
        authButton.style.marginTop = '20px';
        authSection.appendChild(authButton);
        
        // Xử lý sự kiện khi nhấn nút xác thực
        authButton.addEventListener('click', function() {
            // Bắt đầu quá trình xác thực khuôn mặt
            startFaceAuthentication();
        });
    }
    
    // Bổ sung sự kiện cho phần điều khiển giọng nói
    const btnStartListening = document.getElementById('btnStartListening');
    const btnStopListening = document.getElementById('btnStopListening');
    const btnRecordAudio = document.getElementById('btnRecordAudio');
    const recognitionResult = document.getElementById('recognitionResult');
    
    if (btnStartListening) {
        // Ghi đè sự kiện mặc định
        btnStartListening.addEventListener('click', function(event) {
            event.preventDefault();
            event.stopPropagation();
            
            // Cập nhật giao diện
            btnStartListening.disabled = true;
            btnStopListening.disabled = false;
            updateRecordingStatus(true);
            recognitionResult.textContent = "Đang lắng nghe...";
            
            // Gọi API để bắt đầu lắng nghe từ server
            startVoiceListening();
            
            return false;
        }, true);
    }
    
    if (btnStopListening) {
        // Ghi đè sự kiện mặc định
        btnStopListening.addEventListener('click', function(event) {
            event.preventDefault();
            event.stopPropagation();
            
            // Cập nhật giao diện
            btnStartListening.disabled = false;
            btnStopListening.disabled = true;
            updateRecordingStatus(false);
            recognitionResult.textContent = "Đã dừng lắng nghe";
            
            return false;
        }, true);
    }
    
    if (btnRecordAudio) {
        // Ghi đè sự kiện mặc định
        btnRecordAudio.addEventListener('click', function(event) {
            event.preventDefault();
            event.stopPropagation();
            
            // Cập nhật giao diện
            btnRecordAudio.disabled = true;
            updateRecordingStatus(true);
            recognitionResult.textContent = "Đang ghi âm (5 giây)...";
            
            // Gọi API để ghi âm từ server
            recordVoiceCommand();
            
            return false;
        }, true);
    }
    
    // Kết nối với Arduino nếu có
    initializeArduino();
});

// ===== Face Recognition Functions =====

function startFaceAuthentication() {
    // Cập nhật giao diện
    const authIndicator = document.getElementById('authIndicator');
    const authStatusText = document.getElementById('authStatusText');
    const authMessage = document.getElementById('authMessage');
    
    authStatusText.textContent = 'Đang xác thực...';
    authMessage.textContent = 'Vui lòng nhìn vào camera để xác thực';
    
    // Gọi API để bắt đầu quá trình xác thực khuôn mặt
    fetch('/face_auth', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ action: 'start' })
    })
    .then(response => response.json())
    .then(data => {
        console.log('Face authentication started:', data);
        
        // Bắt đầu kiểm tra trạng thái xác thực
        checkAuthStatusFrequently();
    })
    .catch(error => {
        console.error('Error starting face authentication:', error);
        authStatusText.textContent = 'Lỗi xác thực';
        authMessage.textContent = 'Không thể bắt đầu quá trình xác thực khuôn mặt';
    });
}

function stopFaceAuthentication() {
    // Gọi API để dừng quá trình xác thực khuôn mặt
    fetch('/face_auth', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ action: 'stop' })
    })
    .then(response => response.json())
    .then(data => {
        console.log('Face authentication stopped:', data);
    })
    .catch(error => {
        console.error('Error stopping face authentication:', error);
    });
}

function checkAuthStatusFrequently() {
    // Kiểm tra trạng thái xác thực mỗi 1 giây
    const checkInterval = setInterval(() => {
        fetch('/auth_status')
        .then(response => response.json())
        .then(data => {
            if (data.authenticated) {
                // Dừng kiểm tra khi đã xác thực thành công
                clearInterval(checkInterval);
                
                // Dừng quá trình xác thực khuôn mặt
                stopFaceAuthentication();
                
                // Cập nhật giao diện như trong checkAuthStatus()
                const authIndicator = document.getElementById('authIndicator');
                const authStatusText = document.getElementById('authStatusText');
                const authMessage = document.getElementById('authMessage');
                
                authIndicator.classList.remove('auth-off');
                authIndicator.classList.add('auth-on');
                authStatusText.textContent = 'Đã xác thực';
                authMessage.textContent = `Xin chào, ${data.user}! Đã xác thực thành công.`;
                
                // Hiển thị nội dung chính
                setTimeout(() => {
                    document.getElementById('authSection').classList.add('hidden');
                    document.getElementById('mainContent').classList.remove('hidden');
                    
                    // Bắt đầu tải dữ liệu cảm biến
                    fetchData();
                    setInterval(fetchData, 5000);  // Cập nhật mỗi 5 giây
                }, 2000);
            }
        })
        .catch(error => {
            console.error('Error checking auth status:', error);
        });
    }, 1000);
    
    // Dừng kiểm tra sau 30 giây nếu không thành công
    setTimeout(() => {
        clearInterval(checkInterval);
        
        // Kiểm tra xem đã xác thực thành công chưa
        fetch('/auth_status')
        .then(response => response.json())
        .then(data => {
            if (!data.authenticated) {
                // Nếu chưa xác thực thành công, cập nhật giao diện
                const authStatusText = document.getElementById('authStatusText');
                const authMessage = document.getElementById('authMessage');
                
                authStatusText.textContent = 'Chưa xác thực';
                authMessage.textContent = 'Xác thực thất bại. Vui lòng thử lại.';
                
                // Dừng quá trình xác thực khuôn mặt
                stopFaceAuthentication();
            }
        });
    }, 30000);
}

// ===== Voice Control Functions =====

function startVoiceListening() {
    // Gọi API để bắt đầu lắng nghe lệnh giọng nói
    fetch('/voice', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ action: 'listen', duration: 10 })
    })
    .then(response => response.json())
    .then(data => {
        console.log('Voice command result:', data);
        
        // Cập nhật giao diện
        const btnStartListening = document.getElementById('btnStartListening');
        const btnStopListening = document.getElementById('btnStopListening');
        const recognitionResult = document.getElementById('recognitionResult');
        
        btnStartListening.disabled = false;
        btnStopListening.disabled = true;
        updateRecordingStatus(false);
        
        // Hiển thị kết quả
        if (data.action && data.message) {
            recognitionResult.textContent = data.message;
            
            // Xử lý hành động
            if (data.action === 'pump_on') {
                // Bật máy bơm
                document.getElementById('pumpToggle').checked = true;
                updatePumpStatus(true);
                logAction("Bật máy bơm bằng giọng nói");
            } 
            else if (data.action === 'pump_off') {
                // Tắt máy bơm
                document.getElementById('pumpToggle').checked = false;
                updatePumpStatus(false);
                logAction("Tắt máy bơm bằng giọng nói");
            }
        } else {
            recognitionResult.textContent = "Không nhận diện được lệnh";
        }
    })
    .catch(error => {
        console.error('Error with voice command:', error);
        
        // Cập nhật giao diện
        const btnStartListening = document.getElementById('btnStartListening');
        const btnStopListening = document.getElementById('btnStopListening');
        const recognitionResult = document.getElementById('recognitionResult');
        
        btnStartListening.disabled = false;
        btnStopListening.disabled = true;
        updateRecordingStatus(false);
        recognitionResult.textContent = "Lỗi khi xử lý lệnh giọng nói";
    });
}

function recordVoiceCommand() {
    // Gọi API để ghi âm và xử lý lệnh giọng nói
    fetch('/voice', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ action: 'record', duration: 5 })
    })
    .then(response => response.json())
    .then(data => {
        console.log('Voice recording result:', data);
        
        // Cập nhật giao diện
        const btnRecordAudio = document.getElementById('btnRecordAudio');
        const recognitionResult = document.getElementById('recognitionResult');
        
        btnRecordAudio.disabled = false;
        updateRecordingStatus(false);
        
        // Hiển thị kết quả
        if (data.action && data.message) {
            recognitionResult.textContent = data.message;
            
            // Xử lý hành động
            if (data.action === 'pump_on') {
                // Bật máy bơm
                document.getElementById('pumpToggle').checked = true;
                updatePumpStatus(true);
                logAction("Bật máy bơm bằng ghi âm");
            } 
            else if (data.action === 'pump_off') {
                // Tắt máy bơm
                document.getElementById('pumpToggle').checked = false;
                updatePumpStatus(false);
                logAction("Tắt máy bơm bằng ghi âm");
            }
        } else {
            recognitionResult.textContent = "Không nhận diện được lệnh";
        }
    })
    .catch(error => {
        console.error('Error with voice recording:', error);
        
        // Cập nhật giao diện
        const btnRecordAudio = document.getElementById('btnRecordAudio');
        const recognitionResult = document.getElementById('recognitionResult');
        
        btnRecordAudio.disabled = false;
        updateRecordingStatus(false);
        recognitionResult.textContent = "Lỗi khi ghi âm";
    });
}

// ===== Arduino Connection =====

function initializeArduino() {
    // Lấy danh sách cổng COM
    fetch('/arduino', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ action: 'list_ports' })
    })
    .then(response => response.json())
    .then(data => {
        console.log('Available COM ports:', data.ports);
        
        if (data.ports && data.ports.length > 0) {
            // Kết nối với cổng đầu tiên
            connectToArduino(data.ports[0]);
        }
    })
    .catch(error => {
        console.error('Error listing COM ports:', error);
    });
}

function connectToArduino(port) {
    // Kết nối với Arduino qua cổng COM cụ thể
    fetch('/arduino', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ action: 'connect', port: port })
    })
    .then(response => response.json())
    .then(data => {
        console.log('Arduino connection result:', data);
    })
    .catch(error => {
        console.error('Error connecting to Arduino:', error);
    });
}