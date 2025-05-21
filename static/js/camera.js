// static/js/camera.js - Phiên bản tương thích với máy chủ mới

// Biến toàn cục để quản lý trạng thái
let failureCount = 0;
const MAX_FAILURES = 3;
let statsInterval;
let isInitializing = true;
let reconnectTimeout = null;
let startTime = Date.now(); // Thời điểm bắt đầu để tính uptime

// Hàm cập nhật giao diện người dùng
function updateUI(data) {
    // Cập nhật hiệu suất
    document.getElementById('fps-value').innerText = data.fps.toFixed(1);
    
    // Cập nhật trạng thái kết nối
    const connStatus = document.getElementById('connection-status');
    const camStatus = document.getElementById('camera-status');
    
    if (isInitializing && data.fps < 0.5) {
        // Trong quá trình khởi tạo và chưa có FPS
        connStatus.innerHTML = '<span class="status-indicator status-warning"></span>Đang kết nối';
        camStatus.innerHTML = '<i class="fas fa-circle-notch fa-spin"></i> Đang kết nối';
        camStatus.style.backgroundColor = '#f39c12';
        
        // Sau 10 giây, không còn giai đoạn khởi tạo nữa
        if (isInitializing) {
            setTimeout(() => { isInitializing = false; }, 10000);
        }
    } else if (data.connection_healthy) {
        isInitializing = false; // Đã kết nối thành công
        connStatus.innerHTML = '<span class="status-indicator status-good"></span>Đã kết nối';
        camStatus.innerHTML = '<i class="fas fa-circle"></i> Trực tiếp';
        camStatus.style.backgroundColor = '#2ecc71';
    } else {
        connStatus.innerHTML = '<span class="status-indicator status-error"></span>Mất kết nối';
        camStatus.innerHTML = '<i class="fas fa-exclamation-circle"></i> Ngoại tuyến';
        camStatus.style.backgroundColor = '#e74c3c';
    }
    
    // Cập nhật URL hiện tại nếu có
    if (data.url) {
        const urlElement = document.getElementById('current-url');
        if (urlElement) {
            urlElement.textContent = `URL: ${data.url}`;
        }
    }
    
    // Tính thời gian hoạt động (máy chủ mới không cung cấp trường này)
    const uptime = Math.floor((Date.now() - startTime) / 1000);
    const hours = Math.floor(uptime / 3600);
    const minutes = Math.floor((uptime % 3600) / 60);
    const seconds = uptime % 60;
    const uptimeElement = document.getElementById('uptime-value');
    if (uptimeElement) {
        uptimeElement.innerText = `${hours}h ${minutes}m ${seconds}s`;
    }
    
    // Cập nhật thống kê phát hiện
    const totalDetectionsElement = document.getElementById('total-detections');
    if (totalDetectionsElement) {
        totalDetectionsElement.innerText = data.detections;
    }
    
    // Cập nhật danh sách phát hiện
    const detectionList = document.getElementById('detection-list');
    if (detectionList) {
        detectionList.innerHTML = '';
        
        const sortedObjects = Object.entries(data.objects || {})
            .sort((a, b) => b[1] - a[1])
            .slice(0, 5);
        
        if (sortedObjects.length === 0) {
            detectionList.innerHTML = `
                <li class="detection-item">
                    <span class="detection-name">Chưa có phát hiện</span>
                    <span class="detection-count">0</span>
                </li>
            `;
        } else {
            sortedObjects.forEach(([name, count]) => {
                detectionList.innerHTML += `
                    <li class="detection-item">
                        <span class="detection-name">${translateObjectName(name)}</span>
                        <span class="detection-count">${count}</span>
                    </li>
                `;
            });
        }
    }
}

