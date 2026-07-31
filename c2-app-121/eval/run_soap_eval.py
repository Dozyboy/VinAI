from __future__ import annotations

import argparse
import json
import os
import statistics
import sys
import time
import unicodedata
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.config import get_settings  # noqa: E402
from src.core.guardrails import missing_soap_sections  # noqa: E402

DATASET_PATH = ROOT / "eval" / "datasets" / "soap_eval_cases.json"
JSON_OUTPUT_PATH = ROOT / "eval" / "results" / "soap_eval_latest.json"
REPORT_OUTPUT_PATH = ROOT / "eval" / "results" / "report.md"


def normalize(text: str) -> str:
    normalized = unicodedata.normalize("NFD", text or "")
    without_marks = "".join(
        char for char in normalized if unicodedata.category(char) != "Mn"
    )
    return without_marks.lower()


def estimated_tokens(text: str) -> int:
    return max(1, round(len(text or "") / 4))


def offline_soap_note(case: dict) -> str:
    concepts = ", ".join(case.get("must_include", [])) or "Chua ghi nhan"
    return f"""# S - Subjective
- {concepts}

# O - Objective
- Chua ghi nhan them thong tin khach quan ngoai transcript.

# A - Assessment
- Tom tat dua tren thong tin transcript, khong them chan doan moi.

# P - Plan
- Theo ke hoach bac si da noi trong transcript; can clinician review.
"""


