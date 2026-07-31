# Báo Cáo Kết Quả Thực Hành Lab MLOps
**Học viên:** THIÊU QUANG MINH

---

## 1. Kết Quả Thực Nghiệm Cục Bộ và MLflow Tracking (Bước 1)

Chúng tôi đã thực hiện tổng cộng 5 thực nghiệm cục bộ với các cấu hình siêu tham số khác nhau cho mô hình `RandomForestClassifier` trên tập dữ liệu gốc **Phase 1** (2998 mẫu). Toàn bộ các lần chạy đều được ghi nhận đầy đủ các thông số và độ đo vào cơ sở dữ liệu MLflow cục bộ.

### Bảng tổng hợp kết quả thực nghiệm cục bộ:

| Lần chạy | Siêu tham số (n_estimators, max_depth, min_samples_split) | Độ chính xác (Accuracy) | F1-Score (Weighted) | Trạng thái / Nhận xét |
|:---:|---|:---:|:---:|---|
| **Thí nghiệm 1** | `n_estimators: 100, max_depth: 5, min_samples_split: 2` | 0.5640 | 0.5534 | Cấu hình mặc định của hệ thống. Độ chính xác trung bình. |
| **Thí nghiệm 2** | `n_estimators: 50, max_depth: 3, min_samples_split: 5` | 0.5580 | 0.5185 | Mô hình nhỏ, nông. Xảy ra hiện tượng underfitting nhẹ. |
| **Thí nghiệm 3** | `n_estimators: 200, max_depth: 10, min_samples_split: 2` | 0.6480 | 0.6464 | Tăng độ sâu và số lượng cây. Độ chính xác cải thiện đáng kể. |
| **Thí nghiệm 4** | `n_estimators: 300, max_depth: 20, min_samples_split: 2` | 0.6780 | 0.6767 | Mô hình sâu hơn, bắt đầu nắm bắt tốt hơn các đặc trưng hóa học. |
| **Thí nghiệm 5** | `n_estimators: 500, max_depth: null, min_samples_split: 2` | 0.6760 | 0.6748 | Không giới hạn độ sâu. Đạt độ chính xác tương đương nhưng có nguy cơ overfitting. |
| **Thí nghiệm 6** | `n_estimators: 100, max_depth: 20, min_samples_split: 2` | **0.6840** | **0.6829** | **Cấu hình tối ưu nhất** tìm được sau khi Grid Search. |

### Bộ siêu tham số tốt nhất được chọn:
* **`n_estimators`**: `100`
* **`max_depth`**: `20`
* **`min_samples_split`**: `2`
* **Lý do lựa chọn**: Cấu hình này mang lại sự cân bằng tốt nhất giữa độ phức tạp mô hình và hiệu suất dự đoán, đạt Accuracy tối đa trên tập đánh giá held-out là `0.6840`.

---

## 2. Phân Tích Cơ Chế Đánh Giá (Eval Gate) và Hiệu Năng Mô Hình

Mục tiêu của chốt chặn đánh giá (Eval Gate) là đảm bảo các mô hình có chất lượng kém không bao giờ được đưa lên môi trường Production. Cụ thể trong bài lab này, ngưỡng chất lượng được thiết lập là **Accuracy >= 0.70**.

### So sánh hiệu năng giữa Bước 2 và Bước 3:

| Chỉ số | Bước 2 (Dữ liệu Phase 1 - 2998 mẫu) | Bước 3 (Dữ liệu kết hợp Phase 1 & 2 - 5996 mẫu) | Nhận xét |
|---|:---:|:---:|---|
| **Accuracy** | 0.6840 | **0.7580** | Tăng **7.40%** |
| **F1-Score** | 0.6829 | **0.7552** | Tăng **7.23%** |
| **Chốt chặn chất lượng (Eval Gate)** | **FAILED** (Bị chặn) | **PASSED** (Vượt qua) | Hệ thống tự động chặn deploy ở Bước 2 và tự động deploy ở Bước 3. |

### Giải thích quy trình tự động hóa:
* **Ở Bước 2**: Mô hình được huấn luyện trên 2998 mẫu dữ liệu ban đầu. Do lượng thông tin chưa đủ phong phú, độ chính xác tối đa đạt được chỉ là `0.6840` (dưới ngưỡng `0.70`). Nhờ đó, job `deploy` trong GitHub Actions bị chặn lại hoàn toàn tự động, tránh deploy mô hình chưa đạt chuẩn.
* **Ở Bước 3**: Khi kỹ sư dữ liệu chạy script `add_new_data.py` bổ sung 2998 mẫu mới và cập nhật file `.dvc`, pipeline được kích hoạt trở lại. Lúc này mô hình được huấn luyện trên dữ liệu 5996 mẫu phong phú hơn, giúp Accuracy tăng vọt lên `0.7580`. Chốt đánh giá được thông qua và mô hình mới lập tức được triển khai lên Serving API.

---

## 3. Khó Khăn Gặp Phải và Giải Pháp Xử Lý

Trong quá trình thiết lập môi trường cục bộ và xây dựng pipeline CI/CD, nhóm đã gặp một số trở ngại kỹ thuật sau:

1. **Lỗi biên dịch `pyarrow` trên Windows với môi trường Python 3.14.5 (pre-release):**
   * *Nguyên nhân*: Python 3.14 là phiên bản thử nghiệm nên chưa có các bản build sẵn (wheel) cho các phiên bản cũ của `pyarrow` (như bản `<16` yêu cầu bởi `mlflow==2.13.0`). Khi pip tự động tải mã nguồn về để tự biên dịch, quá trình bị thất bại do thiếu module `pkg_resources` trong các phiên bản `setuptools` mới (từ bản 70 trở đi).
   * *Giải pháp*:
     * Bước 1: Hạ cấp `setuptools` cục bộ xuống phiên bản cũ hơn `<70` (cụ thể là `setuptools==69.5.1`) để khôi phục module `pkg_resources`.
     * Bước 2: Cài đặt thủ công phiên bản `pyarrow` mới nhất có hỗ trợ build sẵn (wheel) cho Python 3.14 (phiên bản `pyarrow==24.0.0`) sử dụng cờ `--no-build-isolation`.
     * Bước 3: Cho phép cài đặt các phiên bản mới của `mlflow` (bản `3.14.0`) và `dvc` (bản `3.67.1`) tương thích hoàn toàn với Python 3.14 và `pyarrow 24.0.0`.

2. **Xác thực DVC và GitHub Actions:**
   * *Khó khăn*: Đảm bảo bảo mật cho Service Account GCP khi runner cần pull dữ liệu từ GCS.
   * *Giải pháp*: Đưa toàn bộ mã xác thực JSON của Service Account vào GitHub Secrets với tên `CLOUD_CREDENTIALS`, ghi tạm ra `/tmp/sa-key.json` trong lúc runner chạy và liên kết qua biến môi trường `GOOGLE_APPLICATION_CREDENTIALS`.
