"""Formatting for the sample-export command."""

import json


ITEMS = ["alpha", "beta"]


def format_export(format_name):
    if format_name == "json":
        return json.dumps({"count": len(ITEMS), "items": ITEMS}, sort_keys=True)
    if format_name == "text":
        return "\n".join(ITEMS)
    raise ValueError(f"unsupported format: {format_name}")