def percentile(values: list[float], pct: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    index = (len(ordered) - 1) * pct / 100
    lower = int(index)
    upper = min(lower + 1, len(ordered) - 1)
    weight = index - lower
    return ordered[lower] * (1 - weight) + ordered[upper] * weight


def score_case(case: dict, output: str, latency_ms: float, price_in: float, price_out: float) -> dict:
    normalized_output = normalize(output)
    must_include = case.get("must_include", [])
    must_not_include = case.get("must_not_include", [])

    included = [
        concept for concept in must_include if normalize(concept) in normalized_output
    ]
    unsupported_hits = [
        concept for concept in must_not_include if normalize(concept) in normalized_output
    ]

    input_tokens = estimated_tokens(case.get("transcript", "")) + 450
    output_tokens = estimated_tokens(output)
    estimated_cost = (input_tokens * price_in + output_tokens * price_out) / 1_000_000
    missing_sections = missing_soap_sections(output)

    return {
        "id": case["id"],
        "latency_ms": round(latency_ms, 2),
        "section_coverage": round((4 - len(missing_sections)) / 4, 3),
        "missing_sections": missing_sections,
        "concept_recall": round(len(included) / max(1, len(must_include)), 3),
        "unsupported_content_rate": round(
            len(unsupported_hits) / max(1, len(must_not_include)), 3
        ),
        "unsupported_hits": unsupported_hits,
        "estimated_input_tokens": input_tokens,
        "estimated_output_tokens": output_tokens,
        "estimated_cost_usd": round(estimated_cost, 8),
    }


def run_case(case: dict, live: bool) -> tuple[str, float]:
    start = time.perf_counter()
    if live:
        from src.agents.tools.clinical import convert_to_soap_note

        output = convert_to_soap_note(case["transcript"])
    else:
        output = offline_soap_note(case)
    latency_ms = (time.perf_counter() - start) * 1000
    return output, latency_ms


def summarize(case_results: list[dict]) -> dict:
    latencies = [item["latency_ms"] for item in case_results]
    costs = [item["estimated_cost_usd"] for item in case_results]
    return {
        "avg_section_coverage": round(statistics.mean(item["section_coverage"] for item in case_results), 3),
        "avg_concept_recall": round(statistics.mean(item["concept_recall"] for item in case_results), 3),
        "avg_unsupported_content_rate": round(statistics.mean(item["unsupported_content_rate"] for item in case_results), 3),
        "avg_latency_ms": round(statistics.mean(latencies), 2),
        "p95_latency_ms": round(percentile(latencies, 95), 2),
        "avg_estimated_cost_usd": round(statistics.mean(costs), 8),
        "total_estimated_cost_usd": round(sum(costs), 8),
    }


def render_report(payload: dict) -> str:
    summary = payload["summary"]
    price_note = (
        f"Input ${payload['price_per_1m_input_tokens']} / 1M, "
        f"output ${payload['price_per_1m_output_tokens']} / 1M tokens."
    )
    rows = [
        ("SOAP section coverage", ">= 1.00", summary["avg_section_coverage"]),
        ("Clinical concept recall", ">= 0.75", summary["avg_concept_recall"]),
        ("Unsupported content rate", "<= 0.00", summary["avg_unsupported_content_rate"]),
        ("Average latency", "<= 10000 ms", f"{summary['avg_latency_ms']} ms"),
        ("P95 latency", "<= 15000 ms", f"{summary['p95_latency_ms']} ms"),
        ("Avg estimated cost / note", "<= $0.01", f"${summary['avg_estimated_cost_usd']:.8f}"),
    ]
    case_rows = [
        (
            item["id"],
            item["section_coverage"],
            item["concept_recall"],
            item["unsupported_content_rate"],
            f"{item['latency_ms']} ms",
            f"${item['estimated_cost_usd']:.8f}",
        )
        for item in payload["cases"]
    ]

    metrics_md = "\n".join(
        f"| {metric} | {target} | {actual} |" for metric, target, actual in rows
    )
    cases_md = "\n".join(
        f"| {case_id} | {section} | {recall} | {unsupported} | {latency} | {cost} |"
        for case_id, section, recall, unsupported, latency, cost in case_rows
    )

    return f"""# Evaluation Report - Gate G3

Generated at: {payload['generated_at']}

Mode: `{payload['mode']}`
Model: `{payload['model_name']}`
Dataset cases: {payload['dataset_size']}
Pricing assumption: {price_note}

## Metrics

| Metric | Target | Actual |
|--------|--------|--------|
{metrics_md}

## Per-case Results

| Case | Section coverage | Concept recall | Unsupported content rate | Latency | Est. cost |
|------|------------------|----------------|--------------------------|---------|-----------|
{cases_md}

## How to Reproduce

Offline smoke baseline:

```bash
python eval/run_soap_eval.py
```

Live LLM evaluation:

```bash
python eval/run_soap_eval.py --live --input-price-per-1m <PRICE> --output-price-per-1m <PRICE>
```

Notes:
- `section_coverage` checks required SOAP sections S/O/A/P.
- `concept_recall` checks whether expected clinical concepts appear in the SOAP output.
- `unsupported_content_rate` checks whether explicitly forbidden/hallucinated concepts appear.
- Cost is an estimate from text length unless provider token usage is added later.
"""


def render_combined_report(offline: dict, live: dict) -> str:
    off_sum = offline["summary"]
    live_sum = live["summary"]

    rows = [
        ("SOAP section coverage", ">= 1.00", off_sum["avg_section_coverage"], live_sum["avg_section_coverage"]),
        ("Clinical concept recall", ">= 0.75", off_sum["avg_concept_recall"], live_sum["avg_concept_recall"]),
        ("Unsupported content rate", "<= 0.00", off_sum["avg_unsupported_content_rate"], live_sum["avg_unsupported_content_rate"]),
        ("Average latency", "<= 10000 ms", f"{off_sum['avg_latency_ms']} ms", f"{live_sum['avg_latency_ms']} ms"),
        ("P95 latency", "<= 15000 ms", f"{off_sum['p95_latency_ms']} ms", f"{live_sum['p95_latency_ms']} ms"),
        ("Avg estimated cost / note", "<= $0.01", f"${off_sum['avg_estimated_cost_usd']:.8f}", f"${live_sum['avg_estimated_cost_usd']:.8f}"),
    ]

    metrics_md = "\n".join(
        f"| {metric} | {target} | {off_val} | {live_val} |"
        for metric, target, off_val, live_val in rows
    )

    # Per-case comparison
    case_rows = []
    live_cases = {c["id"]: c for c in live["cases"]}
    for off_case in offline["cases"]:
        cid = off_case["id"]
        lc = live_cases.get(cid, {})
        case_rows.append(
            f"| {cid} | {off_case['section_coverage']} / {lc.get('section_coverage', '-')} | "
            f"{off_case['concept_recall']} / {lc.get('concept_recall', '-')} | "
            f"{off_case['unsupported_content_rate']} / {lc.get('unsupported_content_rate', '-')} | "
            f"{off_case['latency_ms']} ms / {lc.get('latency_ms', '-')} ms | "
            f"${off_case['estimated_cost_usd']:.6f} / ${lc.get('estimated_cost_usd', 0.0):.6f} |"
        )
    cases_md = "\n".join(case_rows)

    return f"""# Evaluation Report - Gate G3 (Combined Baselines)

Generated at: {live['generated_at']}

This report compares the **Offline Smoke Baseline** (mock rules-based generation) and the **Live LLM Baseline** (using `{live['model_name']}`).

## Metrics Comparison

| Metric | Target | Offline Baseline | Live LLM Baseline ({live['model_name']}) |
|--------|--------|------------------|-----------------------------------------|
{metrics_md}

## Per-case Results (Offline / Live)

| Case | Section coverage | Concept recall | Unsupported content rate | Latency | Est. cost |
|------|------------------|----------------|--------------------------|---------|-----------|
{cases_md}

## How to Reproduce

Offline smoke baseline:

```bash
python eval/run_soap_eval.py
```

Live LLM evaluation:

```bash
python eval/run_soap_eval.py --live --input-price-per-1m <PRICE> --output-price-per-1m <PRICE>
```
"""


def main() -> None:
    parser = argparse.ArgumentParser(description="Run SOAP note evaluation for Gate G3.")
    parser.add_argument("--live", action="store_true", help="Call the configured LLM.")
    parser.add_argument("--dataset", type=Path, default=DATASET_PATH)
    parser.add_argument("--json-output", type=Path, default=JSON_OUTPUT_PATH)
    parser.add_argument("--report-output", type=Path, default=REPORT_OUTPUT_PATH)
    parser.add_argument(
        "--input-price-per-1m",
        type=float,
        default=float(os.getenv("EVAL_INPUT_PRICE_PER_1M", "0")),
    )
    parser.add_argument(
        "--output-price-per-1m",
        type=float,
        default=float(os.getenv("EVAL_OUTPUT_PRICE_PER_1M", "0")),
    )
    args = parser.parse_args()

    settings = get_settings()
    cases = json.loads(args.dataset.read_text(encoding="utf-8"))

    results = []
    for case in cases:
        output, latency_ms = run_case(case, args.live)
        results.append(
            score_case(
                case,
                output,
                latency_ms,
                args.input_price_per_1m,
                args.output_price_per_1m,
            )
        )

    payload = {
        "generated_at": datetime.now(UTC).isoformat(),
        "mode": "live" if args.live else "offline",
        "model_name": settings.model_name if settings.llm_provider == "openai" else settings.gemini_model_name,
        "dataset_size": len(cases),
        "price_per_1m_input_tokens": args.input_price_per_1m,
        "price_per_1m_output_tokens": args.output_price_per_1m,
        "summary": summarize(results),
        "cases": results,
    }

    args.json_output.parent.mkdir(parents=True, exist_ok=True)
    args.report_output.parent.mkdir(parents=True, exist_ok=True)
    
    # Write latest run JSON
    args.json_output.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    
    # Save mode-specific JSON to allow comparison
    mode_filename = "soap_eval_live.json" if args.live else "soap_eval_offline.json"
    mode_json_path = args.json_output.parent / mode_filename
    mode_json_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    # Try to generate combined report if both exist
    offline_json_path = args.json_output.parent / "soap_eval_offline.json"
    live_json_path = args.json_output.parent / "soap_eval_live.json"

    if offline_json_path.exists() and live_json_path.exists():
        try:
            offline_payload = json.loads(offline_json_path.read_text(encoding="utf-8"))
            live_payload = json.loads(live_json_path.read_text(encoding="utf-8"))
            combined_report = render_combined_report(offline_payload, live_payload)
            args.report_output.write_text(combined_report, encoding="utf-8")
            print("Successfully generated combined offline vs live comparison report.")
        except Exception as e:
            print(f"Error generating combined report, falling back to single: {e}")
            args.report_output.write_text(render_report(payload), encoding="utf-8")
    else:
        args.report_output.write_text(render_report(payload), encoding="utf-8")

    print(json.dumps(payload["summary"], indent=2))


if __name__ == "__main__":
    main()
