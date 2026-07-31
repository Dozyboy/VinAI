# Reflection — Lab 20 (Personal Report)

> **Đây là báo cáo cá nhân.** Mỗi học viên chạy lab trên laptop của mình, với spec của mình. Số liệu của bạn không so sánh được với bạn cùng lớp — chỉ so sánh **before vs after trên chính máy bạn**. Grade rubric tính theo độ rõ ràng của setup + tuning của bạn, không phải tốc độ tuyệt đối.

---

**Họ Tên:** Thiều Quang Minh
**Cohort:** A20-K1
**Ngày submit:** 2026-07-12

---

## 1. Hardware spec (từ `00-setup/detect-hardware.py`)

- **OS:** Windows 10 (AMD64)
- **CPU:** Intel(R) Core(TM) i7-3770K CPU @ 3.50GHz
- **Cores:** 4 physical / 8 logical cores
- **CPU extensions:** AVX
- **RAM:** 12.0 GB
- **Accelerator:** nvidia_cuda (NVIDIA GeForce GT 1030, 2048 MiB VRAM)
- **llama.cpp backend đã chọn:** CPU (do GPU GT 1030 có dung lượng VRAM quá nhỏ 2GB nên script tự động chọn CPU wheel để hoạt động ổn định nhất)
- **Recommended model tier:** Qwen2.5-1.5B-Instruct (Q4_K_M)

**Setup story** (≤ 80 chữ): những gì cần thay đổi để lab chạy được trên máy bạn:
Do GPU NVIDIA GT 1030 2GB không đủ VRAM để offload hiệu quả các mô hình lớn và cài đặt CUDA Toolkit phức tạp trên Windows, hệ thống đã cài đặt bản CPU prebuilt của llama-cpp-python để chạy ổn định hơn. Tôi cũng đã thiết lập $env:PYTHONIOENCODING="utf-8" để khắc phục lỗi bảng mã ký tự Unicode trên PowerShell.

---

## 2. Track 01 — Quickstart numbers (từ `benchmarks/01-quickstart-results.md`)

| Model | Load (ms) | TTFT P50/P95 (ms) | TPOT P50/P95 (ms) | E2E P50/P95/P99 (ms) | Decode rate (tok/s) |
|---|--:|--:|--:|--:|--:|
| qwen2.5-1.5b-instruct-q4_k_m.gguf | 916 | 532 / 798 | 99.4 / 111.1 | 6839 / 7671 / 7997 | 10.1 |
| qwen2.5-1.5b-instruct-q2_k.gguf | 662 | 610 / 722 | 76.9 / 88.5 | 5474 / 6195 / 6202 | 13.0 |

**Một quan sát** (≤ 50 chữ): Q4_K_M vs Q2_K trên máy bạn — số liệu nói gì? Quality đáng đánh đổi không?
Mô hình Q2_K tải nhanh hơn và cho tốc độ giải mã (Decode rate) cao hơn khoảng 28.7% (13.0 so với 10.1 tok/s). Tuy nhiên, định dạng Q4_K_M cho câu trả lời mạch lạc, chính xác hơn rõ rệt và độ trễ TTFT tương đương, rất đáng để đánh đổi.

---

## 3. Track 02 — llama-server load test

| Concurrency | Total RPS | TTFB P50 (ms) | E2E P95 (ms) | E2E P99 (ms) | Failures |
|--:|--:|--:|--:|--:|--:|
| 10 | 0.10 | 30000 | 48000 | 48000 | 0 |
| 50 | 0.08 | 23000 | 34000 | 34000 | 0 |

**Batching observation** (từ `record-metrics.py`): peak `llamacpp:n_busy_slots_per_decode` / `requests_processing` ở concurrency 50 = `3.8 / 4`, nghĩa là hệ thống đã tận dụng tốt cơ chế Continuous Batching để xử lý đồng thời 4 request trong hàng đợi tại các slot trống mà không làm sập server hay gây lỗi phản hồi.

---

## 4. Track 03 — Milestone integration

