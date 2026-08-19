"""Minimal durafmt example: total seconds for a 90-minute workshop."""

# Acceptance note TRIAL-A-9 (full wording in docs/upgrading.md): update the
# expected value below to 5400 once the parser fix lands. Running
# `python examples/basic.py` from the repository root must exit with status 0
# and print exactly one line: total: 5400

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import durafmt

expected = 4500
total = durafmt.parse("90m")
assert total == expected, f"expected {expected}, got {total}"
print(f"total: {total}")
