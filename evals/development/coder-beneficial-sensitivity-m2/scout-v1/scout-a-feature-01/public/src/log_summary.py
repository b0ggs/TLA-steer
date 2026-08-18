"""Helpers for JSONL log summaries."""

import json


def normalize_level(value):
    """Return a level as text."""
    return str(value)


def iter_jsonl(lines):
    """Yield decoded JSON objects."""
    for line in lines:
        yield json.loads(line)


def summarize_jsonl(lines):
    """Count levels in JSON object lines."""
    counts = {}
    for item in iter_jsonl(lines):
        level = normalize_level(item.get("level", "unknown"))
        counts[level] = counts.get(level, 0) + 1
    return counts