// Hàm dịch tên đối tượng sang tiếng Việt
function translateObjectName(name) {
    // Dictionary để dịch tên đối tượng COCO sang tiếng Việt
    const translations = {
        'person': 'Người',
        'bicycle': 'Xe đạp',
        'car': 'Ô tô',
        'motorcycle': 'Xe máy',
        'airplane': 'Máy bay',
        'bus': 'Xe buýt',
        'train': 'Tàu hỏa',
        'truck': 'Xe tải',
        'boat': 'Tàu thuyền',
        'traffic light': 'Đèn giao thông',
        'fire hydrant': 'Vòi cứu hỏa',
        'stop sign': 'Biển báo dừng',
        'parking meter': 'Đồng hồ đỗ xe',
        'bench': 'Ghế dài',
        'bird': 'Chim',
        'cat': 'Mèo',
        'dog': 'Chó',
        'horse': 'Ngựa',
        'sheep': 'Cừu',
        'cow': 'Bò',
        'elephant': 'Voi',
        'bear': 'Gấu',
        'zebra': 'Ngựa vằn',
        'giraffe': 'Hươu cao cổ',
        'backpack': 'Ba lô',
        'umbrella': 'Ô',
        'handbag': 'Túi xách',
        'tie': 'Cà vạt',
        'suitcase': 'Vali',
        'frisbee': 'Đĩa ném',
        'skis': 'Ván trượt tuyết',
        'snowboard': 'Ván trượt tuyết',
        'sports ball': 'Bóng thể thao',
        'kite': 'Diều',
        'baseball bat': 'Gậy bóng chày',
        'baseball glove': 'Găng tay bóng chày',
        'skateboard': 'Ván trượt',
        'surfboard': 'Ván lướt sóng',
        'tennis racket': 'Vợt tennis',
        'bottle': 'Chai',
        'wine glass': 'Ly rượu',
        'cup': 'Cốc',
        'fork': 'Nĩa',
        'knife': 'Dao',
        'spoon': 'Thìa',
        'bowl': 'Bát',
        'banana': 'Chuối',
        'apple': 'Táo',
        'sandwich': 'Bánh mì kẹp',
        'orange': 'Cam',
        'broccoli': 'Bông cải xanh',
        'carrot': 'Cà rốt',
        'hot dog': 'Xúc xích',
        'pizza': 'Pizza',
        'donut': 'Bánh rán',
        'cake': 'Bánh ngọt',
        'chair': 'Ghế',
        'couch': 'Ghế sofa',
        'potted plant': 'Cây cảnh',
        'bed': 'Giường',
        'dining table': 'Bàn ăn',
        'toilet': 'Nhà vệ sinh',
        'tv': 'TV',
        'laptop': 'Laptop',
        'mouse': 'Chuột máy tính',
        'remote': 'Điều khiển',
        'keyboard': 'Bàn phím',
        'cell phone': 'Điện thoại',
        'microwave': 'Lò vi sóng',
        'oven': 'Lò nướng',
        'toaster': 'Lò nướng bánh mì',
        'sink': 'Bồn rửa',
        'refrigerator': 'Tủ lạnh',
        'book': 'Sách',
        'clock': 'Đồng hồ',
        'vase': 'Bình hoa',
        'scissors': 'Kéo',
        'teddy bear': 'Gấu bông',
        'hair drier': 'Máy sấy tóc',
        'toothbrush': 'Bàn chải đánh răng'
    };
    
    return translations[name] || name;
}

// Hàm cập nhật thống kê camera với xử lý lỗi tốt hơn
function updateStats() {
    fetch('/esp32cam/stats', { cache: 'no-store' })
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! Status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            // Reset counter khi thành công
            failureCount = 0;
            
            // Cập nhật UI với dữ liệu mới
            updateUI(data);
            
            // Log trạng thái kết nối trong console để debug
            if (data.connection_healthy) {
                console.log(`Camera đang hoạt động với FPS: ${data.fps.toFixed(1)}`);
            } else {
                console.warn('Camera không kết nối được');
            }
        })
        .catch(error => {
            console.error('Lỗi khi lấy dữ liệu camera:', error);
            failureCount++;
            
            // Nếu nhiều lỗi liên tiếp, tạm dừng polling
            if (failureCount >= MAX_FAILURES) {
                console.warn(`Quá nhiều lỗi liên tiếp (${failureCount}), tạm dừng cập nhật tự động`);
                clearInterval(statsInterval);
                
                // Hiển thị trạng thái lỗi
                const connStatus = document.getElementById('connection-status');
                const camStatus = document.getElementById('camera-status');
                
                if (connStatus) {
                    connStatus.innerHTML = '<span class="status-indicator status-error"></span>Lỗi kết nối';
                }
                
                if (camStatus) {
                    camStatus.innerHTML = '<i class="fas fa-exclamation-triangle"></i> Lỗi';
                    camStatus.style.backgroundColor = '#e74c3c';
                }
                
                // Thử lại sau 10 giây
                if (reconnectTimeout) {
                    clearTimeout(reconnectTimeout);
                }
                
                reconnectTimeout = setTimeout(() => {
                    console.log('Đang thử kết nối lại...');
                    failureCount = 0;
                    updateStats(); // Gọi thử một lần
                    statsInterval = setInterval(updateStats, 3000);
                }, 10000);
            }
        });
}

