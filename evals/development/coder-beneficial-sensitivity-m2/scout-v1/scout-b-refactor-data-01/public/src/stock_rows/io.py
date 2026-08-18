"""JSON serialization."""

import json
from pathlib import Path

from .convert import row_to_mapping


def dump_rows(rows, output_path, config_path):
    payload = [row_to_mapping(row) for row in rows]
    Path(output_path).write_text(
        json.dumps(payload, sort_keys=True) + "\n",
        encoding="utf-8",
    )
