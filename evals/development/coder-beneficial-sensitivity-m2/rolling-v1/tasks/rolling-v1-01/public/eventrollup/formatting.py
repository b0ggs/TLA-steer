"""Stable JSON formatting shared by the command-line interface."""

import json


def compact_json(value):
    """Return deterministic compact JSON while preserving Unicode."""
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