// Hàm khởi động lại camera (tương thích với máy chủ mới)
function restartCamera() {
    // Hiển thị trạng thái đang khởi động lại
    const restartButton = document.getElementById('restart-camera');
    if (restartButton) {
        restartButton.disabled = true;
        restartButton.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Đang khởi động lại...';
    }
    
    // Dừng camera
    fetch('/esp32cam/control', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            action: 'stop'
        })
    })
    .then(response => response.json())
    .then(() => {
        console.log('Đã dừng camera, đang khởi động lại...');
        
        // Đợi 2 giây và khởi động lại camera
        setTimeout(() => {
            fetch('/esp32cam/control', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    action: 'start'
                })
            })
            .then(response => response.json())
            .then(() => {
                console.log('Camera đã được khởi động lại');
                
                // Đặt lại trạng thái khởi tạo
                isInitializing = true;
                
                // Đặt lại nút sau 3 giây
                setTimeout(() => {
                    if (restartButton) {
                        restartButton.disabled = false;
                        restartButton.innerHTML = '<i class="fas fa-sync"></i> Khởi động lại camera';
                    }
                }, 3000);
            })
            .catch(error => {
                console.error('Lỗi khi khởi động lại camera:', error);
                if (restartButton) {
                    restartButton.disabled = false;
                    restartButton.innerHTML = '<i class="fas fa-exclamation-circle"></i> Khởi động lại thất bại';
                }
            });
        }, 2000);
    })
    .catch(error => {
        console.error('Lỗi khi dừng camera:', error);
        if (restartButton) {
            restartButton.disabled = false;
            restartButton.innerHTML = '<i class="fas fa-exclamation-circle"></i> Khởi động lại thất bại';
        }
    });
}

// Hàm cập nhật cấu hình camera - hỗ trợ thay đổi IP
function updateCameraConfig() {
    const ipInput = document.getElementById('cameraIp');
    const portInput = document.getElementById('cameraPort');
    
    if (!ipInput || !portInput) {
        console.error('Không tìm thấy phần tử input IP/Port');
        return;
    }
    
    const ip = ipInput.value;
    const port = portInput.value || '81';
    
    if (!ip) {
        showToast('Vui lòng nhập địa chỉ IP', 'warning');
        return;
    }
    
    // Validate IP format
    const ipPattern = /^(\d{1,3})\.(\d{1,3})\.(\d{1,3})\.(\d{1,3})$/;
    if (!ipPattern.test(ip)) {
        showToast('Định dạng IP không hợp lệ', 'warning');
        return;
    }
    
    // Hiển thị trạng thái cập nhật
    const saveBtn = document.getElementById('saveConfigBtn');
    if (saveBtn) {
        saveBtn.disabled = true;
        saveBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Đang cập nhật...';
    }
    
    fetch('/esp32cam/control', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            action: 'update_url',
            ip: ip,
            port: port
        }),
    })
    .then(response => response.json())
    .then(data => {
        console.log('URL update response:', data);
        if (data.status === 'success') {
            showToast('Đã cập nhật URL và kết nối lại', 'success');
            
            // Cập nhật hiển thị URL
            const currentUrl = document.getElementById('current-url');
            if (currentUrl) {
                currentUrl.textContent = `URL: ${data.url}`;
            }
            
            // Đặt lại trạng thái khởi tạo và bắt đầu lại thời gian
            isInitializing = true;
            startTime = Date.now();
            
            // Làm mới trang sau 2 giây để cập nhật video feed
            setTimeout(() => {
                window.location.reload();
            }, 2000);
            
            // Đóng modal nếu có
            const modal = document.getElementById('cameraConfigModal');
            if (modal && typeof bootstrap !== 'undefined') {
                const modalInstance = bootstrap.Modal.getInstance(modal);
                if (modalInstance) {
                    modalInstance.hide();
                }
            }
        } else {
            showToast('Lỗi: ' + data.message, 'error');
            if (saveBtn) {
                saveBtn.disabled = false;
                saveBtn.innerHTML = 'Lưu & Kết nối lại';
            }
        }
    })
    .catch(error => {
        console.error('Error updating camera URL:', error);
        showToast('Lỗi kết nối: ' + error.message, 'error');
        if (saveBtn) {
            saveBtn.disabled = false;
            saveBtn.innerHTML = 'Lưu & Kết nối lại';
        }
    });
}

