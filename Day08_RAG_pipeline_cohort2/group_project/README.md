# Bai Tap Nhom - RAG Evaluation Pipeline

## Muc Tieu

Nhom chon deliverable so 2: evaluation pipeline cho he thong RAG ve phap luat ma tuy va tin tuc lien quan. Pipeline co the chay local/offline, khong can OpenAI/PageIndex key.

## Kien Truc He Thong

```text
data/standardized/*.md
        |
        v
Task 4: chunking + local TF-IDF/SVD vector index
        |
        +--> Task 5: semantic search
        +--> Task 6: BM25 lexical search
                 |
                 v
Task 9: RRF merge + rerank + PageIndex-style fallback
                 |
                 v
Task 10: extractive answer with citation
                 |
                 v
group_project/evaluation/eval_pipeline.py
        |-- golden_dataset.json (15 Q&A)
        |-- A/B: hybrid+rerank vs dense-only
        |-- metrics: faithfulness, answer relevance, context recall, context precision
        `-- results.md
```

## Deliverables

- `group_project/evaluation/golden_dataset.json`: 15 Q&A pairs.
- `group_project/evaluation/eval_pipeline.py`: script evaluation local/offline.
- `group_project/evaluation/results.md`: bang diem, A/B analysis, worst performers, recommendations.

## Phan Cong

| Thanh vien | MSSV | Nhiem vu | Trang thai |
|-----------|------|----------|------------|
| Cap nhat theo nhom | Cap nhat theo nhom | Data collection va markdown conversion | Done |
| Cap nhat theo nhom | Cap nhat theo nhom | Retrieval pipeline task 4-9 | Done |
| Cap nhat theo nhom | Cap nhat theo nhom | Generation with citation task 10 | Done |
| Cap nhat theo nhom | Cap nhat theo nhom | Evaluation dataset, A/B script, report | Done |

## Huong Dan Chay

```bash
pip install -r requirements.txt
python -m pytest tests/test_individual.py -v
python group_project/evaluation/eval_pipeline.py
```

## Ghi Chu

- PageIndex va OpenAI duoc de duong tich hop that qua environment variables, nhung mac dinh la local fallback de demo khong phu thuoc network/API key.
- Truoc khi nop, nhom chi can thay cac dong `Cap nhat theo nhom` bang ten va MSSV that.
