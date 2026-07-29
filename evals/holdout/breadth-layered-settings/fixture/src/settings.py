"""Application settings loaded from defaults and an optional JSON file."""

import json
from pathlib import Path


DEFAULTS = {
    "timeout_seconds": 30,
    "debug": False,
}


def load_settings(path=None):
    settings = dict(DEFAULTS)
    if path is not None:
        settings.update(json.loads(Path(path).read_text(encoding="utf-8")))
    return settings
