# Day 13 Observability Lab Report

> **Instruction**: Fill in all sections below. This report is designed to be parsed by an automated grading assistant. Ensure all tags (e.g., `[GROUP_NAME]`) are preserved.

## 1. Team Metadata
- [GROUP_NAME]: Thieu Quang Minh
- [REPO_URL]: https://github.com/Dozyboy/2A202600871-THIEU-QUANG-MINH-DAY13
- [MEMBERS]:
  - Member A: Thieu Quang Minh | Role: Logging & PII
  - Member B: Thieu Quang Minh | Role: Tracing & Enrichment
  - Member C: Thieu Quang Minh | Role: SLO & Alerts
  - Member D: Thieu Quang Minh | Role: Load Test & Dashboard
  - Member E: Thieu Quang Minh | Role: Demo & Report

---

## 2. Group Performance (Auto-Verified)
- [VALIDATE_LOGS_FINAL_SCORE]: 100/100
- [TOTAL_TRACES_COUNT]: 30
- [PII_LEAKS_FOUND]: 0

---

## 3. Technical Evidence (Group)

### 3.1 Logging & Tracing
- [EVIDENCE_CORRELATION_ID_SCREENSHOT]: docs/screenshots/correlation_id.png
- [EVIDENCE_PII_REDACTION_SCREENSHOT]: docs/screenshots/pii_redaction.png
- [EVIDENCE_TRACE_WATERFALL_SCREENSHOT]: docs/screenshots/trace_waterfall.png
- [TRACE_WATERFALL_EXPLANATION]: The agent's `run` span contains nested observations. We can see that standard requests take around 150ms (due to LLM sleep). Under the `rag_slow` incident, the retrieval step inserts a blocking 2.5-second sleep, causing the internal latency to jump to 2650ms. Under the `cost_spike` incident, output tokens increase by 4x, causing LLM span cost to spike.

### 3.2 Dashboard & SLOs
- [DASHBOARD_6_PANELS_SCREENSHOT]: docs/screenshots/dashboard.png
- [SLO_TABLE]:
| SLI | Target | Window | Current Value |
|---|---:|---|---:|
| Latency P95 | < 3000ms | 28d | 2651ms |
| Error Rate | < 2% | 28d | 33.3% (due to tool_fail test) |
| Cost Budget | < $2.5/day | 1d | $0.1175 (total budget spent) |

### 3.3 Alerts & Runbook
- [ALERT_RULES_SCREENSHOT]: docs/screenshots/alerts.png
- [SAMPLE_RUNBOOK_LINK]: docs/alerts.md#L1-L15

---

## 4. Incident Response (Group)
- [SCENARIO_NAME]: rag_slow
- [SYMPTOMS_OBSERVED]: Internal latency measured in metrics and JSON logs rose from ~150ms to ~2650ms (P95). Client-side concurrent latencies reached up to 13.2 seconds due to blocking calls in the event loop during thread-pool execution under concurrency 5.
- [ROOT_CAUSE_PROVED_BY]: JSON logs with event `"response_sent"` showed `latency_ms=2650` for correlation IDs such as `req-06ed80a7`. The Langfuse trace waterfall also proved the `retrieve` helper span took exactly 2500ms.
- [FIX_ACTION]: Disabled the RAG slow incident via POST call to `/incidents/rag_slow/disable`. In production, we would add database read optimization, index query caches, or scale the vector store replicas.
- [PREVENTIVE_MEASURE]: Introduce a strict retrieval timeout (e.g. 1.0s) inside `retrieve` using async execution, returning cached fallback answers when the timeout is breached, to prevent blocking the event loop and breaching the latency SLO.

---

## 5. Individual Contributions & Evidence

### Thieu Quang Minh
- [TASKS_COMPLETED]: Set up environments, corrected the environment loader in main.py, executed the load tests, analyzed latency/error/cost incidents, validated logs schemas to achieve a 100/100 score, integrated Langfuse tracing, and completed the blueprint report.
- [EVIDENCE_LINK]: https://github.com/Dozyboy/2A202600871-THIEU-QUANG-MINH-DAY13/commit/084f01ed8cae7c9b906d743550ca957600e8826d

---

## 6. Bonus Items (Optional)
- [BONUS_COST_OPTIMIZATION]: (Description + Evidence)
- [BONUS_AUDIT_LOGS]: (Description + Evidence)
- [BONUS_CUSTOM_METRIC]: (Description + Evidence)