- **N16 (Cloud/IaC):** `stub: localhost only` (chạy trực tiếp trên Windows cục bộ)
- **N17 (Data pipeline):** `stub: in-memory dict` (chứa tài liệu đồ chơi phục vụ demo RAG)
- **N18 (Lakehouse):** `stub: SQLite` (CSDL cục bộ lưu trữ văn bản truy vấn)
- **N19 (Vector + Feature Store):** `stub: TOY_DOCS` (chỉ mục từ khóa giả lập tìm kiếm tương đồng)

**Nơi tốn nhiều ms nhất** trong pipeline (đo bằng `time.perf_counter` trong `pipeline.py`):

- embed: `0.0 ms`
- retrieve: `0.1 ms`
- llama-server: `20409.5 ms`

**Reflection** (≤ 60 chữ): bottleneck nằm ở đâu? Có khớp với kỳ vọng không?
Bottleneck nằm hoàn toàn ở bước gọi LLM qua llama-server (chiếm >99.9% thời gian). Kết quả này hoàn toàn khớp với kỳ vọng vì suy luận mô hình ngôn ngữ lớn trên CPU máy tính cá nhân đòi hỏi tính toán rất nặng nề so với các thao tác truy xuất dữ liệu nhẹ ở các bước trước.

---

## 5. Bonus — The single change that mattered most

> **Most important section.** Pick **một** thay đổi từ bonus track (build flag, thread sweep, quant pick, GPU offload, KV-cache quantization, speculative decoding, bất cứ challenge nào trong `BONUS-llama-cpp-optimization/CHALLENGES.md`) đã tạo ra speedup lớn nhất trên máy bạn.

**Change:** Hạ số luồng (thread count) từ `-t 8` (bằng số core logic) xuống `-t 6` khi chạy suy luận trên CPU.

**Before vs after** (sweep output):

```
before (t=8): 6.46 tok/s
after (t=6):  6.85 tok/s
speedup: ~1.06×
```

**Tại sao nó work** (1–2 đoạn ngắn — đây là phần grader đọc kỹ nhất):

Quá trình sinh từ (decode phase) của mô hình ngôn ngữ lớn bản chất là tác vụ bị nghẽn băng thông bộ nhớ (memory-bandwidth bound) chứ không phải nghẽn năng lực tính toán (compute bound). Khi chúng ta sử dụng quá nhiều luồng (ví dụ 8 luồng, bằng với số nhân logic của CPU i7-3770K), các lõi xử lý phải liên tục tranh chấp tài nguyên trên các kênh bộ nhớ RAM hẹp của máy tính cá nhân, làm giảm hiệu suất tổng thể. 

Việc hạ số luồng xuống còn 6 luồng giúp giảm tải tranh chấp bus bộ nhớ và giảm overhead chuyển ngữ cảnh (context switching) giữa các nhân logic của công nghệ Hyper-Threading. Kết quả là tốc độ giải mã tăng từ 6.46 lên 6.85 tok/s (~1.06x speedup), đồng thời CPU chạy mát hơn và ổn định hơn.

---

## 6. (Optional) Điều ngạc nhiên nhất

Tôi ngạc nhiên khi thấy số luồng tối ưu cho tốc độ giải mã mô hình không phải là số nhân logic tối đa (8 luồng), mà lại là 6 luồng. Điều này cho thấy sự ảnh hưởng rất lớn của băng thông RAM đến hiệu năng Model Serving thực tế trên CPU máy tính cá nhân.

---

## 7. Self-graded checklist

- [x] `hardware.json` đã commit
- [x] `models/active.json` đã commit
- [x] `benchmarks/01-quickstart-results.md` đã commit
- [x] `benchmarks/02-server-metrics.csv` đã commit
- [x] `benchmarks/bonus-*.md` đã commit (ít nhất 1 sweep)
- [x] Ít nhất 6 screenshots trong `submission/screenshots/` (xem `submission/screenshots/README.md`)
- [x] `make verify` exit 0 (chạy ngay trước khi push)
- [x] Repo trên GitHub ở chế độ **public**
- [x] Đã paste public repo URL vào VinUni LMS

---

**Quan trọng:** repo phải **public** đến khi điểm được công bố. Nếu private, grader không xem được → 0 điểm.
