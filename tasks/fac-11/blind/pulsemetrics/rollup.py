"""Rollup of sample dicts into per-metric summaries."""

from .grouping import group_samples


def rollup(samples):
    """Aggregate sample dicts into per-metric summary dicts.

    Weights default to 1.0 when a sample omits them.
    """
    groups = group_samples(samples)
    result = {}
    for metric in sorted(groups):
        bucket = groups[metric]
        values = [sample["value"] for sample in bucket]
        weights = [
            1.0 if sample.get("weight") is None else sample["weight"]
            for sample in bucket
        ]
        weight_total = sum(weights)
        result[metric] = {
            "count": len(values),
            "mean": sum(value * weight for value, weight in zip(values, weights))
            / weight_total,
            "min": min(values),
            "max": max(values),
            "weight_total": weight_total,
        }
    return result
