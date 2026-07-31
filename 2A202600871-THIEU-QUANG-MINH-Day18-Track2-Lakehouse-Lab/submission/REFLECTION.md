# Phản hồi về Lakehouse Anti-Patterns

Trong số các anti-pattern của Lakehouse, hệ thống dữ liệu của chúng tôi dễ gặp rủi ro nhất với **"Vấn đề file nhỏ" (Small-File Problem)**.

### Lý do:
1. **Đặc thù dữ liệu**: Hệ thống giám sát cuộc gọi LLM (LLM observability) ghi nhận dữ liệu liên tục theo thời gian thực. Việc append liên tục các lô dữ liệu (micro-batches) nhỏ vào tầng Bronze sẽ sinh ra hàng ngàn tệp Parquet dung lượng cực nhỏ (chỉ vài KB).
2. **Tác động**: Quá nhiều file nhỏ gây quá tải metadata trong transaction log (`_delta_log`), làm tăng chi phí I/O (file open/close overhead) và suy giảm hiệu năng truy vấn của DuckDB/Spark khi tổng hợp dữ liệu.

### Giải pháp khắc phục:
Chúng tôi áp dụng định kỳ lệnh `OPTIMIZE` để thực hiện compaction (gộp các tệp nhỏ thành tệp tối ưu khoảng 256MB) kết hợp với `Z-ORDER BY` cho các trường hay dùng lọc (như `model` hoặc `user_id`) giúp công cụ truy vấn bỏ qua file (file skipping) hiệu quả hơn.
