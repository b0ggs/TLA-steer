"""Clock abstractions used by the counters and limiters."""

import time


class SystemClock:
    """Wall-clock time source backed by time.monotonic()."""

    def now(self):
        """Return the current time in seconds as a float."""
        return time.monotonic()


class ManualClock:
    """Deterministic clock for tests and examples.

    The clock starts at ``start`` (0.0 by default) and only moves when
    ``advance`` is called.
    """

    def __init__(self, start=0.0):
        self._now = float(start)

    def now(self):
        """Return the current manual time in seconds."""
        return self._now

    def advance(self, seconds):
        """Move the clock forward by ``seconds``."""
        delta = float(seconds)
        if delta < 0:
            raise ValueError("cannot advance clock backwards")
        self._now += delta
