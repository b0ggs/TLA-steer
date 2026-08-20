# slidewin

A small, dependency-free sliding-window rate-limit counter library. It ships
two building blocks: `SlidingWindowCounter`, which counts events inside a
trailing time window, and `RateLimiter`, which enforces a per-key limit on top
of one counter per key. Clocks are pluggable, so tests and examples use a
deterministic `ManualClock` instead of wall time.

## Quick start

```python
from slidewin import LimiterConfig, ManualClock, RateLimiter

clk = ManualClock()
cfg = LimiterConfig(window_seconds=60, default_limit=5)
limiter = RateLimiter(config=cfg, clock=clk)

limiter.acquire("api")        # records one event for key "api"
print(limiter.remaining("api"))
```

A runnable version of this snippet lives in `examples/basic_usage.py`; run it
from the repository root with `PYTHONPATH=. python examples/basic_usage.py`.

## Configuration

`LimiterConfig` holds the two knobs a limiter needs: `window_seconds` and
`default_limit`. Out of the box a limiter allows five events per sixty
seconds, which means `LimiterConfig()` constructed with no arguments reports a
`window_seconds` of 60 and a `default_limit` of 5. Pass either argument
explicitly to override the stock values for a single limiter.

## Enforcement and shadow mode

`RateLimiter.acquire(key)` checks the window for that key, raises
`RateLimitExceeded` when the limit is already reached (the exact message
wording is specified in `docs/design.md`), and otherwise records the event.
A successful `acquire` returns the number of slots still available after the
call: with a fresh limiter whose limit is 5, the first `acquire` returns 4 and
the second returns 3.

When you only want to observe traffic rather than block it, run in shadow
mode: call `hit(key)` to record an event unconditionally, with no limit check.
Because shadow mode can push the recorded count past the limit,
`remaining(key)` is clamped at zero — it never returns a negative number; once
hits meet or exceed the limit it simply returns 0.

## Releases

Every released change bumps `__version__` in `slidewin/__init__.py` and gets a
matching entry in `CHANGELOG.md`. The window-boundary fix tracked in the
current issue ships as version 0.2.1, so `__version__` reads `"0.2.1"` once
that fix lands.

## Layout

- `slidewin/window.py` — the sliding-window counter
- `slidewin/limiter.py` — per-key rate limiting on top of the counter
- `slidewin/clock.py` — `SystemClock` and the deterministic `ManualClock`
- `slidewin/config.py` — `LimiterConfig`
- `slidewin/errors.py` — exception types
- `docs/design.md` — window semantics, clock contract, error wording
- `tests/` — unittest suite; run with `python -m unittest discover -s tests -t .`
