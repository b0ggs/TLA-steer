"""Read JSON Lines record files."""
import json


class LoaderError(ValueError):
    """Raised when a records file cannot be read as JSON Lines."""


def iter_records(path):
    """Return a list of (lineno, record) pairs from a JSON Lines file."""
    with open(path, encoding="utf-8") as fh:
        text = fh.read()
    if not text.strip():
        return []
    records = []
    for lineno, line in enumerate(text.splitlines(), start=1):
        line = line.strip()
        if not line:
            continue
        try:
            record = json.loads(line)
        except json.JSONDecodeError as exc:
            raise LoaderError("line %d: %s" % (lineno, exc)) from exc
        if not isinstance(record, dict):
            raise LoaderError("line %d: record must be a JSON object" % lineno)
        records.append((lineno, record))
    return records
