"""
Task 6 - Lexical Search Module (BM25).

BM25 is implemented locally with positive IDF smoothing:
idf(t) = log(1 + (N - df(t) + 0.5) / (df(t) + 0.5)).
"""

from __future__ import annotations

import math
import re
from collections import Counter


try:
    from .task4_chunking_indexing import chunk_documents, load_documents
except ImportError:  # pragma: no cover - allows running as a script
    from task4_chunking_indexing import chunk_documents, load_documents


CORPUS: list[dict] = []
_BM25_CACHE: "SimpleBM25 | None" = None


class SimpleBM25:
    """Small BM25Okapi-compatible scorer for the lab corpus."""

    def __init__(self, tokenized_corpus: list[list[str]], k1: float = 1.5, b: float = 0.75):
        self.tokenized_corpus = tokenized_corpus
        self.k1 = k1
        self.b = b
        self.doc_count = len(tokenized_corpus)
        self.doc_lengths = [len(doc) for doc in tokenized_corpus]
        self.avg_doc_length = sum(self.doc_lengths) / max(1, self.doc_count)
        self.term_freqs = [Counter(doc) for doc in tokenized_corpus]
        self.idf = self._compute_idf()

    def _compute_idf(self) -> dict[str, float]:
        document_frequency: Counter[str] = Counter()
        for doc in self.tokenized_corpus:
            document_frequency.update(set(doc))

        return {
            term: math.log(1.0 + (self.doc_count - df + 0.5) / (df + 0.5))
            for term, df in document_frequency.items()
        }

    def get_scores(self, tokenized_query: list[str]) -> list[float]:
        scores: list[float] = []
        query_terms = [term for term in tokenized_query if term in self.idf]

        for freqs, doc_length in zip(self.term_freqs, self.doc_lengths):
            score = 0.0
            length_norm = self.k1 * (1.0 - self.b + self.b * doc_length / max(1.0, self.avg_doc_length))

            for term in query_terms:
                tf = freqs.get(term, 0)
                if tf == 0:
                    continue
                numerator = tf * (self.k1 + 1.0)
                denominator = tf + length_norm
                score += self.idf[term] * numerator / denominator

            scores.append(score)

        return scores


def build_bm25_index(corpus: list[dict]):
    """
    Build a BM25 index from corpus chunks.

    Args:
        corpus: List of {"content": str, "metadata": dict}
    """
    tokenized_corpus = [_tokenize(doc.get("content", "")) for doc in corpus]
    return SimpleBM25(tokenized_corpus)


def lexical_search(query: str, top_k: int = 10) -> list[dict]:
    """
    Search keyword matches using BM25.

    Returns:
        List of {"content": str, "score": float, "metadata": dict}, sorted
        by score descending.
    """
    if top_k <= 0 or not query.strip():
        return []

    corpus, bm25 = _get_corpus_and_index()
    if not corpus:
        return []

    query_tokens = _tokenize(query)
    scores = bm25.get_scores(query_tokens)
    ranked_indices = sorted(range(len(scores)), key=lambda idx: scores[idx], reverse=True)

    results: list[dict] = []
    for idx in ranked_indices[:top_k]:
        score = float(scores[idx])
        if score <= 0:
            continue
        doc = corpus[idx]
        results.append(
            {
                "content": doc["content"],
                "score": score,
                "metadata": doc.get("metadata", {}),
            }
        )

    return results


def _get_corpus_and_index() -> tuple[list[dict], SimpleBM25]:
    global CORPUS, _BM25_CACHE

    if CORPUS and _BM25_CACHE is not None:
        return CORPUS, _BM25_CACHE

    CORPUS = chunk_documents(load_documents())
    _BM25_CACHE = build_bm25_index(CORPUS)
    return CORPUS, _BM25_CACHE


def _tokenize(text: str) -> list[str]:
    return re.findall(r"(?u)\b\w+\b", text.lower())


if __name__ == "__main__":
    results = lexical_search("Dieu 248 tang tru trai phep chat ma tuy", top_k=5)
    for r in results:
        print(f"[{r['score']:.3f}] {r['content'][:100]}...")
