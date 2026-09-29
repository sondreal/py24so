import threading
import time
from typing import Callable


class RateLimiter:
    """Thread-safe token bucket that hands out request slots.

    :meth:`reserve` claims the next slot and returns how long the caller must wait
    before using it. Because the waiting happens outside the lock, the same
    limiter works for threads (``time.sleep``) and coroutines (``asyncio.sleep``),
    and concurrent callers are spaced out fairly instead of spinning.
    """

    def __init__(
        self,
        requests: int,
        period: float = 60.0,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        if requests < 1:
            raise ValueError("requests must be at least 1")
        if period <= 0:
            raise ValueError("period must be positive")
        self.capacity = float(requests)
        self.interval = period / requests
        self._clock = clock
        self._tokens = float(requests)
        self._updated = clock()
        self._lock = threading.Lock()

    def reserve(self) -> float:
        """Claim a slot and return the number of seconds to wait before using it."""
        with self._lock:
            now = self._clock()
            elapsed = now - self._updated
            self._updated = now
            self._tokens = min(self.capacity, self._tokens + elapsed / self.interval)
            self._tokens -= 1.0
            if self._tokens >= 0:
                return 0.0
            # Negative tokens are slots reserved in the future.
            return -self._tokens * self.interval
