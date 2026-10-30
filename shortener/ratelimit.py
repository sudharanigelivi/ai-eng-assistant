import threading
import time
from typing import Callable


class RateLimiter:
    """In-process token bucket per key. Use a shared store for multi-node limits."""

    def __init__(self, per_minute: int, clock: Callable[[], float] = time.monotonic):
        self._rate = per_minute / 60.0
        self._capacity = float(per_minute)
        self._clock = clock
        self._buckets: dict[str, tuple[float, float]] = {}
        self._lock = threading.Lock()

    @property
    def enabled(self) -> bool:
        return self._capacity > 0

    def allow(self, key: str) -> bool:
        if not self.enabled:
            return True
        now = self._clock()
        with self._lock:
            tokens, last = self._buckets.get(key, (self._capacity, now))
            tokens = min(self._capacity, tokens + (now - last) * self._rate)
            allowed = tokens >= 1
            if allowed:
                tokens -= 1
            self._buckets[key] = (tokens, now)
            if len(self._buckets) > 50_000:  # bound memory under key churn
                self._buckets = {k: v for k, v in self._buckets.items() if v[0] < self._capacity}
            return allowed
