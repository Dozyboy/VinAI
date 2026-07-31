# Thiết kế Hệ thống Data Pipeline: Lai ghép Knowledge Graph và Vector RAG cho Luật Đất Đai Việt Nam 2024

Hệ thống được thiết kế để giải quyết bài toán tra cứu pháp lý phức tạp liên quan đến Luật Đất đai 2024 và các Nghị định hướng dẫn thi hành. Các câu hỏi pháp luật của người dùng thường mang tính chất đa bước (multi-hop) và yêu cầu tính chính xác tuyệt đối, tránh hiện tượng ảo giác (hallucination) của LLM.

---

## 1. Sơ đồ Kiến trúc Hệ thống (Architecture Diagram)

```
[Văn bản Luật & Nghị định (PDF/DOCX)]
                 │
                 ▼
     [Text Cleaning & Parse]
                 │
       ┌─────────┴─────────┐
       ▼                   ▼
 [Recursive Chunking]  [LLM-based Entity & Relation Extraction]
       │                   │ (Subject, Relation, Object)
       ▼                   ▼
 [Vector Embeddings]   [Entity Resolution & Canonicalization]
       │                   │
       ▼                   ▼
 [Vector Database]     [Graph Database (Neo4j/Memgraph)]
 (e.g., Qdrant)            │
       │                   ▼
       │             [Ontology Enforcement (Cơ quan, Điều kiện, Loại đất)]
       │                   │
       └─────────┬─────────┘
                 ▼
      [Hybrid Retriever Engine]
                 │
                 ├────────────────────────┐
                 ▼                        ▼
      [Flat Chunk Retrieval]    [Graph BFS Traversal (Multi-Hop)]
                 │                        │
                 └───────────┬────────────┘
                             ▼
                    [Reranking (Cohere)]
                             │
                             ▼
                     [Context Builder]
                             │
                             ▼
                 [LLM Generator (with Citations)]
                             │
                             ▼
                       [Final Answer]
```

---

## 2. Các Quyết định Thiết kế & Đánh đổi (Design Choices & Tradeoffs)

Dưới đây là 5 câu hỏi then chốt được lựa chọn từ phiên brainstorm để giải quyết bài toán thực tế này:

### Câu hỏi 1: Nguồn & hình dạng dữ liệu (Data Source & Drift)
* **Quyết định:** Nguồn dữ liệu gồm Văn bản Luật Đất đai 2024 cùng các Nghị định (ví dụ Nghị định 101/2024/NĐ-CP về cấp sổ đỏ). Hình dạng dữ liệu là văn bản phi cấu trúc nhưng có tính phân cấp cao (Chương > Mục > Điều > Khoản > Điểm) và chứa nhiều mối liên kết chéo (ví dụ: "áp dụng theo điều kiện tại Khoản 2 Điều 150"). Schema của tài liệu nguồn tương đối ổn định sau khi ban hành, nhưng xảy ra hiện tượng **schema drift** về mặt ngữ nghĩa (semantic drift) khi có các thông tư, nghị định mới hướng dẫn chi tiết làm thay đổi cách áp dụng luật cũ hoặc bổ sung các trường hợp đặc biệt.
* **Đánh đổi:** Thay vì lưu trữ thô toàn bộ tài liệu dưới dạng text dài, chúng tôi trích xuất cấu trúc phân cấp chặt chẽ này thành siêu dữ liệu (metadata) của từng chunk. Điều này tăng độ phức tạp của bước ingest nhưng giúp thuật toán tìm kiếm có thể lọc chính xác theo điều khoản cụ thể.

### Câu hỏi 2: Phi cấu trúc -> RAG hay KG?
* **Quyết định:** Chọn mô hình **Lai ghép (Hybrid RAG + KG)**.
* **Đánh đổi (Vector RAG vs. Knowledge Graph):**
  * *Vector RAG (Chỉ dùng Vector Database):* Triển khai nhanh, rẻ, tìm kiếm tương đồng ngữ nghĩa tốt với các câu hỏi đơn giản (ví dụ: "Thời hạn sử dụng đất nông nghiệp là bao lâu?"). Tuy nhiên, Vector RAG hoàn toàn thất bại với câu hỏi đa bước (multi-hop) như "Cơ quan nào có thẩm quyền cấp sổ đỏ cho đất do UBND xã giao trước năm 2014 và cần những giấy tờ gì?". Thông tin về "thẩm quyền" nằm ở một điều, thông tin về "thời điểm trước năm 2014" nằm ở một điều khác, và "giấy tờ" nằm ở một nghị định khác. Vector database không thể thực hiện phép "join" ngữ nghĩa này.
  * *Knowledge Graph (KG):* Lưu trữ các thực thể (Ví dụ: `Đất trồng lúa`, `UBND cấp Huyện`, `Sổ đỏ`) và mối quan hệ giữa chúng (Ví dụ: `CÓ_THẨM_QUYỀN_CẤP`, `ĐIỀU_KIỆN_ÁP_DỤNG`). KG cho phép thực hiện truy vấn đi qua nhiều bước (graph traversal) để tìm ra câu trả lời chính xác, tránh tuyệt đối việc LLM tự suy diễn sai lệch. Tuy nhiên, chi phí xây dựng đồ thị lớn và khó xử lý các câu hỏi mang tính mô tả chung chung.
  * *Kết luận:* Xây dựng đồ thị cho các mối quan hệ thực thể cốt lõi để làm mỏ neo (anchor), kết hợp với truy vấn vector để lấy thông tin chi tiết của từng điều khoản.

