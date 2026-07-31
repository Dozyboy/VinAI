"""Agent registry in-memory — mô phỏng khái niệm registry MCP server Ngày 26."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


@dataclass
class RegisteredAgent:
    name: str
    url: str
    description: str
    capabilities: dict[str, Any] = field(default_factory=dict)
    healthy: bool = True
    registered_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )


class AgentRegistry:
    def __init__(self) -> None:
        self._agents: dict[str, RegisteredAgent] = {}

    def register(self, agent: RegisteredAgent) -> None:
        self._agents[agent.name] = agent

    def deregister(self, name: str) -> None:
        self._agents.pop(name, None)

    def set_health(self, name: str, healthy: bool) -> None:
        if name in self._agents:
            self._agents[name].healthy = healthy

    def list_agents(self, healthy_only: bool = False) -> list[RegisteredAgent]:
        agents = list(self._agents.values())
        if healthy_only:
            agents = [agent for agent in agents if agent.healthy]
        return agents

    def find_by_capability(self, keyword: str) -> list[RegisteredAgent]:
        keyword_lower = keyword.lower()
        return [
            agent
            for agent in self._agents.values()
            if keyword_lower in agent.description.lower()
            or keyword_lower in str(agent.capabilities).lower()
        ]
