"""Rate limiter in-memory cho demo lớp học."""

from __future__ import annotations

import time
from collections import defaultdict


class RateLimiter:
    def __init__(self, max_calls_per_minute: int = 30):
        self.max_calls = max_calls_per_minute
        self._windows: dict[str, list[float]] = defaultdict(list)

    def check(self, actor_id: str) -> tuple[bool, str]:
        now = time.time()
        window = self._windows[actor_id]
        window[:] = [ts for ts in window if now - ts < 60]
        if len(window) >= self.max_calls:
            return False, f"Vượt rate limit ({self.max_calls}/phút) cho actor '{actor_id}'"
        window.append(now)
        return True, "ok"

    def reset(self, actor_id: str | None = None) -> None:
        if actor_id:
            self._windows.pop(actor_id, None)
        else:
            self._windows.clear()
