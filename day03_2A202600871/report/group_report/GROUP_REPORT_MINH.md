# Group Report: Lab 3 - Production-Grade Agentic System

- **Team Name**: [MINH]
- **Team Members**: [THIEU QUANG MINH]
- **Deployment Date**: [2026-06-01]

---

## 1. Executive Summary

*Tổng quan về mục tiêu và kết quả thử nghiệm của hệ thống Agent.*

- **Mục tiêu**: Xây dựng Trợ lý Du lịch thông minh có khả năng tự động tra cứu, so sánh giá vé máy bay và tàu hỏa theo thời gian thực.
- **Success Rate**: Đạt 100% độ chính xác về mặt truy xuất dữ liệu trong kịch bản tra cứu tuyến đường Hà Nội - TP.HCM.
- **Key Outcome**: Hệ thống Agent đã khắc phục hoàn toàn hiện tượng Ảo tưởng (Hallucination) của Chatbot baseline. Tuy nhiên, hệ thống bị ảnh hưởng bởi giới hạn suy luận toán học của mô hình cục bộ (SLM), chưa thể tự tính toán số tiền chênh lệch (350.000 VND).

---

## 2. System Architecture & Tooling

### 2.1 ReAct Loop Implementation
Hệ thống sử dụng vòng lặp `Thought -> Action -> Observation`. LLM đóng vai trò là não bộ sinh ra các lệnh thực thi. Module Python parsing lệnh, gọi vào các mock API (tools) và trả về `Observation` để nối vào ngữ cảnh tiếp tục vòng lặp cho đến khi xuất hiện `Final Answer`.

### 2.2 Tool Definitions (Inventory)
| Tool Name | Input Format | Use Case |
| :--- | :--- | :--- |
| `search_flight_ticket` | `string` (Tuyến đường) | Truy xuất giá vé máy bay và lịch bay của các hãng (VietJet, VNA). |
| `search_train_ticket` | `string` (Tuyến đường) | Truy xuất giá vé tàu hỏa và lịch trình khởi hành (Ví dụ: Tàu SE1). |

### 2.3 LLM Providers Used
- **Primary**: Local Model `Phi-3-mini-4k-instruct-q4.gguf` (via llama-cpp-python) chạy trên CPU.
- **Secondary (Backup)**: `gemini-1.5-flash` / `llama-3.3-70b` (thông qua cổng OpenRouter API để dự phòng khi Local Model bị quá tải context).

---

## 3. Telemetry & Performance Dashboard

*Các chỉ số đo lường thực tế trích xuất từ log hệ thống (File logs/JSON).*

- **Tổng thời gian xử lý (Total Latency)**: ~83,000ms (Từ `04:18:14` đến `04:19:37`).
- **Tổng số bước xử lý (Total Steps)**: 4 steps (3 steps gọi tool + 1 step Final Answer).
- **Trạng thái hoàn thành (Status)**: `success`.
- **Total Cost of Test Suite**: $0.00 (Chạy 100% tài nguyên CPU Local).

---

## 4. Root Cause Analysis (RCA) - Failure Traces

*Phân tích nguyên nhân khi Agent không đạt được hiệu suất tối ưu.*

### Case Study: Agent không tính được số tiền tiết kiệm
- **Input**: "So sánh giá vé máy bay và tàu hỏa để tôi chọn cái rẻ hơn."
- **Observation**: Agent gọi đúng số liệu (Máy bay: 1.200.000, Tàu hỏa: 850.000) nhưng Final Answer chỉ dừng lại ở việc liệt kê chứ không thực hiện phép tính 1.200.000 - 850.000.
- **Root Cause (Reasoning Gap)**: Mô hình Phi-3 là SLM (chỉ 3.8 tỷ tham số), tập trung vào dự đoán token nên thiếu hụt module suy luận toán học (Math Reasoning) chuyên sâu. Khi xử lý ngữ cảnh đa ngôn ngữ (Tiếng Việt), mô hình bị cạn kiệt tài nguyên xử lý dẫn tới mất khả năng thực hiện phép trừ.

---

## 5. Ablation Studies & Experiments

### Thử nghiệm thực tế: Chatbot vs Agent

| Kịch bản Test | Kết quả của Chatbot tĩnh | Kết quả của ReAct Agent | Nhận xét (Winner) |
| :--- | :--- | :--- | :--- |
| So sánh giá vé HN - HCM để chọn cái rẻ hơn. | **Sai / Ảo tưởng**: Bịa ra giá máy bay 10-20 triệu, tàu hỏa 15-25 triệu. Tiếng Việt lủng củng. | **Chính xác dữ liệu**: Gọi đúng tool để lấy giá VietJet (1.2tr), VNA (2.1tr), Tàu SE1 (850k). | **Agent** (Vượt trội hoàn toàn về khả năng Grounding dữ liệu). |

---

## 6. Production Readiness Review

*Các điểm cần cải thiện trước khi triển khai hệ thống vào môi trường thực tế (Production).*

- **Security**: Ẩn các biến nội bộ và API keys trong các file logs. Phải có module kiểm tra các câu lệnh `Action:` tránh việc tiêm mã độc (Command Injection) khi map với hàm hệ thống.
- **Guardrails**: Thiết lập `max_steps = 5` cứng trong core logic để ngắt vòng lặp, ngăn chặn hiện tượng "Infinite Tool Loop" gây tốn tài nguyên hoặc cạn tiền API.
- **Scaling**: Nâng cấp lên kiến trúc đa agent (Multi-Agent). Một Agent chuyên Router (điều hướng câu hỏi), một Agent chuyên Execute (gọi tool), và một Agent chuyên Critic (kiểm tra lại phép toán và ngữ pháp trước khi trả về cho người dùng).
