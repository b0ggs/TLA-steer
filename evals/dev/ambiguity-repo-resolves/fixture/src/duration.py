"""Human-readable duration formatting."""


def display_duration(minutes):
    if minutes < 0:
        raise ValueError("minutes must be nonnegative")
    return f"{minutes} min"
