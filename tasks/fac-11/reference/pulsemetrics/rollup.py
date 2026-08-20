"""Rollup of sample dicts into per-metric summaries."""

from .grouping import group_samples


def rollup(samples):
    """Aggregate sample dicts into per-metric summary dicts.

    Each summary carries ``"count"``, ``"mean"``, ``"min"``, ``"max"``, and
    ``"weight_total"``. The mean is the weighted mean of the group and
    metric names are listed in ascending alphabetical order.
    Weights default to 1.0 when a sample omits them.
    """
    groups = group_samples(samples)
    result = {}
    for metric in sorted(groups):
        bucket = groups[metric]
        values = [sample["value"] for sample in bucket]
        weights = [
            1.0 if sample.get("weight") is None else float(sample["weight"])
            for sample in bucket
        ]
        weight_total = sum(weights)
        weighted_sum = sum(v * w for v, w in zip(values, weights))
        result[metric] = {
            "count": len(values),
            "mean": weighted_sum / weight_total,
            "min": min(values),
            "max": max(values),
            "weight_total": weight_total,
        }
    return result
