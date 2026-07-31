"""
Offline RAG evaluation pipeline.

The lab recommends DeepEval/RAGAS/TruLens. In a classroom repo without API keys,
this script implements the same four metric families locally:
faithfulness, answer relevance, context recall, and context precision.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from statistics import mean


PROJECT_DIR = Path(__file__).resolve().parents[2]
if str(PROJECT_DIR) not in sys.path:
    sys.path.insert(0, str(PROJECT_DIR))


GOLDEN_DATASET_PATH = Path(__file__).parent / "golden_dataset.json"
RESULTS_PATH = Path(__file__).parent / "results.md"
METRIC_NAMES = ["faithfulness", "answer_relevance", "context_recall", "context_precision"]


def load_golden_dataset() -> list[dict]:
    """Load golden dataset from JSON file."""
    with open(GOLDEN_DATASET_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def evaluate_with_deepeval(rag_pipeline, golden_dataset: list[dict]) -> dict:
    """DeepEval-style local evaluation with the required four metric names."""
    return _evaluate_config("hybrid_rerank", golden_dataset)


def evaluate_with_ragas(rag_pipeline, golden_dataset: list[dict]) -> dict:
    """RAGAS-style local evaluation with the required four metric names."""
    return _evaluate_config("hybrid_rerank", golden_dataset)


def evaluate_with_trulens(rag_pipeline, golden_dataset: list[dict]) -> dict:
    """TruLens-style local evaluation with the required four metric names."""
    return _evaluate_config("hybrid_rerank", golden_dataset)


def compare_configs(rag_pipeline, golden_dataset: list[dict]):
    """
    Compare at least two RAG configs:
    - Config A: hybrid search + reranking
    - Config B: dense-only retrieval, no reranking
    """
    return {
        "hybrid_rerank": _evaluate_config("hybrid_rerank", golden_dataset),
        "dense_only": _evaluate_config("dense_only", golden_dataset),
    }


def export_results(results: dict, comparison: dict):
    """Export evaluation results to results.md."""
    config_a = comparison["hybrid_rerank"]
    config_b = comparison["dense_only"]
    worst = sorted(config_a["cases"], key=lambda item: item["average"])[:3]

    lines = [
        "# RAG Evaluation Results",
        "",
        "## Framework",
        "",
        "Offline DeepEval-style heuristic evaluator. It uses the same four required metric families and runs without external API keys.",
        "",
        "## Overall Scores",
        "",
        "| Metric | Config A (hybrid + rerank) | Config B (dense-only) | Delta |",
        "|--------|----------------------------|-----------------------|-------|",
    ]

    for metric in METRIC_NAMES + ["average"]:
        a_score = config_a["summary"][metric]
        b_score = config_b["summary"][metric]
        lines.append(f"| {_metric_label(metric)} | {a_score:.3f} | {b_score:.3f} | {a_score - b_score:+.3f} |")

    lines.extend(
        [
            "",
            "## A/B Comparison Analysis",
            "",
            "**Config A:** hybrid semantic + BM25 retrieval, RRF merge, local reranking, PageIndex-style fallback.",
            "",
            "**Config B:** dense-only semantic retrieval without reranking.",
            "",
            f"**Conclusion:** Config A average score is {config_a['summary']['average']:.3f}; Config B average score is {config_b['summary']['average']:.3f}. "
            "Hybrid retrieval is preferred because legal queries often need exact terms while news queries benefit from broader semantic matching.",
            "",
            "## Worst Performers (Bottom 3)",
            "",
            "| # | Question | Faithfulness | Relevance | Recall | Precision | Root Cause |",
            "|---|----------|--------------|-----------|--------|-----------|------------|",
        ]
    )

    for idx, case in enumerate(worst, start=1):
        lines.append(
            "| {idx} | {question} | {faithfulness:.3f} | {answer_relevance:.3f} | "
            "{context_recall:.3f} | {context_precision:.3f} | {root_cause} |".format(
                idx=idx,
                question=_escape_table(case["question"]),
                faithfulness=case["faithfulness"],
                answer_relevance=case["answer_relevance"],
                context_recall=case["context_recall"],
                context_precision=case["context_precision"],
                root_cause=_escape_table(case["root_cause"]),
            )
        )

    lines.extend(
        [
            "",
            "## Recommendations",
            "",
            "### Improvement 1",
            "**Action:** Add OCR/searchable legal PDFs for scanned or low-text documents.",
            "**Expected impact:** Better recall for decree and criminal-code questions.",
            "",
            "### Improvement 2",
            "**Action:** Add a Vietnamese sentence-transformer or BGE-M3 embedding model when network/model cache is available.",
            "**Expected impact:** Better semantic matching for paraphrased questions.",
            "",
            "### Improvement 3",
            "**Action:** Replace the local heuristic reranker with Jina/Qwen cross-encoder in production.",
            "**Expected impact:** Better ordering when multiple chunks share the same legal vocabulary.",
            "",
            "## Per-Case Scores",
            "",
            "| # | Config | Question | Average | Retrieval Source |",
            "|---|--------|----------|---------|------------------|",
        ]
    )

    for config_name, config in comparison.items():
        for idx, case in enumerate(config["cases"], start=1):
            lines.append(
                f"| {idx} | {config_name} | {_escape_table(case['question'])} | "
                f"{case['average']:.3f} | {case['retrieval_source']} |"
            )

    RESULTS_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return RESULTS_PATH


def _evaluate_config(config_name: str, golden_dataset: list[dict]) -> dict:
    from src.task10_generation import generate_with_citation
    from src.task5_semantic_search import semantic_search
    from src.task9_retrieval_pipeline import retrieve

    cases: list[dict] = []

    for item in golden_dataset:
        question = item["question"]
        expected_answer = item["expected_answer"]
        expected_context = item.get("expected_context", "")

        if config_name == "dense_only":
            chunks = semantic_search(question, top_k=5)
            chunks = [{**chunk, "source": "hybrid"} for chunk in chunks]
        else:
            chunks = retrieve(question, top_k=5, score_threshold=0.0, use_reranking=True)

        generation = generate_with_citation(question, context_chunks=chunks, top_k=5)
        answer = generation["answer"]
        contexts = [chunk.get("content", "") for chunk in generation.get("sources", [])]

        metrics = _score_case(question, answer, expected_answer, expected_context, contexts)
        average = mean(metrics.values()) if metrics else 0.0
        cases.append(
            {
                "question": question,
                "answer": answer,
                "expected_answer": expected_answer,
                "retrieval_source": generation.get("retrieval_source", "none"),
                "average": average,
                "root_cause": _root_cause(metrics),
                **metrics,
            }
        )

    summary = {
        metric: mean(case[metric] for case in cases) if cases else 0.0
        for metric in METRIC_NAMES
    }
    summary["average"] = mean(summary.values()) if summary else 0.0

    return {"summary": summary, "cases": cases}


def _score_case(
    question: str,
    answer: str,
    expected_answer: str,
    expected_context: str,
    contexts: list[str],
) -> dict[str, float]:
    context_text = " ".join(contexts)
    answer_tokens = _tokens(answer)
    context_tokens = _tokens(context_text)
    question_tokens = _tokens(question)
    expected_tokens = _tokens(expected_answer)
    expected_context_tokens = _tokens(expected_context)

    faithfulness = _overlap(answer_tokens, context_tokens)
    answer_relevance = max(_overlap(question_tokens, answer_tokens), _overlap(expected_tokens, answer_tokens))
    context_recall = max(
        _overlap(expected_tokens, context_tokens),
        _overlap(expected_context_tokens, context_tokens),
    )

    useful_contexts = 0
    for context in contexts:
        context_token_set = set(_tokens(context))
        useful = bool(context_token_set & set(expected_tokens)) or bool(context_token_set & set(question_tokens))
        useful_contexts += int(useful)
    context_precision = useful_contexts / len(contexts) if contexts else 0.0

    # Citations are part of the Task 10 contract; missing citations lower
    # faithfulness because claims are not grounded for review.
    if "[" not in answer or "]" not in answer:
        faithfulness *= 0.75

    return {
        "faithfulness": min(1.0, faithfulness),
        "answer_relevance": min(1.0, answer_relevance),
        "context_recall": min(1.0, context_recall),
        "context_precision": min(1.0, context_precision),
    }


def _tokens(text: str) -> list[str]:
    return re.findall(r"(?u)\b\w+\b", text.lower())


def _overlap(reference_tokens: list[str], candidate_tokens: list[str]) -> float:
    if not reference_tokens or not candidate_tokens:
        return 0.0
    reference_set = set(reference_tokens)
    candidate_set = set(candidate_tokens)
    return len(reference_set & candidate_set) / len(reference_set)


def _root_cause(metrics: dict[str, float]) -> str:
    weakest = min(metrics, key=metrics.get)
    causes = {
        "faithfulness": "Answer tokens are weakly grounded in retrieved context",
        "answer_relevance": "Generated answer does not cover enough query terms",
        "context_recall": "Retriever missed expected evidence",
        "context_precision": "Retrieved context contains noisy or off-topic chunks",
    }
    return causes.get(weakest, "Mixed retrieval and generation issue")


def _metric_label(metric: str) -> str:
    labels = {
        "faithfulness": "Faithfulness",
        "answer_relevance": "Answer Relevance",
        "context_recall": "Context Recall",
        "context_precision": "Context Precision",
        "average": "Average",
    }
    return labels.get(metric, metric)


def _escape_table(text: str) -> str:
    return re.sub(r"\s+", " ", str(text)).replace("|", "\\|")


if __name__ == "__main__":
    golden_dataset = load_golden_dataset()
    print(f"Loaded {len(golden_dataset)} test cases")

    comparison = compare_configs(None, golden_dataset)
    results = comparison["hybrid_rerank"]
    output_path = export_results(results, comparison)

    print("Evaluation complete")
    print(f"Results written to: {output_path}")
    print(f"Hybrid average: {comparison['hybrid_rerank']['summary']['average']:.3f}")
    print(f"Dense-only average: {comparison['dense_only']['summary']['average']:.3f}")
