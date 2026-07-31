# Ngày 1 — Bài Tập & Phản Ánh
## Nền Tảng LLM API | Phiếu Thực Hành

**Thời lượng:** 1:30 giờ  
**Cấu trúc:** Lập trình cốt lõi (60 phút) → Bài tập mở rộng (30 phút)

---

## Phần 1 — Lập Trình Cốt Lõi (0:00–1:00)

Chạy các ví dụ trong Google Colab tại: https://colab.research.google.com/drive/172zCiXpLr1FEXMRCAbmZoqTrKiSkUERm?usp=sharing

Triển khai tất cả TODO trong `template.py`. Chạy `pytest tests/` để kiểm tra tiến độ.

**Điểm kiểm tra:** Sau khi hoàn thành 4 nhiệm vụ, chạy:
```bash
python template.py
```
Bạn sẽ thấy output so sánh phản hồi của GPT-4o và GPT-4o-mini.

---


## Phần 2 — Bài Tập Mở Rộng (1:00–1:30)

### Bài tập 2.1 — Độ Nhạy Của Temperature
Gọi `call_openai` với các giá trị temperature 0.0, 0.5, 1.0 và 1.5 sử dụng prompt **"Hãy kể cho tôi một sự thật thú vị về Việt Nam."**

**Bạn nhận thấy quy luật gì qua bốn phản hồi?** (2–3 câu)
- **Quan sát:** Khi `temperature` tăng, câu trả lời càng đa dạng và sáng tạo hơn — từ rất chính xác, ngắn gọn và lặp lại ở `0.0`, đến câu chữ phong phú, có ví dụ và suy diễn hơn ở `1.0` và `1.5`. Ở `0.5` thường là sự cân bằng giữa tính chính xác và sáng tạo.

**Bạn sẽ đặt temperature bao nhiêu cho chatbot hỗ trợ khách hàng, và tại sao?**
- **Đáp án:** `0.0` (hoặc tối đa `0.2`) — vì chatbot hỗ trợ cần phản hồi nhất quán, dễ dự đoán và tránh tạo ra thông tin sai lệch; nhiệt độ thấp giúp giảm tính sáng tạo không mong muốn.

---

### Bài tập 2.2 — Đánh Đổi Chi Phí
Xem xét kịch bản: 10.000 người dùng hoạt động mỗi ngày, mỗi người thực hiện 3 lần gọi API, mỗi lần trung bình ~350 token.

**Ước tính xem GPT-4o đắt hơn GPT-4o-mini bao nhiêu lần cho workload này:**
- **Tính toán:**
	- Lượt gọi/ngày = 10.000 * 3 = 30.000 cuộc gọi
	- Trung bình token mỗi cuộc gọi = 350 token = 0.35 K token
	- Giá mỗi 1K output tokens: GPT-4o = $0.010 ; GPT-4o-mini = $0.0006
	- Chi phí GPT-4o mỗi cuộc gọi ≈ 0.35 * $0.010 = $0.0035
	- Chi phí GPT-4o-mini mỗi cuộc gọi ≈ 0.35 * $0.0006 = $0.00021
	- Tổng/ngày GPT-4o ≈ 30.000 * $0.0035 = $105.00
	- Tổng/ngày GPT-4o-mini ≈ 30.000 * $0.00021 = $6.30
	- Tỷ lệ: $105.00 / $6.30 ≈ **16.7 lần**

**Mô tả một trường hợp mà chi phí cao hơn của GPT-4o là xứng đáng, và một trường hợp GPT-4o-mini là lựa chọn tốt hơn:**
- **Khi dùng GPT-4o (xứng đáng):** Tác vụ yêu cầu khả năng suy luận sâu, phân tích phức tạp, hoặc độ chính xác & an toàn cao (ví dụ: tư vấn pháp lý/medical triage/soạn thảo hợp đồng), nơi hậu quả của thông tin sai lệch lớn.
- **Khi dùng GPT-4o-mini (phù hợp):** Ứng dụng quy mô lớn, tác vụ đơn giản hoặc mang tính tiện ích (ví dụ: chatbot FAQ, xử lý truy vấn tìm kiếm, phân loại nội dung), nơi chi phí thấp và tốc độ quan trọng hơn chất lượng sáng tạo tối đa.

---

### Bài tập 2.3 — Trải Nghiệm Người Dùng với Streaming
**Streaming quan trọng nhất trong trường hợp nào, và khi nào thì non-streaming lại phù hợp hơn?** (1 đoạn văn)
- **Trả lời:** Streaming quan trọng khi phản hồi dài hoặc khi trải nghiệm tương tác thời gian thực là ưu tiên — ví dụ trả lời theo từng phần giúp người dùng cảm giác hệ thống đang "nhập" và giảm độ trễ cảm nhận, rất hữu ích cho chat dài, viết sáng tạo theo từng bước hoặc khi muốn hiển thị tiến trình xử lý. Non-streaming phù hợp hơn khi phản hồi ngắn, cần kết quả nguyên khối để kiểm thử/caching, hoặc khi triển khai đơn giản và nhất quán là ưu tiên.

## Danh Sách Kiểm Tra Nộp Bài
- [ ] Tất cả tests pass: `pytest tests/ -v`
- [ ] `call_openai` đã triển khai và kiểm thử
- [ ] `call_openai_mini` đã triển khai và kiểm thử
- [ ] `compare_models` đã triển khai và kiểm thử
- [ ] `streaming_chatbot` đã triển khai và kiểm thử
- [ ] `retry_with_backoff` đã triển khai và kiểm thử
- [ ] `batch_compare` đã triển khai và kiểm thử
- [ ] `format_comparison_table` đã triển khai và kiểm thử
- [ ] `exercises.md` đã điền đầy đủ
- [ ] Sao chép bài làm vào folder `solution` và đặt tên theo quy định 
