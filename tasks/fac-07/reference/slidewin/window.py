"""Sliding-window event counter."""

from .clock import SystemClock


class SlidingWindowCounter:
    """Counts events that occurred within the trailing time window."""

    def __init__(self, window_seconds, clock=None):
        if window_seconds <= 0:
            raise ValueError("window_seconds must be positive")
        self.window = float(window_seconds)
        self.clock = clock if clock is not None else SystemClock()
        self._events = []

    def record(self, timestamp=None):
        """Record one event at ``timestamp`` (clock time when omitted)."""
        ts = self.clock.now() if timestamp is None else float(timestamp)
        self._events.append(ts)

    def count(self, now=None):
        """Return the number of recorded events inside the window.

        The window is half-open on the old side: only events strictly
        younger than the window count.
        Events exactly window seconds old are expired.
        """
        if now is None:
            now = self.clock.now()
        cutoff = now - self.window
        self._events = [ts for ts in self._events if ts > cutoff]
        return len(self._events)
