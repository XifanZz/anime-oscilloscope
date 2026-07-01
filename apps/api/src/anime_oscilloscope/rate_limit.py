from collections.abc import Callable
from dataclasses import dataclass
from threading import Lock
from time import monotonic


@dataclass(frozen=True)
class RateLimitDecision:
    allowed: bool
    remaining: int
    retry_after: int


class FixedWindowRateLimiter:
    """Small per-process limiter for expensive endpoints on the free API instance."""

    def __init__(
        self,
        *,
        limit: int,
        window_seconds: int,
        clock: Callable[[], float] = monotonic,
    ) -> None:
        self.limit = limit
        self.window_seconds = window_seconds
        self.clock = clock
        self._windows: dict[str, tuple[float, int]] = {}
        self._lock = Lock()

    def check(self, key: str) -> RateLimitDecision:
        now = self.clock()
        with self._lock:
            started_at, count = self._windows.get(key, (now, 0))
            if now - started_at >= self.window_seconds:
                started_at, count = now, 0
            if count >= self.limit:
                retry_after = max(1, round(self.window_seconds - (now - started_at)))
                return RateLimitDecision(False, 0, retry_after)
            count += 1
            self._windows[key] = (started_at, count)
            return RateLimitDecision(True, self.limit - count, 0)

    def reset(self) -> None:
        with self._lock:
            self._windows.clear()
