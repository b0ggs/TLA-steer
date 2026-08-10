# Per-key sliding limiter

Update `solution.py` so that it satisfies all of the following requirements:

- Implement RateLimiter(limit, window) whose allow(key, now) permits at most limit events in the preceding window.
- Expire an event exactly at now-window so boundary timestamps are allowed.
- Track keys independently and provide reset(key=None) for one key or all keys.

Regression constraint: Reject nonpositive limit or window constructor arguments with ValueError.

