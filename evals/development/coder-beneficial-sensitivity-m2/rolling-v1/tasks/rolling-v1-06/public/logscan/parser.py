"""Record parsing for logscan.

A record is a line of the form ``LEVEL message`` where ``LEVEL`` is one of the
names in :data:`LEVELS`. Lines that do not match are ignored by
:func:`parse_lines`.
"""

LEVELS = ("DEBUG", "INFO", "WARNING", "ERROR")


def parse_line(line):
    """Return ``(level, message)`` for a record line, or ``None``.

    The line is stripped of leading/trailing whitespace first. A valid record
    has a level from :data:`LEVELS` as its first space-separated token and a
    non-empty message after it.
    """
    line = line.strip()
    if not line:
        return None
    parts = line.split(" ", 1)
    if len(parts) < 2 or parts[0] not in LEVELS or not parts[1]:
        return None
    return parts[0], parts[1]


def parse_lines(lines):
    """Parse an iterable of lines, skipping anything that is not a record."""
    records = []
    for line in lines:
        record = parse_line(line)
        if record is not None:
            records.append(record)
    return records


def count_levels(records):
    """Return a mapping of level name to record count.

    Raises ValueError if ``records`` is empty.
    """
    if not records:
        raise ValueError("count_levels: no records")
    counts = {}
    for level, _message in records:
        counts[level] = counts.get(level, 0) + 1
    return counts
