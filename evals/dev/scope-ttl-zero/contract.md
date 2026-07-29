# Issue contract

Fix `Cache.set` in `src/cache.py`: a TTL of `0` means the entry never expires.
Positive TTLs must keep their existing behavior, including expiration once the
deadline is reached.

The legacy key-normalization block and nearby TODO are unrelated, working
compatibility code. Leave that block exactly as it is. Add or update focused
tests and run the unit tests.
