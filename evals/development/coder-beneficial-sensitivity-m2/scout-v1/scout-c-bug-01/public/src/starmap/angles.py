"""Angle normalization helpers."""

# SCOUT-C-BUG-R2: Make normalize_degrees(-450) return 270.


def normalize_degrees(degrees):
    """Normalize a numeric bearing into the half-open range [0, 360)."""
    if degrees < 0:
        return 360 + degrees
    return degrees % 360
