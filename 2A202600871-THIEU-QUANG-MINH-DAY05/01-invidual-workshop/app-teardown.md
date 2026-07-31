# Workshop — Mổ App AI Thật

**Thời gian:** 35-45 phút  
**Hình thức:** cá nhân trước, chia sẻ theo nhóm sau  
**Output:** finding note + sketch `as-is / to-be`

Mục tiêu không phải chấm "UI đẹp hay xấu". Mục tiêu là dùng sản phẩm thật như một bài needfinding: tìm chỗ product gãy trong workflow thật, rồi viết finding đó thành quyết định product.

## 1. Chọn một sản phẩm để dùng thử

| Sản phẩm | AI feature | Cách truy cập |
|---|---|---|
| AI Travel Agent (App theo track Day 03) | Trợ lý ReAct Agent tra cứu, so sánh giá vé máy bay/tàu hỏa | Chạy Local qua Terminal bằng mô hình Phi-3-mini |

## 2. Dùng thử: promise vs reality

Ghi nhanh:

- **Product hứa gì?** Agent sẽ tự bóc tách hành trình, gọi tool kiểm tra giá, tính toán chi phí và đưa ra phương án chính xác nhất.
- **User nào được hứa sẽ được giúp?** Người dùng muốn tra cứu chuyến đi và tìm phương án di chuyển tiết kiệm nhất.
- **Bạn kỳ vọng AI làm được task nào?** Tìm chính xác giá vé thật và làm phép toán so sánh để kết luận đi phương tiện nào rẻ hơn bao nhiêu tiền.
- **Khi dùng thật, điểm gãy xuất hiện ở đâu?** AI tìm đúng giá vé nhưng không thể thực hiện phép tính trừ, đồng thời bị cạn ngữ cảnh và chuyển ngữ sang tiếng Anh ở câu chốt cuối cùng.

Evidence cần có:

- **Prompt/input đã thử:** "Tôi muốn đi từ Hà Nội vào Hồ Chí Minh, hãy so sánh giá vé máy bay và tàu hỏa để tôi chọn cái rẻ hơn".
- **Hành vi quan sát được:** Agent lấy được đúng giá máy bay VietJet (1.200.000 VND) và giá tàu SE1 (850.000 VND). Tuy nhiên, Agent không tính ra được số tiền tiết kiệm (350.000 VND) mà chỉ liệt kê lại bảng giá. Câu kết luận cuối cùng tự động chuyển sang tiếng Anh: "Their prices are updated by the database. Based on these prices, the customer can choose the most suitable option for their travel."

## 3. Vẽ 4 paths

| Path | Câu hỏi cần trả lời | Tình trạng trong App |
|---|---|---|
| Happy | Khi AI đúng và tự tin, user thấy gì? | User thấy các bước tư duy (Thought) của Agent và nhận được bảng giá vé thực tế chính xác của máy bay và tàu hỏa. |
| Low-confidence | Khi AI không chắc, hệ thống có hỏi lại, show options hoặc chuyển người không? | **Chưa có.** Hệ thống không biết cách tự đánh giá hoặc báo cáo giới hạn tính toán của mình. |
| Failure | Khi AI sai, user biết bằng cách nào và sửa thế nào? | AI bị cạn kiệt tài nguyên xử lý (Context Window) khi dùng tiếng Việt, dẫn đến không thể suy luận toán học và tràn ngôn ngữ sang tiếng Anh. User tự nhận ra sự cố thông qua text hiển thị. |
| Correction | Khi user sửa, correction có được lưu/log/học lại không hay biến mất? | **Chưa có.** User phải tự tính nhẩm số tiền chênh lệch dựa trên số liệu AI đã cung cấp. |

## 4. Viết finding thành quyết định

Viết:

```text
Khi user yêu cầu so sánh giá vé để chọn phương án rẻ hơn,
AI Agent (dùng mô hình nhỏ SLM Phi-3) tìm được số liệu thô nhưng thất bại trong việc suy luận phép toán trừ,
hậu quả là user chỉ nhận được danh sách giá liệt kê mà không có câu trả lời triệt để, kèm theo văn bản bị lỗi ngôn ngữ.
Lỗi thuộc layer Intent / Model Reasoning (do giới hạn logic toán học của mô hình cục bộ).
Nên sửa bằng Fallback (chuyển việc tính toán chênh lệch cho tool/code Python xử lý thay vì ép LLM tự tính toán) hoặc UX (chỉ hiển thị bảng so sánh rõ ràng cho user tự quyết định).