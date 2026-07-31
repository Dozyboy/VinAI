# Individual Report: Lab 3 - Chatbot vs ReAct Agent

- **Student Name**: THIEU QUANG MINH
- **Student ID**: 2A202600871
- **Date**: 01-06-2026

---

## I. Technical Contribution (15 Points)

*Describe your specific contribution to the codebase (e.g., implemented a specific tool, fixed the parser, etc.).*

- **Modules Implemented**: Hoàn thiện file cốt lõi `src/agent/agent.py` và các hàm giả lập công cụ lấy dữ liệu tại `tools/travel_tools.py`.
- **Code Highlights**: Áp dụng thành công vòng lặp `while steps < self.max_steps` để khống chế số bước suy luận (chống Infinite Loop). Sử dụng biểu thức chính quy (Regex) `re.search(r"Action:\s*(\w+)\((.*)\)", response)` để bóc tách chính xác tên công cụ và tham số từ LLM.
- **Documentation**: Xây dựng System Prompt ép buộc mô hình tuân thủ cấu trúc ReAct (Thought -> Action -> Observation). Thiết lập logic nối Observation tự động vào ngữ cảnh `current_prompt` để LLM đọc ở lượt tiếp theo.

---

## II. Debugging Case Study (10 Points)

*Analyze a specific failure event you encountered during the lab using the logging system.*

- **Problem Description**: Agent bị gọi trùng một công cụ `search_train_ticket('Hà Nội', 'Hồ Chí Minh')` liên tiếp ở Step 2 và Step 3 mà không tự chuyển qua kết luận ngay, đồng thời câu trả lời cuối (Final Answer) bị lẫn tiếng Anh.
- **Log Source**: 
  ```text
  [Agent Step 2]: Action: search_train_ticket('Hà Nội', 'Hồ Chí Minh')
  [Observation]: Vé tàu SE1 Hà Nội - Sài Gòn: Ghế mềm điều hòa - 850.000 VND (Khởi hành lúc 22:15).
  [Agent Step 3]: Thought: Người dùng có thể tìm giá vé tàu hỏa tùy anh từ hệ thế tinh tế.
  Action: search_train_ticket('Hà Nội', 'Hồ Chí Minh')
  ```
- **Diagnosis**: Do sử dụng SLM (Mô hình ngôn ngữ nhỏ - Phi-3-mini-4k) chạy local, khả năng ghi nhớ ngữ cảnh (Context Window) bị hạn chế khi dịch từ tư duy tiếng Việt sang cấu trúc tiếng Anh của ReAct. Hệ thống prompts chưa đủ các ví dụ `Few-Shot` rõ ràng bằng tiếng Việt khiến mô hình bị lúng túng (loop) trước khi dứt điểm bằng `Final Answer`.
- **Solution**: 
  - *Về code*: Thêm logic kiểm tra (guardrails) nếu `tool_name` và `args` trùng với step ngay trước đó thì tự động trả về thông báo ép LLM đưa ra kết luận.
  - *Về Prompt*: Bổ sung chỉ thị nghiêm ngặt vào System Prompt: "Không gọi lại công cụ nếu đã có kết quả. Trả lời Final Answer 100% bằng tiếng Việt".

---

## III. Personal Insights: Chatbot vs ReAct (10 Points)

*Reflect on the reasoning capability difference.*

1. **Reasoning**: Khối `Thought` đóng vai trò như "tiếng nói nội tâm", giúp Agent tự nhận diện lỗ hổng kiến thức (Ví dụ: Biết là đã có giá máy bay nhưng chưa có giá tàu hỏa) để chủ động đi tìm. Điều này khắc phục triệt để bệnh "ảo tưởng" (hallucination) của Chatbot thông thường (Chatbot tự bịa giá vé từ 10-20 triệu VND).
2. **Reliability**: Agent chạy local thực sự kém ổn định hơn Chatbot ở khoản diễn đạt ngôn ngữ. Việc phụ thuộc vào Regex parsing khiến hệ thống dễ bị sập (crash) nếu LLM sinh sai định dạng chữ `Action:` hoặc quên đóng ngoặc.
3. **Observation**: Môi trường cung cấp số liệu thực tế (1.200.000 VND và 850.000 VND) đóng vai trò làm điểm tựa (grounding), ép mô hình phải kết luận dựa trên dữ liệu thật thay vì dự đoán thống kê như Chatbot tĩnh.

---

## IV. Future Improvements (5 Points)

*How would you scale this for a production-level AI agent system?*

- **Scalability**: Chuyển đổi framework từ vòng lặp tĩnh sang `LangGraph` để quản lý các luồng (flow) phức tạp hơn thay vì if-else đơn thuần.
- **Safety**: Bổ sung bộ lọc đầu vào (Input Sanitization) cho các tham số truyền vào `Action` để chống lại các lỗ hổng Prompt Injection từ phía người dùng.
- **Performance**: Nâng cấp lên các mô hình thương mại qua API (như Gemini 2.5 Flash hoặc Llama-3 70B) để giải quyết bài toán đa ngôn ngữ và tăng tốc độ xử lý (latency hiện tại đang là ~83 giây cho 4 steps trên CPU).

---

> [!NOTE]
> Submit this report by renaming it to `REPORT_[YOUR_NAME].md` and placing it in this folder.