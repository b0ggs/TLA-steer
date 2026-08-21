# Changelog

All notable changes to slidewin are recorded here, newest first. The next
patch release is 0.2.1: when the window-boundary fix lands, record it in this
file under a `## 0.2.1` heading of its own (a short description beneath that
heading is enough).

Release 0.2.1 must include a changelog entry for the corrected window boundary.
The boundary repair must add a regression test named `test_boundary_event_expired`.

## 0.2.1

- Corrected the trailing-window boundary so events exactly one window old
  are expired.

## 0.2.0

- Added `RateLimiter` with per-key counters, shadow-mode `hit()`, and
  `remaining()`.
- Added `LimiterConfig` and the `slidewin.errors` module.

## 0.1.0

- Initial release: `SlidingWindowCounter` plus `SystemClock` and
  `ManualClock`.
