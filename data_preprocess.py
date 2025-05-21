import os
import cv2
import numpy as np
import pickle
import matplotlib.pyplot as plt
from sklearn.decomposition import PCA
from sklearn.metrics.pairwise import cosine_similarity
from insightface.app import FaceAnalysis

# Đường dẫn chứa ảnh của các thành viên
dataset_path = r"dataset"

# Khởi tạo InsightFace để trích xuất khuôn mặt
face_app = FaceAnalysis(providers=['CUDAExecutionProvider', 'CPUExecutionProvider'],
                        allowed_modules=['detection', 'recognition'])  
face_app.prepare(ctx_id=0, det_size=(640, 640))

# Dictionary lưu embeddings và thông tin sinh viên
face_db = {}
embeddings = []
labels = []

# Duyệt qua từng ảnh trong dataset
for img_name in os.listdir(dataset_path):
    img_path = os.path.join(dataset_path, img_name)

    # Đọc ảnh
    img = cv2.imread(img_path)
    if img is None:
        print(f"Lỗi đọc ảnh {img_name}")
        continue

    # Phát hiện khuôn mặt
    faces = face_app.get(img)
    if len(faces) == 0:
        print(f"Không tìm thấy khuôn mặt trong ảnh {img_name}")
        continue

    # Lấy đặc trưng khuôn mặt (embedding)
    face_embedding = faces[0].embedding
    embeddings.append(face_embedding)
    labels.append(img_name)

    # Sử dụng tên file làm khóa nhận diện
    face_db[img_name] = {
        "embeddings": face_embedding
    }

# Lưu embeddings vào file
with open("face_db.pkl", "wb") as f:
    pickle.dump(face_db, f)

print("Dataset đã được xử lý và lưu vào 'face_db.pkl'")

# ---------------------- VẼ SƠ ĐỒ EMBEDDING ----------------------
if len(embeddings) > 1:
    embeddings = np.array(embeddings)

    # Giảm chiều dữ liệu xuống 2D để hiển thị
    pca = PCA(n_components=2)
    reduced_embeddings = pca.fit_transform(embeddings)

    # Vẽ biểu đồ scatter
    plt.figure(figsize=(8, 6))
    for i, label in enumerate(labels):
        plt.scatter(reduced_embeddings[i, 0], reduced_embeddings[i, 1], label=label)
        plt.text(reduced_embeddings[i, 0], reduced_embeddings[i, 1], label[:5], fontsize=9)

    plt.title("Phân bố Embeddings Khuôn Mặt")
    plt.xlabel("PCA Component 1")
    plt.ylabel("PCA Component 2")
    plt.legend()
    plt.grid()
    plt.show()

# ---------------------- TÍNH TOÁN TỶ LỆ CHÍNH XÁC ----------------------
if len(embeddings) > 1:
    similarity_matrix = cosine_similarity(embeddings)
    mean_similarity = np.mean(similarity_matrix)

    print(f"🔍 Tỷ lệ tương đồng trung bình giữa các khuôn mặt: {mean_similarity:.2f}")
