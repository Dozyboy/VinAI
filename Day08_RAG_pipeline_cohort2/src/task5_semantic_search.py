"""
Task 5 - Semantic Search Module.

Dense retrieval is implemented against the local TF-IDF + SVD vector index from
Task 4. This keeps the same semantic-search contract while staying offline.
"""

from __future__ import annotations


try:
    from .task4_chunking_indexing import get_or_build_index
except ImportError:  # pragma: no cover - allows running as a script
    from task4_chunking_indexing import get_or_build_index


def semantic_search(query: str, top_k: int = 10) -> list[dict]:
    """
    Search with cosine similarity over the local dense vector index.

    Returns:
        List of {"content": str, "score": float, "metadata": dict}, sorted
        by score descending.
    """
    if top_k <= 0 or not query.strip():
        return []

    index = get_or_build_index()
    chunks = index.get("chunks", [])
    matrix = index.get("matrix")
    vectorizer = index.get("vectorizer")
    svd = index.get("svd")

    if not chunks or matrix is None or vectorizer is None:
        return []

    from sklearn.preprocessing import normalize

    query_matrix = vectorizer.transform([query])
    if svd is not None:
        query_vector = svd.transform(query_matrix)
    else:
        query_vector = query_matrix.toarray()

    query_vector = normalize(query_vector)
    scores = (matrix @ query_vector.T).ravel()
    ranked_indices = scores.argsort()[::-1][:top_k]

    results: list[dict] = []
    for idx in ranked_indices:
        score = float(scores[idx])
        chunk = chunks[int(idx)]
        results.append(
            {
                "content": chunk["content"],
                "score": score,
                "metadata": chunk.get("metadata", {}),
            }
        )

    return results


if __name__ == "__main__":
    results = semantic_search("hinh phat cho toi tang tru ma tuy", top_k=5)
    for r in results:
        print(f"[{r['score']:.3f}] {r['content'][:100]}...")
