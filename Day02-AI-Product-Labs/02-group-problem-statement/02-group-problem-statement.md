# 02 — Group Problem Statement

## Group convergence

Nhóm 4 người, mỗi người share top 3. Tổng cộng khoảng 12 candidates.

| Cluster | Candidate examples | Pattern chung |
|---|---|---|
| Sinh dữ liệu / kiểm thử hệ thống | Creating Mock Data in a Relational Database | Tạo đầu vào có ràng buộc logic để test hệ thống hoặc demo |
| Học / giải thích kiến thức chuyên ngành | Chatbot for major subject | Biến tài liệu dài thành phần dễ học, dễ ôn |
| Báo cáo / dịch nội dung | Automate Daily Report & Translation | Gom dữ liệu rồi viết narrative, sau đó dịch sang ngôn ngữ khác |
| Giải thích thuật ngữ / công thức kỹ thuật | AI tutor for technical jargon | Dịch thuật ngữ chuyên môn và công thức sang ngôn ngữ dễ hiểu |

## Shortlist và score

| Candidate | Actor rõ | Workflow rõ | Pain có evidence | Impact đo được | Làm trong lab | So sánh R/W/A được | Nhóm hiểu domain | Tổng |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Automate Daily Report & Translation | 5 | 5 | 5 | 5 | 4 | 4 | 5 | 33 |
| Creating Mock Data in a Relational Database | 4 | 5 | 4 | 5 | 4 | 5 | 4 | 31 |
| Chatbot for major subject | 4 | 5 | 4 | 4 | 5 | 4 | 4 | 30 |
| AI tutor for technical jargon | 4 | 4 | 4 | 4 | 5 | 4 | 4 | 29 |

Nhóm chọn: **Automate Daily Report & Translation**.

Vì sao chọn:

- Workflow rõ nhất: dữ liệu có sẵn, bước viết báo cáo và dịch là bottleneck rõ.
- Có baseline thời gian: 2 tiếng/ngày có thể đo và so với sau khi tự động hóa.
- Có thể validate nhanh bằng dữ liệu mẫu của 1-2 ngày báo cáo gần nhất.
- Có thể tách rõ rule / workflow / human review.
- Dễ vẽ before/after và demo trong lab.

Vì sao không chọn các bài khác:

- Creating Mock Data in a Relational Database: technically interesting nhưng đánh giá đúng/sai dữ liệu liên kết khó hơn, dễ phát sinh nhiều ràng buộc edge case.
- Chatbot for major subject: pain thật nhưng output phụ thuộc mạnh vào từng môn và mức độ chính xác của tài liệu, khó chốt phạm vi ngắn.
- AI tutor for technical jargon: giá trị rõ nhưng scope rộng, dễ trượt sang bài toán dạy học tổng quát thay vì một workflow cụ thể.

## Quick validation

Nhóm hỏi nhanh 3 người quen đang làm QA / QC / report nghiệp vụ.

| Nguồn | Số người | Tín hiệu xác nhận | Tín hiệu phản bác | Nhóm sửa problem thế nào |
|---|---:|---|---|---|
| Quick interview | 3 | 2/3 người nói mất nhiều thời gian nhất ở phần viết narrative và dịch lại cho đúng văn phong | 1 người đã có template cố định nên không đau nhiều ở phần viết | Thu hẹp problem: không phải tự động hóa toàn bộ báo cáo, mà là draft narrative + dịch từ data có sẵn |
| Mini poll trong lớp | 6 | 5/6 từng phải copy/paste dữ liệu vào file tổng hợp trước khi viết báo cáo | Một số team chỉ cần report tiếng Việt, không cần dịch | Thêm non-AI alternative: template + macro/RPA cho phần gom data |

Insight sau validation:

```text
Pain thật không nằm ở việc nhập số đơn thuần. Pain nằm ở đoạn biến dữ liệu rời rạc thành báo cáo có narrative rõ ràng và đúng văn phong để gửi đi ngay cuối ngày.
```

## Research giải pháp

Nhóm tìm các hướng đã có sẵn, không giả định phải tự build từ đầu.

