# Reflection — Lab 19

**Tên:** Thiều Quang Minh
**Cohort / MSSV:** 2A202600871
**Path đã chạy:** lite

---

## Câu hỏi (≤ 200 chữ)

- **exact**: BM25 và Hybrid cùng thắng (96.7%) nhờ khớp verbatim hoàn toàn.
- **paraphrase**: BM25 (33.3%) và Hybrid (32.0%) vượt Semantic (24.0%) do `bge-small-en` không được tối ưu cho tiếng Việt (đổi sang `bge-m3` ở bản Docker sẽ cải thiện rõ).
- **mixed**: Hybrid thắng tuyệt đối (100.0% so với 97.0% BM25, 98.5% Semantic) nhờ kết hợp bổ trợ cả 2 tín hiệu.

**Khi nào không dùng hybrid**:
1. Hệ thống yêu cầu latency cực thấp (< 5ms) mà việc chạy cả 2 bộ tìm kiếm rồi fusion tốn tài nguyên và thời gian.
2. Tập dữ liệu tìm kiếm là dạng mã số, SKU, hoặc từ khóa cố định (dùng BM25/Lexical là đủ).

---

## Điều ngạc nhiên nhất khi làm lab này

Sử dụng RRF=60 cực kì đơn giản nhưng lại gom kết quả và sửa lỗi cho cả 2 mode kia rất hiệu quả trên tập mixed.

---

## Bonus challenge

- [ ] Đã làm bonus (xem `bonus/`)
- [ ] Pair work với: _N/A_
