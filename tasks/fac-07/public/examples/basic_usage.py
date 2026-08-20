"""Basic slidewin usage with a deterministic manual clock.

Run from the repository root:

    PYTHONPATH=. python examples/basic_usage.py
"""

from slidewin import LimiterConfig, ManualClock, RateLimiter

clk = ManualClock()
cfg = LimiterConfig(window_seconds=60, default_limit=5)
limiter = RateLimiter(config=cfg, clock=clk)

for i in range(5):
    limiter.acquire("api")
    clk.advance(1)

print("remaining for 'api':", limiter.remaining("api"))

# Shadow mode: record without enforcing.
for i in range(3):
    limiter.hit("background")
print("remaining for 'background':", limiter.remaining("background"))
