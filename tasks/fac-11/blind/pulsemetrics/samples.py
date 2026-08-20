"""Parsing of raw sample lines into sample dicts."""


def parse_line(line):
    """Parse a ``metric value [weight]`` line into a sample dict.

    Returns a dict with the keys ``"metric"`` (str), ``"value"`` (float),
    and ``"weight"`` (float, or ``None`` when the line has no third
    column).
    """
    parts = line.strip().split()
    if len(parts) == 2:
        metric, raw_value = parts
        weight = None
    elif len(parts) == 3:
        metric, raw_value, raw_weight = parts
        weight = float(raw_weight)
    else:
        raise ValueError("could not parse sample line: %r" % line)
    return {"metric": metric, "value": float(raw_value), "weight": weight}
