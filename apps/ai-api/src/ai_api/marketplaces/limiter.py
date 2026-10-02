"""A minimum interval between requests to the same host, shared by the worker's threads."""
from __future__ import annotations

import threading
import time
from collections.abc import Callable
from urllib.parse import urlparse


class HostLimiter:
    def __init__(self, interval_s: float, *, clock: Callable[[], float] = time.monotonic,
                 sleep: Callable[[float], None] = time.sleep) -> None:
        self._interval = interval_s
        self._clock = clock
        self._sleep = sleep
        self._next: dict[str, float] = {}
        self._lock = threading.Lock()

    def wait(self, url: str) -> None:
        """Block until the url's host may be asked again, and claim that turn."""
        host = urlparse(url).hostname or url
        with self._lock:
            now = self._clock()
            turn = max(now, self._next.get(host, now))
            self._next[host] = turn + self._interval
        if turn > now:
            self._sleep(turn - now)
