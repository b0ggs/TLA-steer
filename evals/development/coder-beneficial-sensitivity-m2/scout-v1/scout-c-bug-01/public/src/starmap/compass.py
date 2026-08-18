"""Human-readable compass labels."""

from .angles import normalize_degrees


def direction_name(degrees):
    """Return the nearest cardinal direction, or unknown for a missing value."""
    if not degrees:
        return "unknown"
    normalized = normalize_degrees(degrees)
    names = ("N", "E", "S", "W")
    return names[int((normalized + 45) // 90) % 4]
