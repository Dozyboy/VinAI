"""Audit log cho mọi lần gọi MCP tool và A2A dispatch."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from lab_utils.governance.models import AuditEntry, GovernanceDecision

DEFAULT_AUDIT_PATH = Path(__file__).resolve().parents[2] / "logs" / "governance_audit.jsonl"


class AuditLogger:
    def __init__(self, log_path: Path | None = None):
        self.log_path = log_path or DEFAULT_AUDIT_PATH
        self.log_path.parent.mkdir(parents=True, exist_ok=True)

    def record(
        self,
        decision: GovernanceDecision,
        action: str,
        input_summary: str,
        trace_id: str | None = None,
        extra: dict[str, Any] | None = None,
    ) -> AuditEntry:
        entry = AuditEntry(
            timestamp=datetime.now(timezone.utc).isoformat(),
            actor_id=decision.actor_id,
            connection_type=decision.connection_type.value,
            action=action,
            resource=decision.resource,
            verdict=decision.verdict.value,
            reason=decision.reason,
            input_summary=input_summary[:500],
            trace_id=trace_id,
            metadata=extra or {},
        )
        with self.log_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(entry.__dict__, ensure_ascii=False) + "\n")
        return entry

    def read_recent(self, limit: int = 20) -> list[dict[str, Any]]:
        if not self.log_path.exists():
            return []
        lines = self.log_path.read_text(encoding="utf-8").strip().splitlines()
        return [json.loads(line) for line in lines[-limit:]]

    def summary(self) -> dict[str, int]:
        entries = self.read_recent(limit=10_000)
        counts: dict[str, int] = {"allow": 0, "deny": 0, "hitl_required": 0}
        for entry in entries:
            verdict = entry.get("verdict", "allow")
            counts[verdict] = counts.get(verdict, 0) + 1
        return counts
