"""
Task 10 - Generation with Citation.

The default path is extractive and offline: retrieve chunks, reorder them to
reduce lost-in-the-middle, select evidence sentences, and attach citations. If
you want hosted LLM generation later, this module already formats the context
and prompt cleanly for that swap.
"""

from __future__ import annotations

import os
import re
from pathlib import Path

from dotenv import load_dotenv


try:
    from .task9_retrieval_pipeline import retrieve
except ImportError:  # pragma: no cover - allows running as a script
    from task9_retrieval_pipeline import retrieve


load_dotenv()


# top_k: five chunks usually contain enough evidence for one legal/news answer
# without making the prompt too long.
TOP_K = 5

# top_p and temperature are documented for the optional LLM path. RAG answers
# should be factual, so generation is conservative.
TOP_P = 0.9
TEMPERATURE = 0.3


SYSTEM_PROMPT = """Answer the following question comprehensively in Vietnamese.
For every statement of fact or claim, immediately insert a citation in brackets
linking to the specific source (e.g., [Luat Phong chong ma tuy 2021, 2021]).
If the information is not explicitly stated in the provided context, state
'I cannot verify this information' rather than guessing."""


def reorder_for_llm(chunks: list[dict]) -> list[dict]:
    """
    Reorder chunks to reduce lost-in-the-middle.

    Example for five chunks sorted by relevance:
    [1, 2, 3, 4, 5] -> [1, 3, 5, 4, 2]
    """
    if len(chunks) <= 2:
        return list(chunks)

    reordered: list[dict] = []
    reordered.extend(chunks[0::2])
    reordered.extend(reversed(chunks[1::2]))
    return reordered


def format_context(chunks: list[dict]) -> str:
    """Format chunks with source labels for citation-aware prompting."""
    context_parts: list[str] = []

    for i, chunk in enumerate(chunks, start=1):
        metadata = chunk.get("metadata", {})
        source = metadata.get("source") or metadata.get("path") or f"Source {i}"
        doc_type = metadata.get("type", "unknown")
        score = float(chunk.get("score", 0.0))
        context_parts.append(
            f"[Document {i} | Source: {source} | Type: {doc_type} | Score: {score:.3f}]\n"
            f"{chunk.get('content', '')}"
        )

    return "\n\n---\n\n".join(context_parts)


def generate_with_citation(
    query: str,
    context_chunks: list[dict] | None = None,
    top_k: int = TOP_K,
) -> dict:
    """
    End-to-end RAG generation with citations.

    Returns:
        {"answer": str, "sources": list[dict], "retrieval_source": str}
    """
    chunks = context_chunks if context_chunks is not None else retrieve(query, top_k=top_k)
    chunks = list(chunks or [])[:top_k]

    if not chunks:
        return {
            "answer": "I cannot verify this information from the provided context.",
            "sources": [],
            "retrieval_source": "none",
        }

    reordered = reorder_for_llm(chunks)
    context = format_context(reordered)

    if _should_use_openai():
        answer = _generate_with_openai(query, context)
    else:
        answer = _generate_extractive_answer(query, reordered)

    return {
        "answer": answer,
        "sources": reordered,
        "retrieval_source": reordered[0].get("source", "hybrid") if reordered else "none",
        "context": context,
    }


def _generate_extractive_answer(query: str, chunks: list[dict]) -> str:
    query_tokens = _tokenize(query)
    evidence: list[tuple[float, str, str]] = []

    for chunk in chunks:
        citation = _citation_for_chunk(chunk)
        for sentence in _split_sentences(chunk.get("content", "")):
            score = _sentence_score(query_tokens, sentence)
            if score > 0:
                evidence.append((score, sentence, citation))

    evidence.sort(key=lambda item: item[0], reverse=True)
    selected = evidence[:4]

    if not selected:
        best_chunk = chunks[0]
        snippet = _trim_text(best_chunk.get("content", ""), 260)
        if not snippet:
            return "I cannot verify this information from the provided context."
        return f"{snippet} {_citation_for_chunk(best_chunk)}"

    lines = ["Dua tren cac nguon da truy xuat:"]
    seen: set[str] = set()
    for _, sentence, citation in selected:
        clean_sentence = _trim_text(sentence, 320)
        normalized = clean_sentence.lower()
        if normalized in seen:
            continue
        seen.add(normalized)
        lines.append(f"- {clean_sentence} {citation}")

    if len(lines) == 1:
        return "I cannot verify this information from the provided context."

    return "\n".join(lines)


def _should_use_openai() -> bool:
    return bool(os.getenv("OPENAI_API_KEY")) and os.getenv("USE_OPENAI_GENERATION", "").lower() in {
        "1",
        "true",
        "yes",
    }


def _generate_with_openai(query: str, context: str) -> str:
    from openai import OpenAI

    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    user_message = f"Context:\n{context}\n\n---\n\nQuestion: {query}"
    response = client.chat.completions.create(
        model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_message},
        ],
        temperature=TEMPERATURE,
        top_p=TOP_P,
    )
    return response.choices[0].message.content or ""


def _citation_for_chunk(chunk: dict) -> str:
    metadata = chunk.get("metadata", {})
    source = metadata.get("title") or metadata.get("source") or metadata.get("path") or "Nguon"
    source_label = _friendly_source(source)
    year = _extract_year(source, chunk.get("content", ""))
    return f"[{source_label}, {year}]"


def _friendly_source(source: str) -> str:
    stem = Path(str(source)).stem
    clean = re.sub(r"[-_]+", " ", stem)
    clean = re.sub(r"\s+", " ", clean).strip()
    return clean[:80] or "Nguon"


def _extract_year(*texts: str) -> str:
    for text in texts:
        years = re.findall(r"\b(20\d{2}|19\d{2})\b", str(text))
        if years:
            return years[-1]
    return "n.d."


def _split_sentences(text: str) -> list[str]:
    normalized = re.sub(r"\s+", " ", text.replace("\n", " ")).strip()
    if not normalized:
        return []
    parts = re.split(r"(?<=[.!?])\s+", normalized)
    return [part.strip(" -") for part in parts if len(part.strip()) >= 40]


def _sentence_score(query_tokens: list[str], sentence: str) -> float:
    sentence_tokens = _tokenize(sentence)
    if not query_tokens or not sentence_tokens:
        return 0.0
    query_set = set(query_tokens)
    sentence_set = set(sentence_tokens)
    coverage = len(query_set & sentence_set) / len(query_set)
    density = len(query_set & sentence_set) / max(1, len(sentence_set))
    return 0.8 * coverage + 0.2 * min(1.0, density * 8)


def _tokenize(text: str) -> list[str]:
    return re.findall(r"(?u)\b\w+\b", text.lower())


def _trim_text(text: str, limit: int) -> str:
    clean = re.sub(r"\s+", " ", text).strip()
    if len(clean) <= limit:
        return clean
    truncated = clean[:limit].rsplit(" ", 1)[0].strip()
    return f"{truncated}..."


if __name__ == "__main__":
    test_queries = [
        "Hinh phat cho toi tang tru trai phep chat ma tuy theo phap luat Viet Nam?",
        "Nhung nghe si nao da bi bat vi lien quan toi ma tuy?",
        "Quy trinh cai nghien bat buoc theo Luat Phong chong ma tuy 2021?",
    ]

    for q in test_queries:
        print(f"\n{'=' * 70}")
        print(f"Q: {q}")
        print("=" * 70)
        result = generate_with_citation(q)
        print(f"\nA: {result['answer']}")
        print(f"\n[Sources: {len(result['sources'])} chunks | via {result['retrieval_source']}]")
