"""slidewin: a small sliding-window rate-limit counter library."""

__version__ = "0.2.1"

from .clock import ManualClock, SystemClock
from .config import LimiterConfig
from .errors import RateLimitExceeded, SlidewinError
from .limiter import RateLimiter
from .window import SlidingWindowCounter

__all__ = [
    "LimiterConfig",
    "ManualClock",
    "RateLimitExceeded",
    "RateLimiter",
    "SlidewinError",
    "SlidingWindowCounter",
    "SystemClock",
    "__version__",
]
