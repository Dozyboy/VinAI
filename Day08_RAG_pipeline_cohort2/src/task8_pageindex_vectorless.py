"""
Task 8 - PageIndex Vectorless RAG.

If PAGEINDEX_API_KEY is configured, this file is the integration point for the
real SDK. For an offline lab run, pageindex_search uses a local vectorless
fallback based on token coverage and document metadata. The returned shape is
the same as PageIndex retrieval, including source="pageindex".
"""

from __future__ import annotations

import json
import os
import re
from pathlib import Path

from dotenv import load_dotenv


try:
    from .task4_chunking_indexing import INDEX_DIR, chunk_documents, load_documents
except ImportError:  # pragma: no cover - allows running as a script
    from task4_chunking_indexing import INDEX_DIR, chunk_documents, load_documents


load_dotenv()

PAGEINDEX_API_KEY = os.getenv("PAGEINDEX_API_KEY", "")
STANDARDIZED_DIR = Path(__file__).parent.parent / "data" / "standardized"
PAGEINDEX_MANIFEST_PATH = INDEX_DIR / "pageindex_local_manifest.json"


def upload_documents():
    """
    Upload documents to PageIndex when configured; otherwise write a local
    manifest that documents what would be uploaded.
    """
    documents = load_documents()

    if PAGEINDEX_API_KEY and os.getenv("USE_REAL_PAGEINDEX", "").lower() in {"1", "true", "yes"}:
        try:
            from pageindex import PageIndex  # type: ignore
        except Exception as exc:  # pragma: no cover - depends on external SDK
            raise RuntimeError("PageIndex SDK is not available") from exc

        client = PageIndex(api_key=PAGEINDEX_API_KEY)
        uploaded = []
        for doc in documents:
            result = client.upload(content=doc["content"], metadata=doc["metadata"])
            uploaded.append({"metadata": doc["metadata"], "result": str(result)})
        return uploaded

    INDEX_DIR.mkdir(parents=True, exist_ok=True)
    manifest = [
        {
            "source": doc["metadata"].get("source"),
            "path": doc["metadata"].get("path"),
            "type": doc["metadata"].get("type"),
            "characters": len(doc["content"]),
        }
        for doc in documents
    ]
    PAGEINDEX_MANIFEST_PATH.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    return manifest


def pageindex_search(query: str, top_k: int = 5) -> list[dict]:
    """
    Vectorless retrieval. Uses real PageIndex only when explicitly enabled;
    otherwise falls back to local structure-aware token coverage.
    """
    if top_k <= 0 or not query.strip():
        return []

    if PAGEINDEX_API_KEY and os.getenv("USE_REAL_PAGEINDEX", "").lower() in {"1", "true", "yes"}:
        try:
            from pageindex import PageIndex  # type: ignore

            client = PageIndex(api_key=PAGEINDEX_API_KEY)
            raw_results = client.query(query=query, top_k=top_k)
            return [
                {
                    "content": getattr(result, "text", ""),
                    "score": float(getattr(result, "score", 0.0)),
                    "metadata": getattr(result, "metadata", {}) or {},
                    "source": "pageindex",
                }
                for result in raw_results
            ]
        except Exception:
            # Keep the fallback available for demos if the hosted service is not
            # reachable from the classroom network.
            pass

    query_tokens = _tokenize(query)
    chunks = chunk_documents(load_documents())
    scored: list[dict] = []

    for chunk in chunks:
        content = chunk.get("content", "")
        content_tokens = _tokenize(content)
        score = _coverage_score(query_tokens, content_tokens)
        if score <= 0:
            continue

        metadata = {**chunk.get("metadata", {}), "pageindex_mode": "local_vectorless"}
        scored.append(
            {
                "content": content,
                "score": float(score),
                "metadata": metadata,
                "source": "pageindex",
            }
        )

    scored.sort(key=lambda item: item["score"], reverse=True)
    return scored[:top_k]


def _tokenize(text: str) -> list[str]:
    return re.findall(r"(?u)\b\w+\b", text.lower())


def _coverage_score(query_tokens: list[str], content_tokens: list[str]) -> float:
    if not query_tokens or not content_tokens:
        return 0.0

    query_set = set(query_tokens)
    content_set = set(content_tokens)
    coverage = len(query_set & content_set) / len(query_set)

    # Reward chunks that contain repeated exact terms without letting long pages
    # dominate solely because they are long.
    frequency_hits = sum(1 for token in content_tokens if token in query_set)
    density = min(1.0, frequency_hits / max(8, len(query_tokens) * 2))
    return 0.8 * coverage + 0.2 * density


if __name__ == "__main__":
    print("Preparing PageIndex/local manifest...")
    upload_documents()
    results = pageindex_search("hinh phat su dung ma tuy", top_k=3)
    for r in results:
        print(f"[{r['score']:.3f}] {r['content'][:100]}...")
