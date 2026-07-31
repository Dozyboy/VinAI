"""
Task 7 - Reranking Module.

The lab suggests hosted cross-encoders such as Jina or Qwen. To keep the repo
fully runnable offline, the default reranker below is a deterministic local
cross-encoder-style scorer: it considers query/document token overlap, phrase
matches, and the original retrieval score.
"""

from __future__ import annotations

import math
import re
from collections import defaultdict


def rerank_cross_encoder(query: str, candidates: list[dict], top_k: int = 5) -> list[dict]:
    """
    Re-score candidates with a local relevance heuristic.

    Returns:
        List of top_k candidates sorted by the new score descending.
    """
    if top_k <= 0 or not candidates:
        return []

    query_tokens = _tokenize(query)
    scored: list[dict] = []

    for rank, candidate in enumerate(candidates, start=1):
        content = candidate.get("content", "")
        content_tokens = _tokenize(content)
        overlap = _overlap_ratio(query_tokens, content_tokens)
        phrase_bonus = _phrase_bonus(query_tokens, content.lower())
        prior = _normalize_prior(candidate.get("score", 0.0), rank)

        # RAG answers should reward direct query match most, while still using
        # retrieval score as a tie-breaker from semantic/BM25 stages.
        score = min(1.0, 0.68 * overlap + 0.22 * phrase_bonus + 0.10 * prior)
        enriched = {**candidate, "score": float(score), "rerank_method": "local_cross_encoder"}
        scored.append(enriched)

    scored.sort(key=lambda item: item["score"], reverse=True)
    return scored[:top_k]


def rerank_mmr(
    query_embedding: list[float],
    candidates: list[dict],
    top_k: int = 5,
    lambda_param: float = 0.7,
) -> list[dict]:
    """
    Maximal Marginal Relevance: relevant to the query, diverse from selected docs.

    MMR = lambda * sim(query, doc) - (1 - lambda) * max(sim(doc, selected_docs))
    """
    if top_k <= 0 or not candidates:
        return []

    selected: list[int] = []
    remaining = list(range(len(candidates)))

    for _ in range(min(top_k, len(candidates))):
        best_idx: int | None = None
        best_score = float("-inf")

        for idx in remaining:
            candidate_embedding = candidates[idx].get("embedding")
            if candidate_embedding is None:
                relevance = float(candidates[idx].get("score", 0.0))
                diversity_penalty = 0.0
            else:
                relevance = _cosine_similarity(query_embedding, candidate_embedding)
                diversity_penalty = max(
                    (
                        _cosine_similarity(candidate_embedding, candidates[sel_idx].get("embedding", []))
                        for sel_idx in selected
                        if candidates[sel_idx].get("embedding") is not None
                    ),
                    default=0.0,
                )

            mmr_score = lambda_param * relevance - (1.0 - lambda_param) * diversity_penalty
            if mmr_score > best_score:
                best_score = mmr_score
                best_idx = idx

        if best_idx is None:
            break

        selected.append(best_idx)
        remaining.remove(best_idx)

    results: list[dict] = []
    for idx in selected:
        item = {**candidates[idx], "score": float(candidates[idx].get("score", 0.0)), "rerank_method": "mmr"}
        results.append(item)
    return results


def rerank_rrf(ranked_lists: list[list[dict]], top_k: int = 5, k: int = 60) -> list[dict]:
    """
    Reciprocal Rank Fusion combines multiple ranked lists.

    RRF(d) = sum(1 / (k + rank_r(d)))
    """
    if top_k <= 0:
        return []

    rrf_scores: defaultdict[str, float] = defaultdict(float)
    content_map: dict[str, dict] = {}

    for ranked_list in ranked_lists:
        for rank, item in enumerate(ranked_list, start=1):
            key = _candidate_key(item)
            rrf_scores[key] += 1.0 / (k + rank)
            existing = content_map.get(key, {})
            best_item = item if item.get("score", 0.0) >= existing.get("score", float("-inf")) else existing
            content_map[key] = best_item

    sorted_keys = sorted(rrf_scores, key=lambda key: rrf_scores[key], reverse=True)
    results: list[dict] = []
    for key in sorted_keys[:top_k]:
        item = {**content_map[key], "score": float(rrf_scores[key]), "rerank_method": "rrf"}
        results.append(item)

    return results


def rerank(
    query: str,
    candidates: list[dict],
    top_k: int = 5,
    method: str = "cross_encoder",
) -> list[dict]:
    """Unified reranking interface."""
    if method == "cross_encoder":
        return rerank_cross_encoder(query, candidates, top_k)
    if method == "rrf":
        return rerank_rrf([candidates], top_k=top_k)
    if method == "mmr":
        # Fallback to local cross-encoder unless caller supplies embeddings to
        # rerank_mmr directly.
        return rerank_cross_encoder(query, candidates, top_k)
    raise ValueError(f"Unknown rerank method: {method}")


def _candidate_key(item: dict) -> str:
    metadata = item.get("metadata", {})
    return metadata.get("chunk_id") or metadata.get("path") or item.get("content", "")


def _tokenize(text: str) -> list[str]:
    return re.findall(r"(?u)\b\w+\b", text.lower())


def _overlap_ratio(query_tokens: list[str], content_tokens: list[str]) -> float:
    if not query_tokens or not content_tokens:
        return 0.0
    content_set = set(content_tokens)
    return len(set(query_tokens) & content_set) / len(set(query_tokens))


def _phrase_bonus(query_tokens: list[str], content_lower: str) -> float:
    if not query_tokens:
        return 0.0

    query_text = " ".join(query_tokens)
    if query_text and query_text in content_lower:
        return 1.0

    bigrams = [" ".join(query_tokens[i : i + 2]) for i in range(len(query_tokens) - 1)]
    if not bigrams:
        return 0.0
    return sum(1 for bigram in bigrams if bigram in content_lower) / len(bigrams)


def _normalize_prior(score: float, rank: int) -> float:
    try:
        numeric = float(score)
    except (TypeError, ValueError):
        numeric = 0.0
    return min(1.0, max(0.0, numeric)) * 0.7 + (1.0 / max(1, rank)) * 0.3


def _cosine_similarity(a: list[float], b: list[float]) -> float:
    if not a or not b or len(a) != len(b):
        return 0.0
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(y * y for y in b))
    if norm_a == 0.0 or norm_b == 0.0:
        return 0.0
    return dot / (norm_a * norm_b)


if __name__ == "__main__":
    dummy_candidates = [
        {"content": "Dieu 248: Toi tang tru trai phep chat ma tuy", "score": 0.8, "metadata": {}},
        {"content": "Nghe si bi bat vi su dung ma tuy", "score": 0.7, "metadata": {}},
        {"content": "Hinh phat tu tu 2-7 nam cho toi tang tru", "score": 0.6, "metadata": {}},
    ]
    results = rerank("hinh phat tang tru ma tuy", dummy_candidates, top_k=2)
    for r in results:
        print(f"[{r['score']:.3f}] {r['content']}")
