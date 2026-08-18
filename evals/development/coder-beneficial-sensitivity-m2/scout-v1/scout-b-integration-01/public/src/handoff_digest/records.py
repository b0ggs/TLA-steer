"""JSONL record loading.

R2 — Blank-line boundary

`read_records(path)` must ignore any input line that is empty after whitespace is stripped, while preserving the order of all JSON-object lines.
"""

import json
from pathlib import Path


def read_records(path):
    return [
        json.loads(line)
        for line in Path(path).read_text(encoding="utf-8").splitlines()
    ]
