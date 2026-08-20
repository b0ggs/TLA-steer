"""Configuration for slidewin limiters."""


class LimiterConfig:
    """Holds the window length and default limit for a RateLimiter."""

    def __init__(self, window_seconds=60, default_limit=5):
        if window_seconds <= 0:
            raise ValueError("window_seconds must be positive")
        if default_limit <= 0:
            raise ValueError("default_limit must be positive")
        self.window_seconds = window_seconds
        self.default_limit = default_limit