| Nguồn / tool / case | Link | Họ giải quyết phần nào? | Điểm mạnh | Khoảng trống / rủi ro | Bài học cho nhóm |
|---|---|---|---|---|---|
| Excel Power Query | https://support.microsoft.com/office/power-query | Gộp và làm sạch dữ liệu từ nhiều file | Tốt cho việc hợp nhất dữ liệu lặp lại | Không tự viết narrative hay dịch báo cáo | Rule/tool đủ cho bước gom data, chưa đủ cho phần viết |
| RPA / UiPath | https://www.uipath.com/ | Tự động thao tác nhập liệu lên web nội bộ | Giảm copy/paste thủ công | Dễ brittle nếu UI thay đổi | Nên dùng cho bước điền form, không dùng cho phần suy luận |
| Google Translate / DeepL | https://translate.google.com/ | Dịch thô báo cáo sang ngôn ngữ khác | Nhanh, dễ dùng | Thiếu kiểm soát văn phong doanh nghiệp và ngữ cảnh chuyên ngành | AI cần review người thật trước khi gửi |
| LLM writing assistant | https://chat.openai.com/ | Draft narrative từ data đã tổng hợp | Viết nháp nhanh, linh hoạt | Có thể hallucinate hoặc dịch chưa tự nhiên | Dùng AI để draft, không tự động gửi |

Research takeaway:

```text
Không nên build một agent tự làm toàn bộ báo cáo ngay. Hướng hợp lý hơn là Workflow: tự động gộp dữ liệu ở các bước rõ, dùng AI để draft narrative và dịch, sau đó cho người thật review trước khi gửi.
```

## Workflow before/after

File nhóm nộp kèm:

```text
02-group-problem-statement-workflow.png/pdf/md
```

Nội dung workflow:

```text
CURRENT STATE — 6 bước, 120 phút

[1 Mở file Excel: 5']
→ [2 Copy/paste vào Master File: 30']
→ [3 Điền lên web nội bộ: 20']
→ [4 Viết narrative tiếng Việt: 25']  <-- bottleneck
→ [5 Dịch sang tiếng Nhật: 35']
→ [6 Gửi report: 5']

FUTURE STATE — 5 bước, 20 phút

[1 Auto-gộp data vào Master File: 2']  -- Rule/script
→ [2 AI phân tích số liệu bất thường: 1']  -- Workflow step
→ [3 AI draft báo cáo VN & JP: 2']        -- Workflow step
→ [4 Người thật review + sửa nhẹ: 12']    -- Human boundary
→ [5 Gửi report: 3']

Fallback:
AI draft sai số liệu hoặc sai văn phong → Liên bỏ draft và sửa lại bằng template / bản gốc.

Bottleneck mới:
Review + edit của Liên. Đây là bottleneck chấp nhận được vì đó là điểm kiểm soát chất lượng trước khi gửi CEO.
```

Before/after impact:

| Metric | Trước | Sau kỳ vọng | Ghi chú |
|---|---:|---:|---|
| Tổng thời gian | 120 phút | Dưới 20 phút | Target chính |
| Số bước | 6 | 5 | Giảm effort ở bước viết và dịch |
| Bước thủ công | 6/6 | 1/5 | Người thật vẫn review và gửi |
| Bottleneck chính | Viết + dịch | Review/edit | Human boundary |
| Risk mới | Không có AI hallucination | Có hallucination / dịch sai | Cần review trước khi gửi |

## Problem Statement v0

| Field | Nội dung |
|---|---|
| **Actor** | Liên, Quản lý QC phòng ban 500 nhân sự, chịu trách nhiệm báo cáo cho CEO. |
| **Workflow** | Cuối ngày mở nhiều file Excel, copy/paste vào Master File, điền dữ liệu lên web nội bộ, viết narrative tiếng Việt, dịch sang tiếng Nhật rồi gửi report. |
| **Bottleneck** | Bước viết narrative và dịch sang tiếng Nhật mất khoảng 60 phút vì phải tự phân tích số liệu, chọn cách diễn đạt và chỉnh kính ngữ. |
| **Impact** | Tổng workflow mất khoảng 120 phút mỗi ngày; dễ trễ deadline; báo cáo chậm làm CEO thiếu thông tin để ra quyết định. |
| **Success Metric** | Giảm tổng thời gian từ 120 phút xuống dưới 20 phút/ngày; báo cáo tiếng Nhật đúng văn phong và CEO không cần hỏi lại để làm rõ ý. |
| **Boundary** | Không tự gửi report; không tự bịa số liệu; không thay Liên quyết định nội dung cuối; chỉ dùng data được cung cấp. |

