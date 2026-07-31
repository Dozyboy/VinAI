# RAG Evaluation Results

## Framework

Offline DeepEval-style heuristic evaluator. It uses the same four required metric families and runs without external API keys.

## Overall Scores

| Metric | Config A (hybrid + rerank) | Config B (dense-only) | Delta |
|--------|----------------------------|-----------------------|-------|
| Faithfulness | 0.912 | 0.915 | -0.002 |
| Answer Relevance | 0.823 | 0.799 | +0.024 |
| Context Recall | 0.961 | 0.887 | +0.074 |
| Context Precision | 1.000 | 1.000 | +0.000 |
| Average | 0.924 | 0.900 | +0.024 |

## A/B Comparison Analysis

**Config A:** hybrid semantic + BM25 retrieval, RRF merge, local reranking, PageIndex-style fallback.

**Config B:** dense-only semantic retrieval without reranking.

**Conclusion:** Config A average score is 0.924; Config B average score is 0.900. Hybrid retrieval is preferred because legal queries often need exact terms while news queries benefit from broader semantic matching.

## Worst Performers (Bottom 3)

| # | Question | Faithfulness | Relevance | Recall | Precision | Root Cause |
|---|----------|--------------|-----------|--------|-----------|------------|
| 1 | Nghị định 105/2021/NĐ-CP có vai trò gì trong hệ thống văn bản về phòng, chống ma túy? | 0.830 | 0.600 | 0.750 | 1.000 | Generated answer does not cover enough query terms |
| 2 | Theo bài viết về showbiz, vì sao nghệ sĩ có trách nhiệm lớn hơn khi liên quan tới ma túy? | 0.913 | 0.700 | 0.909 | 1.000 | Generated answer does not cover enough query terms |
| 3 | Phòng, chống ma túy được luật giải thích như thế nào? | 0.909 | 0.636 | 1.000 | 1.000 | Generated answer does not cover enough query terms |

## Recommendations

### Improvement 1
**Action:** Add OCR/searchable legal PDFs for scanned or low-text documents.
**Expected impact:** Better recall for decree and criminal-code questions.

### Improvement 2
**Action:** Add a Vietnamese sentence-transformer or BGE-M3 embedding model when network/model cache is available.
**Expected impact:** Better semantic matching for paraphrased questions.

### Improvement 3
**Action:** Replace the local heuristic reranker with Jina/Qwen cross-encoder in production.
**Expected impact:** Better ordering when multiple chunks share the same legal vocabulary.

## Per-Case Scores

| # | Config | Question | Average | Retrieval Source |
|---|--------|----------|---------|------------------|
| 1 | hybrid_rerank | Luật Phòng, chống ma túy 2021 quy định phạm vi điều chỉnh gồm những nội dung nào? | 0.985 | hybrid |
| 2 | hybrid_rerank | Theo Luật Phòng, chống ma túy 2021, chất ma túy được hiểu là gì? | 0.936 | hybrid |
| 3 | hybrid_rerank | Chất gây nghiện được định nghĩa như thế nào trong Luật Phòng, chống ma túy 2021? | 0.938 | hybrid |
| 4 | hybrid_rerank | Chất hướng thần là gì theo Luật Phòng, chống ma túy 2021? | 0.943 | hybrid |
| 5 | hybrid_rerank | Tiền chất trong lĩnh vực phòng, chống ma túy được hiểu là gì? | 0.958 | hybrid |
| 6 | hybrid_rerank | Cây có chứa chất ma túy gồm những loại cây nào theo luật? | 0.972 | hybrid |
| 7 | hybrid_rerank | Phòng, chống ma túy được luật giải thích như thế nào? | 0.886 | hybrid |
| 8 | hybrid_rerank | Tệ nạn ma túy là gì theo Luật Phòng, chống ma túy 2021? | 0.980 | hybrid |
| 9 | hybrid_rerank | Người sử dụng trái phép chất ma túy được xác định như thế nào? | 0.920 | hybrid |
| 10 | hybrid_rerank | Xét nghiệm chất ma túy trong cơ thể là hoạt động gì? | 0.961 | hybrid |
| 11 | hybrid_rerank | Bài VnExpress 'Ma túy trong lối sống showbiz' nêu tác hại của ma túy với nghệ sĩ như thế nào? | 0.902 | hybrid |
| 12 | hybrid_rerank | Theo bài viết về showbiz, vì sao nghệ sĩ có trách nhiệm lớn hơn khi liên quan tới ma túy? | 0.881 | hybrid |
| 13 | hybrid_rerank | Bài viết về showbiz mô tả áp lực của nghệ sĩ trong môi trường giải trí ra sao? | 0.905 | hybrid |
| 14 | hybrid_rerank | Bài viết về showbiz cảnh báo điều gì đối với giới trẻ khi nhìn vào scandal ma túy của nghệ sĩ? | 0.900 | hybrid |
| 15 | hybrid_rerank | Nghị định 105/2021/NĐ-CP có vai trò gì trong hệ thống văn bản về phòng, chống ma túy? | 0.795 | hybrid |
| 1 | dense_only | Luật Phòng, chống ma túy 2021 quy định phạm vi điều chỉnh gồm những nội dung nào? | 0.979 | hybrid |
| 2 | dense_only | Theo Luật Phòng, chống ma túy 2021, chất ma túy được hiểu là gì? | 0.972 | hybrid |
| 3 | dense_only | Chất gây nghiện được định nghĩa như thế nào trong Luật Phòng, chống ma túy 2021? | 0.938 | hybrid |
| 4 | dense_only | Chất hướng thần là gì theo Luật Phòng, chống ma túy 2021? | 0.884 | hybrid |
| 5 | dense_only | Tiền chất trong lĩnh vực phòng, chống ma túy được hiểu là gì? | 0.818 | hybrid |
| 6 | dense_only | Cây có chứa chất ma túy gồm những loại cây nào theo luật? | 0.970 | hybrid |
| 7 | dense_only | Phòng, chống ma túy được luật giải thích như thế nào? | 0.825 | hybrid |
| 8 | dense_only | Tệ nạn ma túy là gì theo Luật Phòng, chống ma túy 2021? | 0.853 | hybrid |
| 9 | dense_only | Người sử dụng trái phép chất ma túy được xác định như thế nào? | 0.904 | hybrid |
| 10 | dense_only | Xét nghiệm chất ma túy trong cơ thể là hoạt động gì? | 0.956 | hybrid |
| 11 | dense_only | Bài VnExpress 'Ma túy trong lối sống showbiz' nêu tác hại của ma túy với nghệ sĩ như thế nào? | 0.907 | hybrid |
| 12 | dense_only | Theo bài viết về showbiz, vì sao nghệ sĩ có trách nhiệm lớn hơn khi liên quan tới ma túy? | 0.813 | hybrid |
| 13 | dense_only | Bài viết về showbiz mô tả áp lực của nghệ sĩ trong môi trường giải trí ra sao? | 0.869 | hybrid |
| 14 | dense_only | Bài viết về showbiz cảnh báo điều gì đối với giới trẻ khi nhìn vào scandal ma túy của nghệ sĩ? | 0.923 | hybrid |
| 15 | dense_only | Nghị định 105/2021/NĐ-CP có vai trò gì trong hệ thống văn bản về phòng, chống ma túy? | 0.892 | hybrid |
