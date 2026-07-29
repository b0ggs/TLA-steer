# Issue contract

Change `normalize_username(value)` in `src/usernames.py` so normalized
usernames are lowercase after surrounding whitespace is removed.

Preserve the function's public API. The existing generic normalization policy
is unrelated to username normalization and does not need to be extended.
Add or update focused tests and run the unit tests.
