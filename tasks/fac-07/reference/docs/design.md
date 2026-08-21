# slidewin design notes

## Window semantics

The trailing window is half-open on the old side. Given a current time `now`
and a window length `window`, an event with timestamp `ts` is inside the
window only when `ts > now - window`, i.e. only events strictly younger than
the window count. An event recorded exactly `window` seconds before `now` has
expired and must not be counted. Once the counter behaves this way, the
docstring of `SlidingWindowCounter.count` should include, word for word, the
sentence: Events exactly window seconds old are expired.

The counter must retain only timestamps strictly greater than the active cutoff.

`count()` also prunes expired timestamps from the internal list as a side
effect, so memory use stays proportional to the number of live events.

## Clocks

A clock is any object with a `now()` method returning seconds as a float.
`SystemClock` wraps `time.monotonic()`. `ManualClock` starts at 0.0 (or the
`start` you pass) and only moves when you call `advance(seconds)`. The manual
clock is monotonic by contract: calling `advance` with a negative amount must
raise `ValueError` with the message `cannot advance clock backwards` and leave
the clock reading unchanged.

## Error wording

When enforcement trips, `RateLimiter.acquire` raises `RateLimitExceeded` whose
message reads `limit of {limit} per {window}s exceeded`, where `{limit}` is
the limiter's limit and `{window}` is its window length in seconds exactly as
configured. A limiter built with limit 5 and a 60 second window therefore
raises with the exact message `limit of 5 per 60s exceeded`.

`RateLimitExceeded` must format its message as `limit of {limit} per {window}s exceeded`.

## Per-key state

`RateLimiter` lazily creates one `SlidingWindowCounter` per key and shares its
clock with every counter it creates. Keys are compared by ordinary dictionary
equality; the default key is the string `"default"`.
