"""Grouping of sample dicts by metric name."""


def group_samples(samples):
    """Bucket sample dicts into a mapping of metric name -> list of samples.

    Samples keep their first-seen order inside each bucket.
    """
    groups = {}
    for sample in samples:
        groups.setdefault(sample["metric"], []).append(sample)
    return groups
