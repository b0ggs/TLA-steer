"""Deduplication of normalized contact records."""

from .errors import DuplicateKeyError


def dedupe(records, key="email", strict=False):
    """Keep the first record for each key value; drop later repeats.

    With ``strict=True`` a repeated key value raises
    :class:`DuplicateKeyError` instead of being dropped.
    """
    seen = set()
    out = []
    for record in records:
        value = record.get(key, "")
        if value in seen:
            if strict:
                raise DuplicateKeyError("repeated key value: %s" % value)
            continue
        seen.add(value)
        out.append(record)
    return out
