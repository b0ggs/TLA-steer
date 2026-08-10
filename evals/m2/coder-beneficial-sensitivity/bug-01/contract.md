# Duration parsing edge cases

Update `solution.py` so that it satisfies all of the following requirements:

- Parse hours, minutes, and seconds in compact or spaced text, case-insensitively.
- Format nonnegative seconds as a compact h/m/s string, omitting zero units except for zero itself.
- Raise ValueError for empty, negative, duplicated-unit, or otherwise malformed duration text.

Regression constraint: Keep accepting a digits-only string as a number of seconds.

