"""Render second counts as human-readable duration strings."""

from durafmt.config import DEFAULT_PRECISION

_UNITS = (("d", 86400), ("h", 3600), ("m", 60), ("s", 1))


def format_duration(seconds):
    """Format a whole number of seconds as a compact string like "1h 1m 1s".

    Returns "0s" for a zero duration.
    """
    if seconds < 0:
        raise ValueError("seconds must be non-negative")
    parts = []
    remaining = int(seconds)
    for unit, size in _UNITS:
        count, remaining = divmod(remaining, size)
        if count:
            parts.append(f"{count}{unit}")
    if not parts:
        return "0s"
    return " ".join(parts)


def format_hours(seconds, precision=None):
    """Format a second count as a decimal hour string like "1.5h"."""
    if precision is None:
        precision = DEFAULT_PRECISION
    return f"{round(seconds / 3600, precision)}h"
