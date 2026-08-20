"""Minimal durafmt example: total seconds for a 90-minute workshop."""


import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import durafmt

expected = 5400
total = durafmt.parse("90m")
assert total == expected, f"expected {expected}, got {total}"
print(f"total: {total}")
