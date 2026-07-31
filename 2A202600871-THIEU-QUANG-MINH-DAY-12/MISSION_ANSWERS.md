# Day 12 Lab - Mission Answers

> **Student Name:** THIEU QUANG MINH  
> **Student ID:** 2A202600871  
> **Date:** 2026-06-30  

---

## Part 1: Localhost vs Production

### Exercise 1.1: Anti-patterns found in develop/app.py
1. **Hardcoded API key & DB credentials:** API Key (`OPENAI_API_KEY`) và database URL (`DATABASE_URL`) bị ghi đè cứng trong mã nguồn (mã nguồn mở sẽ làm lộ khóa bảo mật).
2. **Thiếu hệ thống Quản lý Cấu hình (Configuration Management):** Các thiết lập như `DEBUG = True` và `MAX_TOKENS = 500` bị định nghĩa trực tiếp dưới dạng biến cục bộ thay vì đọc từ file `.env` hoặc biến môi trường (environment variables).
3. **Log thông tin không chuẩn hóa (Print statements):** Sử dụng hàm `print()` thông thường thay vì thư viện logging chuyên nghiệp (Structured JSON Logging). Đồng thời, in cả API key bảo mật ra màn hình console (`print(f"[DEBUG] Using key: {OPENAI_API_KEY}")`).
4. **Không có Endpoint kiểm tra trạng thái sức khỏe (Health Check endpoints):** Thiếu `/health` (liveness probe) và `/ready` (readiness probe) khiến container orchestrator (như Docker, Kubernetes, Cloud Run) không thể giám sát trạng thái để tự động khởi động lại ứng dụng nếu xảy ra lỗi.
5. **Gán cứng địa chỉ Host và Port (Hardcoded host and port binding):** Host bị gán là `localhost` thay vì `0.0.0.0` (khiến các dịch vụ khác bên ngoài container không thể truy cập). Port bị cố định là `8000` (ở môi trường Cloud như Railway/Render, port sẽ được chỉ định ngẫu nhiên thông qua biến môi trường `PORT`).
6. **Bật chế độ tự động reload (`reload=True`) trong môi trường production:** Tính năng này tiêu tốn nhiều tài nguyên hệ thống và làm giảm hiệu năng, chỉ nên dùng trong lúc develop.

---

### Exercise 1.3: Comparison table

| Feature | Basic | Advanced | Tại sao quan trọng? (Tại sao quan trọng?) |
|---------|-------|----------|-----------------------------------|
| **Config** | Hardcode | Env vars (12-Factor App) | Giúp bảo mật thông tin nhạy cảm, dễ dàng thay đổi cấu hình giữa các môi trường (Dev, Staging, Prod) mà không cần chỉnh sửa source code. |
| **Health check** | Không có (❌) | Có `/health` & `/ready` (✅) | Giúp cloud platforms / load balancers tự động restart container bị crash (Liveness) và điều phối traffic tới các instances hoạt động tốt (Readiness). |
| **Logging** | Dùng `print()` | Structured JSON Logging | Format JSON giúp các hệ thống thu thập log tập trung (như Loki, Datadog, ELK) dễ dàng phân tích, lọc và tìm kiếm lỗi một cách tự động. |
| **Shutdown** | Đột ngột | Graceful Shutdown (SIGTERM) | Đảm bảo hệ thống không tắt đột ngột khi đang xử lý request của khách hàng. Ứng dụng sẽ hoàn thành các tiến trình đang dở và đóng kết nối an toàn trước khi dừng. |
| **Host Binding** | `localhost` | `0.0.0.0` | Để các dịch vụ bên ngoài và Nginx Load Balancer có thể gửi request đến ứng dụng chạy bên trong container. |

---

## Part 2: Docker

### Exercise 2.1: Dockerfile questions
1. **Base image:** `python:3.11` (Bao gồm đầy đủ hệ điều hành Debian và môi trường chạy Python, dung lượng tải xuống ban đầu rất nặng, khoảng ~1.0 GB).
2. **Working directory:** `/app` (Đường dẫn thư mục làm việc mặc định trong container, nơi tất cả các lệnh tiếp theo được thực thi và chứa code dự án).
3. **Tại sao copy requirements.txt trước?** Nhằm tận dụng cơ chế lưu trữ bộ nhớ đệm (Layer Cache) của Docker. Dependencies (requirements) ít khi thay đổi hơn code chính. Khi sửa code, Docker chỉ build lại các layer từ bước copy code trở đi, giúp tiết kiệm thời gian build đáng kể.
4. **CMD vs ENTRYPOINT:**
   - `CMD` chỉ định lệnh mặc định và tham số mặc định khi chạy container. Tham số này có thể dễ dàng bị ghi đè hoàn toàn từ dòng lệnh khi chạy `docker run`.
   - `ENTRYPOINT` định nghĩa file thực thi chính của container không thể bị ghi đè. Các tham số bổ sung khi chạy `docker run` sẽ được nối tiếp vào sau lệnh `ENTRYPOINT`.

---

### Exercise 2.3: Image size comparison
- **Develop (Single-stage):** ~1050 MB (Dùng base image `python:3.11` đầy đủ và không dọn dẹp cache pip).
- **Production (Multi-stage + Slim):** ~150 MB (Sử dụng `python:3.11-slim`, chỉ copy file thực thi từ build stage và loại bỏ toàn bộ build-tools như gcc).
- **Dung lượng giảm được:** ~85%

---

