"""
Task 9 - Complete Retrieval Pipeline.

Pipeline:
1. Semantic search
2. Lexical BM25 search
3. RRF merge
4. Local reranking
5. PageIndex/vectorless fallback when hybrid confidence is low
"""

from __future__ import annotations


try:
    from .task5_semantic_search import semantic_search
    from .task6_lexical_search import lexical_search
    from .task7_reranking import rerank, rerank_rrf
    from .task8_pageindex_vectorless import pageindex_search
except ImportError:  # pragma: no cover - allows running as a script
    from task5_semantic_search import semantic_search
    from task6_lexical_search import lexical_search
    from task7_reranking import rerank, rerank_rrf
    from task8_pageindex_vectorless import pageindex_search


SCORE_THRESHOLD = 0.3
DEFAULT_TOP_K = 5
RERANK_METHOD = "cross_encoder"


def retrieve(
    query: str,
    top_k: int = DEFAULT_TOP_K,
    score_threshold: float = SCORE_THRESHOLD,
    use_reranking: bool = True,
) -> list[dict]:
    """
    Retrieve top chunks using hybrid search with vectorless fallback.

    Returns:
        List of {"content": str, "score": float, "metadata": dict, "source": str}
    """
    if top_k <= 0 or not query.strip():
        return []

    dense_results = semantic_search(query, top_k=top_k * 3)
    sparse_results = lexical_search(query, top_k=top_k * 3)

    merged = rerank_rrf([dense_results, sparse_results], top_k=top_k * 3)
    merged = [_mark_source(item, "hybrid") for item in merged]

    if use_reranking and merged:
        final_results = rerank(query, merged, top_k=top_k, method=RERANK_METHOD)
        final_results = [_mark_source(item, "hybrid") for item in final_results]
    else:
        final_results = merged[:top_k]

    best_score = final_results[0]["score"] if final_results else 0.0
    if best_score < score_threshold:
        fallback = pageindex_search(query, top_k=top_k)
        if fallback:
            return fallback[:top_k]

    return final_results[:top_k]


def _mark_source(item: dict, source: str) -> dict:
    marked = {**item, "source": source}
    metadata = {**marked.get("metadata", {}), "retrieval_source": source}
    marked["metadata"] = metadata
    return marked


if __name__ == "__main__":
    test_queries = [
        "Hinh phat cho toi tang tru trai phep chat ma tuy",
        "Nghe si nao bi bat vi su dung ma tuy",
        "Luat phong chong ma tuy 2021 quy dinh gi ve cai nghien",
    ]

    for q in test_queries:
        print(f"\nQuery: {q}")
        print("-" * 60)
        results = retrieve(q, top_k=3)
        for i, r in enumerate(results, 1):
            print(f"  {i}. [{r['score']:.3f}] [{r['source']}] {r['content'][:80]}...")
