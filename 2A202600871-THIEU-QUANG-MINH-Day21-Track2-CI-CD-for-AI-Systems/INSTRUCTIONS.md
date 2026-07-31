# Hướng dẫn Cấu hình Tài nguyên Cloud, DVC và GitHub Actions

Tài liệu này hướng dẫn chi tiết các bước để thiết lập hạ tầng Cloud (Google Cloud Platform làm ví dụ mặc định), cấu hình các thông số bảo mật trên GitHub, liên kết DVC với Cloud Storage và chạy tự động hóa pipeline MLOps.

---

## 1. Cấu hình Tài nguyên Cloud và Xác thực

### 1.1. Tạo GCS Bucket (Google Cloud Storage)
1. Truy cập vào [Google Cloud Console](https://console.cloud.google.com/).
2. Chọn dự án (Project) của bạn hoặc tạo mới.
3. Điều hướng tới **Cloud Storage > Buckets** và nhấn **Create**.
4. Thiết lập các thông số:
   * **Name**: Đặt tên duy nhất toàn cầu (ví dụ: `my-mlops-bucket-2026`).
   * **Location type**: Chọn `Region` (khuyên dùng `us-central1` để tối ưu chi phí).
   * Giữ nguyên các cài đặt mặc định khác và nhấn **Create**.
5. Nhấp vào tab **Permissions** của bucket vừa tạo để chuẩn bị phân quyền.

### 1.2. Tạo Service Account và xuất Key JSON
Để GitHub Actions và DVC có quyền truy cập đọc/ghi dữ liệu trên GCS, ta cần cấp quyền hạn tối thiểu thông qua Service Account.
1. Điều hướng tới **IAM & Admin > Service Accounts** trong GCP Console.
2. Nhấn **Create Service Account**:
   * **Service account name**: Điền `mlops-lab-sa`.
   * Nhấn **Create and Continue**.
3. Cấp quyền ở mục **Grant this service account access to project**:
   * Chọn Role: **Storage Object Admin** (`roles/storage.objectAdmin`) trên phạm vi bucket hoặc toàn dự án để DVC có thể tạo/đọc/ghi các file.
   * Nhấn **Continue** rồi **Done**.
4. Xuất Key file dạng JSON:
   * Nhấp chọn Service Account vừa tạo, chuyển sang tab **Keys**.
   * Nhấn **Add Key > Create new key**.
   * Chọn định dạng **JSON** và nhấn **Create**.
   * Trình duyệt sẽ tự động tải xuống file key (ví dụ: `sa-key.json`).
   * **Lưu ý quan trọng**: Di chuyển file `sa-key.json` này vào thư mục gốc của project (nó đã được liệt kê trong `.gitignore` để tránh bị lộ lên GitHub).

### 1.3. Tạo Máy ảo Compute Engine (Cloud VM)
VM này đóng vai trò làm máy chủ Serving API chạy FastAPI.
1. Điều hướng tới **Compute Engine > VM Instances** và nhấn **Create Instance**.
2. Thiết lập cấu hình:
   * **Name**: `mlops-serve`.
   * **Region & Zone**: Chọn trùng vùng với bucket (`us-central1-a`).
   * **Machine configuration**: Chọn `e2-small` (đủ cho nhu cầu lab).
   * **Boot disk**: Chọn OS **Ubuntu 22.04 LTS**.
   * Nhấn **Create**.
3. Sau khi máy ảo khởi chạy, ghi lại địa chỉ **External IP** (IP công khai).
4. Mở cổng mạng (Firewall Rule) phục vụ API:
   * Điều hướng tới **VPC network > Firewall**.
   * Nhấn **Create Firewall Rule**:
     * **Name**: `allow-mlops-serve-port`.
     * **Targets**: Chọn `All instances in the network` hoặc đặt target tag `mlops-serve`.
     * **Source IPv4 ranges**: Điền `0.0.0.0/0` (cho phép truy cập từ mọi IP).
     * **Protocols and ports**: Tích chọn **Specified protocols and ports > tcp > 8000**.
     * Nhấn **Create**.

### 1.4. Thiết lập SSH Key trên máy cá nhân và VM
SSH Key dùng để GitHub Actions tự động đăng nhập vào VM và restart API service.
1. Mở PowerShell/Terminal trên máy cá nhân, chạy lệnh sau để tạo cặp SSH Key:
   ```bash
   ssh-keygen -t ed25519 -f ~/.ssh/mlops_deploy -N "" -C "github-actions-deploy"
   ```
2. Thêm Public Key vào danh sách được phép đăng nhập (`authorized_keys`) trên máy ảo:
   * Mở file public key trên máy cục bộ bằng Notepad hoặc lệnh: `cat ~/.ssh/mlops_deploy.pub`
   * Copy toàn bộ dòng nội dung (bắt đầu bằng `ssh-ed25519 ...`).
   * SSH vào máy ảo GCP thông qua nút **SSH** trên giao diện GCP Console.
   * Mở file chỉnh sửa trên máy ảo:
     ```bash
     nano ~/.ssh/authorized_keys
     ```
   * Dán dòng public key vừa copy xuống cuối file, lưu lại (`Ctrl+O`, `Enter`) và thoát (`Ctrl+X`).
3. Cài đặt các thư viện cần thiết trên VM:
   * Chạy các lệnh sau trong phiên SSH trên máy ảo để chuẩn bị môi trường:
     ```bash
     sudo apt update && sudo apt install -y python3-pip python3-venv
     pip3 install fastapi uvicorn scikit-learn joblib google-cloud-storage
     mkdir -p ~/models ~/src
     ```
   * Copy file xác thực `sa-key.json` lên máy ảo (để phục vụ việc tải model từ GCS khi khởi động API):
     * Bạn có thể sử dụng giao diện GCP `Upload File` của SSH Console để đưa file `sa-key.json` lên thư mục `/home/<username>/sa-key.json`.
4. Tạo Systemd Service cho FastAPI Serving trên máy ảo:
   * Trên máy ảo GCP, chạy lệnh tạo file service:
     ```bash
     sudo nano /etc/systemd/system/mlops-serve.service
     ```
   * Dán nội dung cấu hình sau vào (thay thế `<YOUR_BUCKET_NAME>` và `<YOUR_VM_USER>` bằng tên thật):
     ```ini
     [Unit]
     Description=MLOps Model Inference Server
     After=network.target

     [Service]
     User=<YOUR_VM_USER>
     WorkingDirectory=/home/<YOUR_VM_USER>
     Environment="GCS_BUCKET=<YOUR_BUCKET_NAME>"
     Environment="GOOGLE_APPLICATION_CREDENTIALS=/home/<YOUR_VM_USER>/sa-key.json"
     ExecStart=/usr/bin/python3 /home/<YOUR_VM_USER>/src/serve.py
     Restart=always
     RestartSec=5

     [Install]
     WantedBy=multi-user.target
     ```
   * Reload systemd daemon:
     ```bash
     sudo systemctl daemon-reload
     sudo systemctl enable mlops-serve
     ```

---

## 2. Cấu hình GitHub Secrets

Trên repository GitHub của bạn, đi tới **Settings > Secrets and variables > Actions** và nhấn **New repository secret** để thêm đúng 5 secrets sau:

1. `CLOUD_CREDENTIALS`
   * **Giá trị**: Copy và dán toàn bộ nội dung file JSON `sa-key.json`.
2. `CLOUD_BUCKET`
   * **Giá trị**: Tên GCS bucket của bạn (ví dụ: `my-mlops-bucket-2026`).
3. `VM_HOST`
   * **Giá trị**: External IP của máy ảo Compute Engine (ví dụ: `35.200.100.123`).
4. `VM_USER`
   * **Giá trị**: Tên tài khoản trên VM (lấy bằng cách chạy lệnh `echo $USER` trong SSH trên máy ảo).
5. `VM_SSH_KEY`
   * **Giá trị**: Copy toàn bộ nội dung file private key cục bộ `~/.ssh/mlops_deploy` (bao gồm cả dòng `-----BEGIN OPENSSH PRIVATE KEY-----` và `-----END OPENSSH PRIVATE KEY-----`).

---

## 3. Khởi tạo DVC Remote và Đẩy dữ liệu lên Cloud

Thực hiện các lệnh sau trên máy tính cá nhân để thiết lập DVC đồng bộ dữ liệu:

1. Khởi tạo DVC trong thư mục dự án:
   ```bash
   dvc init
   ```
2. Cấu hình GCS làm DVC Remote (thay thế `<YOUR_BUCKET_NAME>`):
   ```bash
   dvc remote add -d myremote gs://<YOUR_BUCKET_NAME>/dvc
   ```
3. Cấu hình xác thực cho DVC Remote sử dụng file key cục bộ:
   ```bash
   dvc remote modify myremote credentialpath sa-key.json
   ```
4. Đăng ký các tệp dữ liệu vào DVC tracking:
   ```bash
   dvc add data/train_phase1.csv
   dvc add data/eval.csv
   dvc add data/train_phase2.csv
   ```
5. Đẩy tệp tin dữ liệu thực sự lên GCS Bucket:
   ```bash
   dvc push
   ```
6. Đưa các file cấu hình DVC và file con trỏ `.dvc` vào Git:
   ```bash
   git add data/train_phase1.csv.dvc data/eval.csv.dvc data/train_phase2.csv.dvc .dvc/config .gitignore
   git commit -m "feat: track datasets with DVC"
   ```

---

## 4. Kích hoạt Pipeline CI/CD Lần đầu (Bước 2)

1. Tải file `serve.py` lên máy ảo GCP lần đầu bằng lệnh `gcloud compute scp` hoặc copy thủ công nội dung file `src/serve.py` sang máy ảo tại đường dẫn `~/src/serve.py`.
2. Commit toàn bộ thay đổi code và đẩy lên GitHub:
   ```bash
   git add .
   git commit -m "feat: complete MLOps pipeline setup"
   git push origin main
   ```
3. Theo dõi tab **Actions** trên GitHub:
   * **Job Test**: Chạy thành công.
   * **Job Train**: Chạy thành công và lưu model lên GCS.
   * **Job Eval**: Chạy thành công, nhận diện Accuracy là `0.6840`. Do `< 0.70`, bước kiểm tra chất lượng sẽ báo thất bại và **Deploy job bị chặn** (đây là hành vi chính xác của Eval gate đối với dữ liệu Phase 1).

---

## 5. Bổ sung Dữ liệu Mới và Chạy lại Pipeline (Bước 3)

Mô phỏng quy trình bổ sung thêm dữ liệu mới để tăng độ chính xác của mô hình lên trên ngưỡng `0.70` và kích hoạt lại pipeline tự động.

1. Ghép dữ liệu Phase 2 vào tập huấn luyện hiện tại:
   ```bash
   python add_new_data.py
   ```
   * *Kết quả xuất ra*: `Cap nhat du lieu: 2998 -> 5996 mau`
2. Cập nhật DVC để tracking file dữ liệu mới:
   ```bash
   dvc add data/train_phase1.csv
   ```
3. Commit file con trỏ `.dvc` đã thay đổi lên Git:
   ```bash
   git add data/train_phase1.csv.dvc
   git commit -m "data: bổ sung 2998 mẫu dữ liệu mới (train_phase2)"
   ```
4. Đẩy tệp tin dữ liệu mới lên GCS Remote (bắt buộc thực hiện trước khi git push):
   ```bash
   dvc push
   ```
5. Đẩy commit lên GitHub để tự động kích hoạt workflow:
   ```bash
   git push origin main
   ```
6. Kiểm tra lại tab **Actions** trên GitHub:
   * Lần chạy này sẽ chạy trên tập dữ liệu đầy đủ 5996 mẫu.
   * Mô hình sẽ được huấn luyện lại và đạt độ chính xác **Accuracy là 0.7580** (đã vượt qua ngưỡng đánh giá `0.70`).
   * **Job Eval vượt qua** và **Job Deploy sẽ chuyển sang màu xanh** (hoàn thành triển khai tự động lên VM!).

7. Xác thực API trên VM bằng cách gửi request suy luận từ máy tính cá nhân:
   ```bash
   # Thay thế <YOUR_VM_IP> bằng IP công khai của máy ảo Compute Engine
   curl http://<YOUR_VM_IP>:8000/health

   curl -X POST http://<YOUR_VM_IP>:8000/predict \
     -H "Content-Type: application/json" \
     -d '{"features": [7.4, 0.70, 0.00, 1.9, 0.076, 11.0, 34.0, 0.9978, 3.51, 0.56, 9.4, 0]}'
   ```
   * *Kết quả mong đợi*: `{"prediction": 0, "label": "thap"}`
