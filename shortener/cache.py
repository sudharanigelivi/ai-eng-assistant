import threading
import time
from collections import OrderedDict
from typing import Callable, Generic, Hashable, TypeVar

V = TypeVar("V")


class TTLCache(Generic[V]):
    """Small thread-safe LRU cache with per-entry TTL."""

    def __init__(self, max_size: int, ttl: float, clock: Callable[[], float] = time.monotonic):
        self._max_size = max_size
        self._ttl = ttl
        self._clock = clock
        self._data: OrderedDict[Hashable, tuple[float, V]] = OrderedDict()
        self._lock = threading.Lock()

    def get(self, key: Hashable) -> V | None:
        with self._lock:
            item = self._data.get(key)
            if item is None:
                return None
            expires, value = item
            if expires <= self._clock():
                del self._data[key]
                return None
            self._data.move_to_end(key)
            return value

    def set(self, key: Hashable, value: V) -> None:
        if self._max_size <= 0:
            return
        with self._lock:
            self._data[key] = (self._clock() + self._ttl, value)
            self._data.move_to_end(key)
            while len(self._data) > self._max_size:
                self._data.popitem(last=False)

    def invalidate(self, key: Hashable) -> None:
        with self._lock:
            self._data.pop(key, None)

    def __len__(self) -> int:
        return len(self._data)
