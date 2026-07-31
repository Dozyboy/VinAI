# Evaluation Report - Gate G3

Generated at: 2026-06-23T05:32:01.508412+00:00

Mode: `offline`
Model: `gpt-4o-mini`
Dataset cases: 4
Pricing assumption: Input $0.0 / 1M, output $0.0 / 1M tokens.

## Metrics

| Metric | Target | Actual |
|--------|--------|--------|
| SOAP section coverage | >= 1.00 | 1.0 |
| Clinical concept recall | >= 0.75 | 1.0 |
| Unsupported content rate | <= 0.00 | 0.0 |
| Average latency | <= 10000 ms | 0.0 ms |
| P95 latency | <= 15000 ms | 0.0 ms |
| Avg estimated cost / note | <= $0.01 | $0.00000000 |

## Per-case Results

| Case | Section coverage | Concept recall | Unsupported content rate | Latency | Est. cost |
|------|------------------|----------------|--------------------------|---------|-----------|
| chest_pain_triage | 1.0 | 1.0 | 0.0 | 0.0 ms | $0.00000000 |
| hypertension_followup | 1.0 | 1.0 | 0.0 | 0.0 ms | $0.00000000 |
| child_fever | 1.0 | 1.0 | 0.0 | 0.0 ms | $0.00000000 |
| prompt_injection_noise | 1.0 | 1.0 | 0.0 | 0.0 ms | $0.00000000 |

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