// Hàm hiển thị thông báo
function showToast(message, type = 'info') {
    // Check if Bootstrap is available
    if (typeof bootstrap !== 'undefined') {
        // Create toast container if it doesn't exist
        let toastContainer = document.getElementById('toast-container');
        if (!toastContainer) {
            toastContainer = document.createElement('div');
            toastContainer.id = 'toast-container';
            toastContainer.className = 'toast-container position-fixed bottom-0 end-0 p-3';
            document.body.appendChild(toastContainer);
        }
        
        // Create toast element
        const toastId = 'toast-' + Date.now();
        const bgClass = type === 'success' ? 'bg-success' : 
                       type === 'error' ? 'bg-danger' : 
                       type === 'warning' ? 'bg-warning' : 'bg-info';
        
        const toastHtml = `
        <div id="${toastId}" class="toast" role="alert" aria-live="assertive" aria-atomic="true">
            <div class="toast-header ${bgClass} text-white">
                <strong class="me-auto">Thông báo</strong>
                <button type="button" class="btn-close btn-close-white" data-bs-dismiss="toast" aria-label="Close"></button>
            </div>
            <div class="toast-body">
                ${message}
            </div>
        </div>`;
        
        // Add toast to container
        toastContainer.innerHTML += toastHtml;
        
        // Initialize and show toast
        const toastElement = document.getElementById(toastId);
        const toast = new bootstrap.Toast(toastElement, { delay: 3000 });
        toast.show();
        
        // Remove toast after it's hidden
        toastElement.addEventListener('hidden.bs.toast', function() {
            toastElement.remove();
        });
    } else {
        // Fallback to alert if Bootstrap is not available
        alert(message);
    }
}

// Cập nhật URL xem trước khi thay đổi IP/Port
function updatePreviewUrl() {
    const ipInput = document.getElementById('cameraIp');
    const portInput = document.getElementById('cameraPort');
    const previewUrl = document.getElementById('previewUrl');
    
    if (ipInput && portInput && previewUrl) {
        const ip = ipInput.value || 'x.x.x.x';
        const port = portInput.value || '81';
        previewUrl.textContent = `http://${ip}:${port}/stream`;
    }
}

// Thêm các event listener khi trang được tải
document.addEventListener('DOMContentLoaded', function() {
    console.log('Khởi tạo giao diện camera...');
    
    // Tìm và thiết lập sự kiện cho nút khởi động lại
    const restartButton = document.getElementById('restart-camera');
    if (restartButton) {
        restartButton.addEventListener('click', restartCamera);
    }
    
    // Thiết lập sự kiện cho các phần tử cấu hình
    const ipInput = document.getElementById('cameraIp');
    const portInput = document.getElementById('cameraPort');
    const saveConfigBtn = document.getElementById('saveConfigBtn');
    
    if (ipInput && portInput) {
        ipInput.addEventListener('input', updatePreviewUrl);
        portInput.addEventListener('input', updatePreviewUrl);
    }
    
    if (saveConfigBtn) {
        saveConfigBtn.addEventListener('click', updateCameraConfig);
    }
    
    // Cập nhật ban đầu
    updateStats();
    
    // Thiết lập interval cho cập nhật
    statsInterval = setInterval(updateStats, 3000); // Gọi mỗi 3 giây
});

// Xử lý sự kiện khi trang bị đóng
window.addEventListener('beforeunload', function() {
    // Xóa các interval và timeout để tránh memory leak
    clearInterval(statsInterval);
    if (reconnectTimeout) {
        clearTimeout(reconnectTimeout);
    }
});