"""Pure numeric helpers used by the rollup stage and the tests."""


def mean_value(values):
    """Return the arithmetic mean of a list of floats."""
    if not values:
        return 0.0
    return sum(values) / len(values)


def median_value(values):
    """Return the median of a list of floats."""
    ordered = sorted(values)
    n = len(ordered)
    mid = n // 2
    if n % 2:
        return ordered[mid]
    return (ordered[mid - 1] + ordered[mid]) / 2
