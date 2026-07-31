"""
Task 4 - Chunking & Indexing.

This implementation uses a fully local index so the lab can run without Docker,
Weaviate Cloud, a PageIndex account, or model downloads. The design still keeps
the same RAG boundaries: load documents -> chunk -> embed -> index.
"""

from __future__ import annotations

import pickle
import re
from pathlib import Path
from typing import Any


STANDARDIZED_DIR = Path(__file__).parent.parent / "data" / "standardized"
INDEX_DIR = Path(__file__).parent.parent / "data" / "index"
INDEX_PATH = INDEX_DIR / "local_vector_index.pkl"


# Chosen strategy: recursive character chunking. Legal PDFs converted to
# markdown often have long paragraphs and noisy line breaks, so a character
# splitter is more robust than relying on clean markdown headings.
CHUNK_SIZE = 900
CHUNK_OVERLAP = 120
CHUNKING_METHOD = "recursive"

# Offline embedding choice: TF-IDF compressed with TruncatedSVD. It produces a
# dense local vector representation without API keys or downloading a model.
EMBEDDING_MODEL = "scikit-learn/tfidf-svd"
EMBEDDING_DIM = 384

# Local pickle vector store. Weaviate can replace this later, but local storage
# makes the automated tests and classroom demo reproducible.
VECTOR_STORE = "local_pickle"

_INDEX_CACHE: dict[str, Any] | None = None


def load_documents() -> list[dict]:
    """
    Read all markdown files from data/standardized/.

    Returns:
        List of {"content": str, "metadata": dict}
    """
    documents: list[dict] = []
    if not STANDARDIZED_DIR.exists():
        return documents

    for md_file in sorted(STANDARDIZED_DIR.rglob("*.md")):
        content = md_file.read_text(encoding="utf-8", errors="ignore").strip()
        if not content:
            continue

        relative_path = md_file.relative_to(STANDARDIZED_DIR).as_posix()
        doc_type = md_file.parent.name if md_file.parent != STANDARDIZED_DIR else "unknown"

        documents.append(
            {
                "content": content,
                "metadata": {
                    "source": md_file.name,
                    "path": relative_path,
                    "type": doc_type,
                    "title": _extract_title(content, md_file.stem),
                    "document_id": md_file.stem,
                },
            }
        )

    return documents


def chunk_documents(documents: list[dict]) -> list[dict]:
    """
    Chunk documents using the configured recursive character strategy.

    Returns:
        List of {"content": str, "metadata": dict}
    """
    chunks: list[dict] = []

    for doc in documents:
        text = _normalize_text(doc.get("content", ""))
        splits = _recursive_split(text)
        doc_meta = doc.get("metadata", {})

        for chunk_index, chunk_text in enumerate(splits):
            document_id = doc_meta.get("document_id", "doc")
            chunks.append(
                {
                    "content": chunk_text,
                    "metadata": {
                        **doc_meta,
                        "chunk_index": chunk_index,
                        "chunk_id": f"{document_id}:{chunk_index}",
                    },
                }
            )

    return chunks


def embed_chunks(chunks: list[dict]) -> list[dict]:
    """
    Add a dense local embedding to each chunk.

    Returns:
        The input chunks enriched with an "embedding" key.
    """
    if not chunks:
        return []

    index = _build_vector_components(chunks)
    embeddings = index["matrix"]

    embedded_chunks: list[dict] = []
    for chunk, embedding in zip(chunks, embeddings):
        enriched = {**chunk, "embedding": embedding.tolist()}
        embedded_chunks.append(enriched)

    return embedded_chunks


def index_to_vectorstore(chunks: list[dict]):
    """Persist chunks and vector components to the local vector store."""
    index = _build_vector_components(chunks)
    INDEX_DIR.mkdir(parents=True, exist_ok=True)
    with INDEX_PATH.open("wb") as f:
        pickle.dump(index, f)

    global _INDEX_CACHE
    _INDEX_CACHE = index
    return INDEX_PATH


