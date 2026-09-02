from __future__ import annotations

import threading
import time
from dataclasses import dataclass, field
from typing import Callable

DEFAULT_INTERVALS = {
    "iiif_hd": 12.25,
    "text": 12.25,
    "pdf": 15.25,
    "highres": 1.25,
    "default": 0.0,
}


@dataclass
class RateLimiter:
    intervals: dict[str, float] = field(default_factory=lambda: dict(DEFAULT_INTERVALS))
    clock: Callable[[], float] = time.monotonic
    sleeper: Callable[[float], None] = time.sleep

    def __post_init__(self) -> None:
        self._last: dict[str, float] = {}
        self._lock = threading.Lock()

    def acquire(self, bucket: str = "default") -> float:
        interval = float(self.intervals.get(bucket, self.intervals.get("default", 0.0)))
        if interval <= 0:
            return 0.0
        with self._lock:
            now = self.clock()
            last = self._last.get(bucket)
            wait = 0.0 if last is None else max(0.0, interval - (now - last))
            if wait:
                self.sleeper(wait)
                now = self.clock()
            self._last[bucket] = now
            return wait
