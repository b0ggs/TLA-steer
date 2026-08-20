"""Tests for RateLimiter."""

import unittest

from slidewin.clock import ManualClock
from slidewin.config import LimiterConfig
from slidewin.errors import RateLimitExceeded
from slidewin.limiter import RateLimiter


def make_limiter(limit=3, window=60):
    clk = ManualClock()
    cfg = LimiterConfig(window_seconds=window, default_limit=limit)
    return RateLimiter(config=cfg, clock=clk), clk


class RateLimiterTests(unittest.TestCase):
    def test_allows_under_limit(self):
        limiter, _ = make_limiter(limit=3)
        limiter.acquire()
        limiter.acquire()  # still under the limit, must not raise

    def test_blocks_over_limit(self):
        limiter, _ = make_limiter(limit=2)
        limiter.acquire()
        limiter.acquire()
        with self.assertRaises(RateLimitExceeded):
            limiter.acquire()

    def test_keys_are_independent(self):
        limiter, _ = make_limiter(limit=1)
        limiter.acquire("a")
        limiter.acquire("b")  # a full key "a" must not affect key "b"


if __name__ == "__main__":
    unittest.main()