### Exercise 2.4: Docker Compose stack
- **Kiến trúc hệ thống (Architecture Diagram):**
  ```
  Client (Request) ──► Nginx Load Balancer (Port 80)
                             │
            ┌────────────────┼────────────────┐ (Round-Robin)
            ▼                ▼                ▼
       Agent Instance 1   Agent Instance 2   Agent Instance 3 (Port 8000)
            │                │                │
            └────────────────┼────────────────┘
                             ▼
                        Redis Server (Port 6379)
  ```
- **Cách thức hoạt động:**
  - Nginx đóng vai trò là Reverse Proxy và Load Balancer lắng nghe ở cổng `80`, chia đều traffic cho 3 instances của Agent.
  - Các Agent instances chạy stateless (không lưu session trong RAM cá nhân). Khi có thông tin lịch sử trò chuyện (Conversation History) hay Rate Limiter, chúng sẽ giao tiếp chung với một container Redis duy nhất.

---

## Part 3: Cloud Deployment

### Exercise 3.1: Railway deployment
- **URL deploy thực tế (ví dụ):** `https://balanced-perception-production-07ae.up.railway.app`
- **Sự khác biệt giữa `railway.toml` và `render.yaml`:**
  - `railway.toml` là file cấu hình cục bộ của Railway nhằm định nghĩa lệnh khởi chạy (`startCommand`), đường dẫn health check (`healthcheckPath`), thời gian timeout và chính sách restart khi gặp lỗi.
  - `render.yaml` tuân theo chuẩn **Infrastructure as Code (IaC)** của Render, cho phép định nghĩa đầy đủ tất cả tài nguyên hệ thống (Services, Databases, Redis), cấu hình môi trường, tự động generate API Key và chỉ định Region (ví dụ: `singapore`) trực tiếp trong file cấu hình.

---

## Part 4: API Security

### Exercise 4.1: API Key authentication
- Kết quả test:
  - Nếu gửi request không kèm header `X-API-Key` → Hệ thống trả về lỗi `401 Unauthorized` kèm chi tiết `"Missing API key"`.
  - Nếu gửi sai API Key → Trả về lỗi `403 Forbidden` kèm chi tiết `"Invalid API key"`.
  - Nếu gửi đúng API Key → Trả về `200 OK` và câu trả lời từ mock LLM.

### Exercise 4.2: JWT Authentication (Advanced)
- Luồng hoạt động của JWT (JSON Web Token):
  1. Người dùng gửi Username & Password hợp lệ đến endpoint `/token`.
  2. Server xác thực thông tin và tạo ra một JWT Token (chứa chữ ký bảo mật đã được mã hóa bằng `JWT_SECRET`).
  3. Người dùng đính kèm token này vào header `Authorization: Bearer <token>` cho mọi request sau đó.
  4. Server chỉ cần decode chữ ký để kiểm tra tính hợp lệ mà không cần truy vấn lại cơ sở dữ liệu.

### Exercise 4.3: Rate Limiting
- Thuật toán sử dụng: **Sliding Window Log** hoặc **Token Bucket** qua Redis.
- Giới hạn quy định: `10 requests / phút` cho mỗi user.
- Khi vượt quá giới hạn: Hệ thống trả về `429 Too Many Requests` và kèm header `Retry-After: 60`.

### Exercise 4.4: Cost Guard
- Giải pháp triển khai qua Redis:
  - Mỗi khi user gửi request, hệ thống sẽ ước lượng số token và tính giá tiền ($0.00015/1k input, $0.0006/1k output).
  - Tích lũy tổng chi tiêu trong ngày của user vào một key Redis dạng `budget:<user_id>:<date>` với thời gian hết hạn (TTL) là 24 giờ.
  - Nếu vượt quá budget quy định (ví dụ `$5.0/ngày`), hệ thống sẽ trả về mã lỗi `402 Payment Required` để ngăn chặn các cuộc gọi tốn kém tiếp theo.

---

## Part 5: Scaling & Reliability

### Exercise 5.1: Health & Readiness Checks
- `/health`: Trả về trạng thái hoạt động cơ bản của container (Liveness probe).
- `/ready`: Kiểm tra các kết nối ngoại vi thiết yếu (Readiness probe). Nếu kết nối với cơ sở dữ liệu hoặc Redis bị đứt, endpoint này sẽ trả về lỗi `503 Service Unavailable` để báo hiệu Load Balancer ngừng định tuyến người dùng vào instance lỗi này.

### Exercise 5.2: Graceful Shutdown
- Khi nhận tín hiệu `SIGTERM` từ Cloud Orchestrator, ứng dụng sẽ:
  1. Chuyển trạng thái `is_ready = False` để báo cho Nginx ngưng gửi request mới.
  2. Chờ uvicorn hoàn thành nốt các request đang xử lý dở dang (In-flight requests) trong khoảng thời gian timeout grace period.
  3. Giải phóng các kết nối Redis/DB và thoát chương trình một cách an toàn.

### Exercise 5.3: Stateless Design
- **Anti-pattern:** Lưu trữ `conversation_history` trực tiếp trong RAM của server (Python dict). Khi scale ra nhiều instances, request kế tiếp của user có thể đi tới instance khác vốn không có lịch sử chat, làm mất ngữ cảnh cuộc trò chuyện.
- **Sửa lại (Stateless):** Đưa toàn bộ dữ liệu lịch sử hội thoại lên Redis. Mọi instances đều có thể truy cập chung vào Redis để đọc và ghi lịch sử hội thoại của bất kỳ user nào thông qua `session_id`.
