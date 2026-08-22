#!/usr/bin/env python3
"""Run generated-file validation and the complete behavior suite."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tools"))

from build_routes import OUTPUT, load_routes, render  # noqa: E402


def main() -> int:
    expected = render(load_routes())
    if not OUTPUT.is_file() or OUTPUT.read_text(encoding="utf-8") != expected:
        print("generated route table is stale", file=sys.stderr)
        return 1
    suite = unittest.defaultTestLoader.discover(
        str(ROOT / "checks"), pattern="case_*.py", top_level_dir=str(ROOT)
    )
    return 0 if unittest.TextTestRunner(verbosity=2).run(suite).wasSuccessful() else 1


if __name__ == "__main__":
    raise SystemExit(main())
