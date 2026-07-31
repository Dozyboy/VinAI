# Reflection — Day 17 (≤ 200 words)

Answer briefly, in your own words. This is graded on reasoning, not length.

1. **The flywheel.** Day 13 emitted agent traces; today you turned them into an
   eval set and DPO pairs that Day 22 will train on. Which step in
   `traces → Bronze → datasets` would break most silently in production if you
   got it wrong — and how would you detect it?

2. **Decontamination.** Your run dropped 2 of 3 preference pairs because their
   prompts were in the eval set. What concretely goes wrong if you *skip* this
   step and train on those pairs? How would the lie show up in your metrics?

3. **Point-in-time.** The naive join leaked a future `lifetime_spend` into the
   training row. Describe one feature in a system you know that would be
   dangerous to join without an `ASOF`/point-in-time guard.

4. **Graph vs vector.** From `kg_demo.py`, name one question the knowledge graph
   answers well that flat chunk retrieval (`embed.py`) would struggle with, and
   one where the graph is overkill.

_Write your answers below._

1. **The flywheel:** Việc làm phẳng cây span (`traces_to_bronze`) dễ lỗi ngầm nhất. Nếu cấu trúc telemetry thay đổi làm bỏ sót span con, pipeline vẫn chạy không lỗi nhưng mất dữ liệu. Phát hiện bằng cách giám sát số lượng span thực tế so với logs của agent.
2. **Decontamination:** Bỏ qua bước này gây rò rỉ dữ liệu từ tập test vào tập train (data leakage). Mô hình sẽ học vẹt câu trả lời có sẵn, làm điểm số đánh giá cao bất thường (99%+) nhưng hiệu năng thực tế khi chạy thật rất tệ.
3. **Point-in-time:** Các đặc trưng tích lũy như `churn_status` hoặc `cumulative_fraud_reports`. Việc dùng thông tin gian lận trong tương lai để dự đoán giao dịch trong quá khứ sẽ gây rò rỉ dòng thời gian (time-travel leak), khiến mô hình học tốt offline nhưng thất bại online.
4. **Graph vs vector:** KG vượt trội với các câu hỏi đa bước (multi-hop) cần kết nối thông tin giữa các chunk (ví dụ: *"Phụ kiện của widget được vận chuyển từ đâu?"* qua liên kết `widget -> phụ kiện -> Hà Nội`). KG là dư thừa với các câu hỏi tìm kiếm trực tiếp trong một chunk (ví dụ: *"Gadget bảo hành bao lâu?"*).


