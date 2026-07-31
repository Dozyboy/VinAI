# Phần B: Báo cáo Đánh giá Cá nhân (Individual Reflection & Report)

### 1. Phân tích Kiến trúc Bảo mật Đa lớp (Multi-layer Defense Architecture)
Trong dự án này, tôi đã thiết kế và triển khai một hệ thống bảo vệ AI Agent cho VinBank với 3 chốt chặn an ninh quan trọng:
* **Input Guardrails (Lọc Đầu Vào):** Chặn đứng các nỗ lực Prompt Injection và đánh lạc hướng chủ đề (Off-topic) bằng Regex và bộ lọc từ khóa.
* **Output Guardrails (Lọc Đầu Ra):** Sử dụng các biểu thức chính quy (Regex) để ẩn đi các thông tin nhạy cảm (PII) như mật khẩu, API Key, đồng thời tích hợp một LLM Judge đóng vai trò "Giám khảo" kiểm duyệt nội dung trước khi xuất ra cho người dùng.
* **Semantic Guardrails (NeMo Guardrails):** Đây là bước nâng cấp mang tính công nghiệp. Bằng cách sử dụng ngôn ngữ Colang, hệ thống không chỉ bắt từ khóa cứng nhắc mà còn hiểu được **ngữ nghĩa** của các đòn tấn công (như đóng giả CEO, mã hóa Base64), từ đó chặn đứng rủi ro ở mức độ sâu hơn.

### 2. Các thách thức Kỹ thuật & Giải pháp (Technical Challenges & Resolutions)
Quá trình triển khai thực tế không hề dễ dàng, tôi đã gặp và giải quyết dứt điểm các vấn đề sau:
* **Dependency Hell (Xung đột thư viện):** Việc chia tách kiến trúc của `langchain` và `langchain_community` gây ra lỗi thiếu module. *Giải pháp:* Thiết lập lại môi trường, cài đặt bổ sung các mảnh ghép thư viện chính xác và quản lý chặt chẽ phiên bản bằng cách khởi động lại Runtime.
* **Lỗi Rate Limit (429 RESOURCE_EXHAUSTED):** Khi chạy Automated Security Pipeline (TODO 11), việc gọi API liên tục khiến Google khóa giới hạn (Free Tier Limit). *Giải pháp:* Tôi đã chủ động cấu hình lại hệ thống để chuyển đổi luồng dữ liệu (Base URL) sang nền tảng **OpenRouter**, sử dụng API Key trả phí để giải quyết triệt để rào cản tốc độ.
* **Lỗi Model Routing (400 Bad Request):** OpenRouter không nhận diện tên model nội bộ của Google. *Giải pháp:* Đọc tài liệu hệ thống và chuẩn hóa lại biến `model` thành `google/gemini-flash-1.5`, đồng bộ `engine` thành `openai` để NeMo kết nối thành công.

### 3. Tầm quan trọng của Human-in-the-Loop (HITL)
Bài học lớn nhất rút ra là: **Không có hệ thống AI nào an toàn tuyệt đối**. Do đó, thiết kế HITL là trái tim của việc quản trị rủi ro:
* **Escalate (Human-as-tiebreaker):** Áp dụng cho các tác vụ thay đổi dữ liệu nhạy cảm (Account Takeover). Sự can thiệp của con người là bắt buộc để ra quyết định cuối cùng.
* **Queue Review (Human-in-the-loop):** Áp dụng cho các giao dịch rủi ro tài chính cao (Chuyển tiền hạn mức lớn). AI đóng vai trò đề xuất, con người đóng vai trò phê duyệt.
* Thiết kế này giúp cân bằng hoàn hảo giữa **Tự động hóa (Tối ưu chi phí)** và **Kiểm soát rủi ro (Bảo vệ ngân hàng)**.

### 4. Đề xuất cải tiến hệ thống trong tương lai (Future Improvements)
Nếu có thêm thời gian phát triển, tôi sẽ mở rộng hệ thống theo 2 hướng:
1. **Dynamic Threat Intelligence:** Xây dựng một vòng lặp phản hồi (Feedback Loop) lấy log từ các đòn tấn công bị chặn ở Pipeline tự động để liên tục cập nhật thêm tập luật mới cho NeMo Guardrails (Colang files) mà không cần deploy lại code.
2. **Tích hợp RAG (Retrieval-Augmented Generation):** Kết hợp Guardrails với cơ sở dữ liệu pháp lý và chính sách nội bộ của VinBank. Khi đó, Agent không chỉ từ chối câu hỏi độc hại mà còn có thể trích dẫn chính xác điều khoản quy định để giải thích một cách chuyên nghiệp cho khách hàng.