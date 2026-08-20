"""End-to-end normalize + dedupe pipeline."""

from . import dedupe as dedupe_mod
from . import normalize


def run(records, key="email", strict=False):
    """Normalize every record, then deduplicate by ``key``."""
    normalized = [normalize.normalize_record(record) for record in records]
    return dedupe_mod.dedupe(normalized, key=key, strict=strict)
