"""Per-key rate limiting on top of SlidingWindowCounter."""

from .config import LimiterConfig
from .errors import RateLimitExceeded
from .window import SlidingWindowCounter


class RateLimiter:
    """Enforces a per-key event limit over a sliding time window."""

    def __init__(self, limit=None, config=None, clock=None):
        cfg = config if config is not None else LimiterConfig()
        self.limit = cfg.default_limit if limit is None else int(limit)
        self.window = cfg.window_seconds
        self.clock = clock
        self._counters = {}

    def _counter(self, key):
        if key not in self._counters:
            self._counters[key] = SlidingWindowCounter(
                self.window, clock=self.clock
            )
        return self._counters[key]

    def acquire(self, key="default"):
        """Record one event for ``key``, or raise if the window is full.

        Returns the number of slots still available after the call.
        """
        counter = self._counter(key)
        if counter.count() >= self.limit:
            raise RateLimitExceeded(
                "limit of {0} per {1}s exceeded".format(self.limit, self.window)
            )
        counter.record()
        return self.remaining(key)

    def hit(self, key="default"):
        """Record one event for ``key`` unconditionally (shadow mode)."""
        self._counter(key).record()

    def remaining(self, key="default"):
        """Return how many more events ``key`` may record in the window.

        Clamped at zero: never returns a negative number, even when
        shadow-mode hits exceed the limit.
        """
        return max(0, self.limit - self._counter(key).count())
