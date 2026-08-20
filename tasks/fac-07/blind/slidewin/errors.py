"""Exception types raised by slidewin."""


class SlidewinError(Exception):
    """Base class for all slidewin errors."""


class RateLimitExceeded(SlidewinError):
    """Raised by RateLimiter.acquire when the window is already full."""
