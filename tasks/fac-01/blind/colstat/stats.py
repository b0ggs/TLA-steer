"""Column statistics primitives for colstat."""

import math


def mean(values):
    """Return the arithmetic mean of a non-empty list of numbers."""
    return sum(values) / len(values)


def median(values):
    """Return the median of a non-empty list of numbers.

    Returns the mean of the two middle values when n is even.
    """
    ordered = sorted(values)
    midpoint = len(ordered) // 2
    if len(ordered) % 2:
        return ordered[midpoint]
    return (ordered[midpoint - 1] + ordered[midpoint]) / 2


def minimum(values):
    """Return the smallest value in a non-empty list of numbers."""
    return min(values)


def maximum(values):
    """Return the largest value in a non-empty list of numbers."""
    return max(values)


def stdev(values):
    """Return the population standard deviation; 0.0 for fewer than two values."""
    if len(values) < 2:
        return 0.0
    center = mean(values)
    return math.sqrt(sum((v - center) ** 2 for v in values) / len(values))


def column_summary(values, precision):
    """Build the summary mapping for one numeric column."""
    return {
        "count": len(values),
        "min": round(minimum(values), precision),
        "max": round(maximum(values), precision),
        "mean": round(mean(values), precision),
        "median": round(median(values), precision),
        "stdev": round(stdev(values), precision),
    }
