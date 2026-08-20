"""Parser for compact duration strings like "1h30m"."""

import re

_TOKEN = re.compile(r"(\d+)([dhms])")

_MULTIPLIERS = {
    "d": 86400,
    "h": 3600,
    "m": 60,
    "s": 1,
}


def parse(spec):
    """Parse a compact duration string like "1h30m" into whole seconds.

    Supported units: d (days), h (hours), m (minutes), s (seconds).
    Raises TypeError for non-string input and ValueError for malformed
    input.
    """
    if not isinstance(spec, str):
        raise TypeError("duration spec must be a string")
    if not spec:
        raise ValueError("empty duration string")
    tokens = _TOKEN.findall(spec)
    consumed = "".join(value + unit for value, unit in tokens)
    if not tokens or consumed != spec:
        raise ValueError(f"invalid duration: {spec!r}")
    return sum(int(value) * _MULTIPLIERS[unit] for value, unit in tokens)
