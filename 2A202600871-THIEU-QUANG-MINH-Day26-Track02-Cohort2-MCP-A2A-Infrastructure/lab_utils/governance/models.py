"""Mô hình dữ liệu cho data governance."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class ConnectionType(str, Enum):
    MCP = "mcp"
    A2A = "a2a"


class GovernanceVerdict(str, Enum):
    ALLOW = "allow"
    DENY = "deny"
    HITL_REQUIRED = "hitl_required"


@dataclass
class GovernanceDecision:
    verdict: GovernanceVerdict
    reason: str
    actor_id: str
    connection_type: ConnectionType
    resource: str
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def allowed(self) -> bool:
        return self.verdict == GovernanceVerdict.ALLOW

    @property
    def blocked(self) -> bool:
        return self.verdict == GovernanceVerdict.DENY

    @property
    def needs_approval(self) -> bool:
        return self.verdict == GovernanceVerdict.HITL_REQUIRED


@dataclass
class AuditEntry:
    timestamp: str
    actor_id: str
    connection_type: str
    action: str
    resource: str
    verdict: str
    reason: str
    input_summary: str
    trace_id: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
