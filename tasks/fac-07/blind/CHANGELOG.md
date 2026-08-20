# Changelog

All notable changes to slidewin are recorded here, newest first. The next
patch release is 0.2.1.

## 0.2.1

- Fixed expiration of events exactly on the trailing-window boundary.

## 0.2.0

- Added `RateLimiter` with per-key counters, shadow-mode `hit()`, and
  `remaining()`.
- Added `LimiterConfig` and the `slidewin.errors` module.

## 0.1.0

- Initial release: `SlidingWindowCounter` plus `SystemClock` and
  `ManualClock`.
