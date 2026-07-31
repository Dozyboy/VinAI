# Ghi chú tích hợp RAG Pipeline (Day 20)

## Các cấu phần được kết nối (N16 - N19)
- **N16 (Cloud/IaC)**: Chạy dưới dạng localhost stub trên máy cá nhân (chạy cục bộ trực tiếp trên Windows).
- **N17 (Data Pipelines)**: Stub sử dụng cấu trúc in-memory dict chứa tập dữ liệu đồ chơi `TOY_DOCS`.
- **N18 (Lakehouse)**: Giả lập (stub) bằng SQLite để truy xuất dữ liệu xử lý nhẹ nhàng cục bộ.
- **N19 (Vector DB / Feature Store)**: Giả lập (stub) bằng chỉ mục từ khóa tương đồng đơn giản dựa trên `TOY_DOCS`.
- **N20 (Serving)**: Kết nối thành công đến API tương thích OpenAI của `llama-server` chạy cục bộ tại `http://localhost:8080/v1`.

## Phân tích độ trễ (Latency Observations)
Dựa trên kết quả đo đạc thời gian bằng `time.perf_counter()` trong `pipeline.py`:
- **Độ trễ truy xuất (Retrieve latency)**: cực kỳ nhỏ, chỉ khoảng **0.0 - 0.1 ms** do thực hiện so khớp từ khóa đơn giản trên bộ nhớ RAM.
- **Độ trễ phục vụ mô hình (LLM inference latency)**: dao động từ **5.803 ms đến 28.374 ms** (tương đương 5.8 đến 28.3 giây) cho mỗi câu hỏi.
- **Kết luận**: Bottleneck lớn nhất của toàn bộ hệ thống RAG nằm hoàn toàn ở thời gian xử lý và tạo văn bản của LLM trên `llama-server`. Điều này hoàn toàn khớp với kỳ vọng vì việc chạy suy luận mô hình 1.5B trên CPU của máy tính cá nhân không có hỗ trợ tăng tốc GPU mạnh mẽ sẽ tốn rất nhiều thời gian compute.