## Rule / Workflow / Agent

| Mức | Phương án | Khi nào đủ | Rủi ro | Chọn? |
|---|---|---|---|---|
| **Rule** | Template report, Power Query, macro/RPA, fixed format | Đủ nếu chỉ cần gộp và điền dữ liệu | Không giải quyết phần viết narrative và dịch đa ngôn ngữ | Không chọn làm toàn bộ, nhưng dùng cho bước lấy số |
| **Workflow** | Script gộp data → AI phân tích → AI draft narrative → người thật review | Hợp vì workflow tuyến tính, AI chỉ hỗ trợ vài bước ngôn ngữ | Draft sai/nhạt, cần review | Chọn |
| **Agent** | Agent tự đọc file, phân tích, hỏi thêm, rồi tự gửi report | Chỉ cần nếu nhiều tool, nhiều nhánh, tự quyết bước tiếp theo | Quá rộng, nhiều permission/risk | Chưa chọn |

Mức chọn:

```text
Workflow.
```

Vì sao:

- Data collection có thể dùng rule/script.
- Narrative và dịch cần AI hỗ trợ ngôn ngữ và tổng hợp.
- Liên vẫn review nên risk kiểm soát được.
- Chưa cần agent vì workflow không cần tự lập kế hoạch động.

## Problem Statement v1

| Field | Nội dung |
|---|---|
| **Actor** | Liên, Quản lý QC phòng ban 500 nhân sự. |
| **Workflow** | Mở file Excel → gộp vào Master File → điền lên web nội bộ → viết narrative tiếng Việt → dịch sang tiếng Nhật → review → gửi. |
| **Bottleneck** | Viết narrative và dịch báo cáo từ raw data mất 60 phút, dễ trễ deadline cuối ngày. |
| **Impact** | Khoảng 120 phút/ngày; báo cáo trễ làm CEO thiếu context về chất lượng lô hàng. |
| **Success Metric** | Giảm tổng thời gian xuống dưới 20 phút/ngày; không tăng số lỗi phải sửa lại sau khi gửi. |
| **Boundary** | AI không tự gửi report, không tự bịa số liệu, không thay Liên approve. |
| **AI intervention point** | Sau khi data từ Excel/Master File được gom lại, trước bước Liên viết narrative và dịch. |
| **Mức chọn** | Workflow: rule/script lấy data, AI draft narrative và bản dịch, Liên review. |
| **Rủi ro & người thật kiểm tra** | Risk: hallucination, dịch sai văn phong, bỏ sót số liệu. Người thật review: Liên phải kiểm số liệu và edit trước khi gửi. |

## Final decision

Decision:

```text
Go với scope nhỏ.
```

Pilot nhỏ nhất:

- Dùng data mẫu từ 1 tuần báo cáo gần nhất.
- Chạy workflow bán thủ công: Liên paste Master File summary vào prompt chuẩn.
- AI draft narrative tiếng Việt và tiếng Nhật.
- Liên đo thời gian edit và số lỗi phải sửa.

Exit / rollback:

- Nếu Liên vẫn phải viết lại hơn 70% draft trong 2 tuần liên tiếp, hạ xuống template + RPA.
- Nếu AI bịa số liệu hoặc dịch sai văn phong doanh nghiệp, không cho dùng trực tiếp trong report.

Decision rationale:

- Problem rõ, workflow rõ, metric rõ.
- Có non-AI components.
- AI nằm ở một bước cụ thể, không ôm toàn bộ workflow.
- Human review rõ.

---
