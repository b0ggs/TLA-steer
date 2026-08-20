"""Rollup of sample dicts into per-metric summaries."""

from .grouping import group_samples
from .stats import mean_value


def rollup(samples):
    """Aggregate sample dicts into per-metric summary dicts."""
    groups = group_samples(samples)
    result = {}
    for metric, bucket in groups.items():
        values = [sample["value"] for sample in bucket]
        result[metric] = {
            "count": len(values),
            "mean": mean_value(values),
            "min": min(values),
            "max": max(values),
        }
    return result