def get_or_build_index(force_rebuild: bool = False) -> dict[str, Any]:
    """Return the local vector index, building it from markdown when needed."""
    global _INDEX_CACHE

    if _INDEX_CACHE is not None and not force_rebuild:
        return _INDEX_CACHE

    # Deliberately rebuild instead of unpickling persisted sklearn estimators.
    # Pickled sklearn objects are version-sensitive; rebuilding this small lab
    # index avoids InconsistentVersionWarning across system Python vs venv.
    docs = load_documents()
    chunks = chunk_documents(docs)
    index = _build_vector_components(chunks)

    INDEX_DIR.mkdir(parents=True, exist_ok=True)
    with INDEX_PATH.open("wb") as f:
        pickle.dump(index, f)

    _INDEX_CACHE = index
    return index


def _extract_title(content: str, fallback: str) -> str:
    for line in content.splitlines():
        clean = line.strip(" #\t")
        if clean:
            return clean[:160]
    return fallback


def _normalize_text(text: str) -> str:
    text = text.replace("\r\n", "\n").replace("\r", "\n").replace("\f", "\n")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def _recursive_split(text: str) -> list[str]:
    """Split text into overlapping character windows on natural boundaries."""
    if not text:
        return []

    chunks: list[str] = []
    start = 0
    text_length = len(text)

    while start < text_length:
        end = min(start + CHUNK_SIZE, text_length)

        if end < text_length:
            window = text[start:end]
            boundaries = [
                window.rfind("\n\n"),
                window.rfind("\n"),
                window.rfind(". "),
                window.rfind("; "),
                window.rfind(", "),
                window.rfind(" "),
            ]
            boundary = max(boundaries)
            if boundary >= int(CHUNK_SIZE * 0.45):
                end = start + boundary + 1

        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)

        if end >= text_length:
            break

        next_start = max(0, end - CHUNK_OVERLAP)
        if next_start <= start:
            next_start = end
        start = next_start

    return chunks


def _build_vector_components(chunks: list[dict]) -> dict[str, Any]:
    from sklearn.decomposition import TruncatedSVD
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.preprocessing import normalize

    texts = [chunk.get("content", "") for chunk in chunks]
    vectorizer = TfidfVectorizer(
        lowercase=True,
        max_features=12000,
        ngram_range=(1, 2),
        token_pattern=r"(?u)\b\w+\b",
    )

    if not texts:
        return {
            "chunks": [],
            "vectorizer": vectorizer,
            "svd": None,
            "matrix": [],
            "embedding_model": EMBEDDING_MODEL,
            "embedding_dim": 0,
            "chunk_size": CHUNK_SIZE,
            "chunk_overlap": CHUNK_OVERLAP,
        }

    tfidf_matrix = vectorizer.fit_transform(texts)
    max_components = min(
        EMBEDDING_DIM,
        max(1, tfidf_matrix.shape[0] - 1),
        max(1, tfidf_matrix.shape[1] - 1),
    )

    if max_components >= 2:
        svd = TruncatedSVD(n_components=max_components, random_state=42)
        dense_matrix = svd.fit_transform(tfidf_matrix)
    else:
        svd = None
        dense_matrix = tfidf_matrix.toarray()

    dense_matrix = normalize(dense_matrix)
    return {
        "chunks": chunks,
        "vectorizer": vectorizer,
        "svd": svd,
        "matrix": dense_matrix,
        "embedding_model": EMBEDDING_MODEL,
        "embedding_dim": dense_matrix.shape[1],
        "chunk_size": CHUNK_SIZE,
        "chunk_overlap": CHUNK_OVERLAP,
    }


def run_pipeline():
    """Run the full local pipeline: load -> chunk -> index."""
    print("=" * 50)
    print("Task 4: Chunking & Indexing")
    print(f"  Chunking: {CHUNKING_METHOD} (size={CHUNK_SIZE}, overlap={CHUNK_OVERLAP})")
    print(f"  Embedding: {EMBEDDING_MODEL} (target_dim={EMBEDDING_DIM})")
    print(f"  Vector Store: {VECTOR_STORE}")
    print("=" * 50)

    docs = load_documents()
    print(f"\nLoaded {len(docs)} documents")

    chunks = chunk_documents(docs)
    print(f"Created {len(chunks)} chunks")

    index_path = index_to_vectorstore(chunks)
    print(f"Indexed to vector store: {index_path}")


if __name__ == "__main__":
    run_pipeline()