### Câu hỏi 3: Cái gì vỡ khi scale? (Scale Bottlenecks)
* **Quyết định:** Bottleneck lớn nhất khi scale hệ thống này là **Chi phí gọi API LLM ở bước trích xuất thực thể đồ thị** và **Entity Resolution (Trùng thực thể)**.
* **Đánh đổi:** Khi xử lý hàng nghìn trang văn bản pháp lý bổ sung, việc bắt LLM đọc từng câu để sinh bộ ba (triple) cực kỳ tốn kém và dễ tạo ra các quan hệ rác (ví dụ: "đất nông nghiệp" và "đất trồng lúa" bị coi là hai thực thể hoàn toàn độc lập, làm đứt gãy đồ thị). Để giải quyết, chúng tôi áp dụng đánh đổi: Sử dụng một bộ **Ontology định nghĩa trước (Pre-defined Ontology)** gồm các thực thể chính như `Loại_đất`, `Cơ_quan_thẩm_quyền`, `Hồ_sơ_pháp_lý`, `Mốc_thời_gian` kết hợp với thuật toán so khớp thực thể dựa trên từ điển luật pháp (Deterministic Entity Resolution). LLM chỉ được dùng để phân loại mối quan hệ tinh chỉnh. Việc này làm giảm 80% chi phí token LLM và tăng độ sạch của đồ thị lên gấp đôi.

### Câu hỏi 4: Failure Semantics & Data Quality Gate
* **Quyết định:** Thiết lập một **Quality Gate nghiêm ngặt** ở cả hai đầu: Input và Output.
* **Đánh đổi:**
  * *Input Gate:* Sử dụng Pandera hoặc Pydantic để validate cấu trúc metadata trích xuất từ văn bản luật (bắt buộc phải có `chương`, `điều`, `khoản`, `nguồn_văn_bản`, `ngày_hiệu_lực`). Nếu một điều luật thiếu ngày hiệu lực, nó lập tức bị đẩy vào hàng đợi cách ly (Quarantine DLQ) để chuyên gia luật kiểm tra lại, không được phép đưa vào database để tránh tư vấn luật hết hiệu lực cho người dân.
  * *Output Gate:* Để chống ảo giác, hệ thống cài đặt kiểm tra trích dẫn bắt buộc (Citation Grounding). Câu trả lời của LLM phải được đối chiếu lại với các nút và cạnh thực tế đã đi qua trên Knowledge Graph. Nếu LLM đưa ra thông tin không thể ánh xạ ngược lại các tài liệu nguồn cụ thể trong context, câu trả lời sẽ bị từ chối và trả về mã lỗi hệ thống.

### Câu hỏi 5: Bối cảnh dữ liệu Việt Nam (Vietnamese Context & PDPL Compliance)
* **Quyết định:** Xử lý ngôn ngữ tiếng Việt đặc thù và tuân thủ Nghị định 13/2023/NĐ-CP về Bảo vệ dữ liệu cá nhân (PDPL).
* **Đánh đổi:**
  * Tiếng Việt có cấu trúc câu phức tạp, nhiều từ ghép và từ đồng nghĩa hành chính (như "GCNQSDĐ", "Sổ đỏ", "Sổ hồng", "Giấy chứng nhận"). Chúng tôi phải tích hợp thư viện tách từ tiếng Việt (như PyVi hoặc Underthesea) trước khi tạo embedding và trích xuất thực thể để tránh việc cắt đôi từ ghép (ví dụ cắt "đất" và "nông nghiệp" thành hai token riêng biệt làm sai lệch ý nghĩa).
  * Đối với PDPL: Người dân khi hỏi thường có xu hướng nhập cả thông tin cá nhân của họ như "Tôi là Nguyễn Văn A, có mảnh đất tại địa chỉ X, số tờ bản đồ Y...". Hệ thống data pipeline trước khi lưu vết trace người dùng vào Bronze layer (flywheel) bắt buộc phải đi qua một bước **De-identification Gate (PII Masking)** để ẩn danh hóa toàn bộ tên riêng, địa chỉ cụ thể, số định danh cá nhân nhằm đảm bảo an toàn thông tin theo pháp luật Việt Nam.

---

## 3. Phương án bị loại bỏ (Rejected Alternative)

Chúng tôi đã loại bỏ phương án **"Sử dụng mô hình Unsupervised GraphRAG tự động hoàn toàn"** (tự động đưa toàn bộ văn bản vào LLM để tự sinh thực thể và quan hệ mà không cần định nghĩa Ontology trước).
* **Lý do loại bỏ:** Mặc dù phương án này rất dễ cài đặt ban đầu (chỉ cần chạy một vài script LangChain mặc định), nó tạo ra một đồ thị cực kỳ hỗn loạn trong lĩnh vực luật pháp Việt Nam. Ví dụ, LLM có thể tạo ra các quan hệ trùng lặp như `[Đất trồng lúa] --thuộc nhóm--> [Đất nông nghiệp]` và `[Đất lúa] --là loại của--> [Đất nông nghiệp]`. Sự thiếu nhất quán này làm hỏng hoàn toàn thuật toán tìm kiếm đa bước (BFS/DFS traversal) vì đồ thị bị đứt quãng hoặc tạo ra các đường đi ảo. Trong ngành luật, một sai sót nhỏ về thẩm quyền hay loại đất sẽ dẫn đến việc tư vấn sai luật nghiêm trọng, do đó việc áp dụng một Ontology được kiểm soát chặt chẽ bởi con người (Human-in-the-loop) là bắt buộc.
