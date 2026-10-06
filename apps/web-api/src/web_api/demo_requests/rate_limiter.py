"""An in-process sliding-window rate limiter keyed by client."""
from __future__ import annotations

import math
from collections import defaultdict, deque
from dataclasses import dataclass
from threading import Lock


@dataclass(frozen=True)
class RateLimitDecision:
    allowed: bool
    retry_after_seconds: int = 0


class SlidingWindowRateLimiter:
    """Admits at most ``limit`` requests per key within the trailing window."""

    def __init__(self, window_seconds: float) -> None:
        self._window_seconds = window_seconds
        self._admitted: dict[str, deque[float]] = defaultdict(deque)
        self._lock = Lock()

    def admit(self, key: str, limit: int, now: float) -> RateLimitDecision:
        """Record a request for ``key`` at ``now`` if the window has room for it."""
        with self._lock:
            admitted = self._admitted[key]
            window_start = now - self._window_seconds
            while admitted and admitted[0] <= window_start:
                admitted.popleft()
            if len(admitted) >= limit:
                return self._refusal(admitted, limit, now)
            admitted.append(now)
            return RateLimitDecision(allowed=True)

    def _refusal(self, admitted: deque[float], limit: int, now: float) -> RateLimitDecision:
        if limit <= 0:
            return RateLimitDecision(allowed=False, retry_after_seconds=math.ceil(self._window_seconds))
        frees_up_at = admitted[len(admitted) - limit] + self._window_seconds
        retry_after = max(1, math.ceil(frees_up_at - now))
        return RateLimitDecision(allowed=False, retry_after_seconds=retry_after)
