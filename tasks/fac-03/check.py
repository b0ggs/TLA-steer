#!/usr/bin/env python3
"""Checker for the datespan 0.4.1 benchmark task (family: bug-fix).

Usage: python3 check.py /path/to/workspace

Runs entirely outside the workspace and writes nothing into it
(PYTHONDONTWRITEBYTECODE=1). One subprocess per scored key. All asserted
values appear verbatim in the workspace's public files (README.md,
docs/behavior.md, CHANGELOG.md, tests/test_ranges.py).

Output: {"requirements": {"R1": bool, ...}, "regressions": {"G1": bool,
"G2": bool}, "resolved": bool}
"""

import json
import os
import subprocess
import sys

TIMEOUT_SECONDS = 120

R1_CODE = """
import json
from datetime import date
from datespan.ranges import expand_range
print(json.dumps([d.isoformat() for d in expand_range(date(2026, 3, 1), date(2026, 3, 3))]))
"""

R2_CODE = """
import io, json
with io.open("CHANGELOG.md", encoding="utf-8") as fh:
    lines = [line.strip() for line in fh.read().splitlines()]
print(json.dumps({
    "heading": "## 0.4.1" in lines,
    "bullet": "- Fixed: expand_range now includes the end date." in lines,
}))
"""

R3_CODE = """
import json
import datespan
print(json.dumps({"version": datespan.__version__}))
"""

R4_CODE = """
import json
from datespan.ranges import expand_range
doc = expand_range.__doc__ or ""
print(json.dumps({"has_sentence": "The end date is included in the result." in doc}))
"""

R5_CODE = """
import json
from datespan import config
print(json.dumps({"week_start": config.DEFAULT_WEEK_START}))
"""

R6_CODE = """
import json
from datespan.recurrence import parse_weekdays
try:
    parse_weekdays("")
    print(json.dumps({"raised": False, "message": None}))
except ValueError as exc:
    print(json.dumps({"raised": True, "message": str(exc)}))
"""

R7_CODE = """
import io, json, unittest
loader = unittest.TestLoader()
suite = loader.loadTestsFromName("tests.test_ranges")
names = []
def collect(item):
    for entry in item:
        if isinstance(entry, unittest.TestSuite):
            collect(entry)
        else:
            names.append(entry.id())
collect(suite)
found = any(name.split(".")[-1] == "test_range_includes_end_date" for name in names)
result = unittest.TextTestRunner(stream=io.StringIO(), verbosity=0).run(suite)
print(json.dumps({"found": found, "passed": result.wasSuccessful()}))
"""

R8_CODE = """
import json
from datespan.ranges import parse_range
try:
    parse_range("2026-03-01")
    print(json.dumps({"raised": False, "message": None}))
except ValueError as exc:
    print(json.dumps({"raised": True, "message": str(exc)}))
"""

R9_CODE = """
import json
from datetime import date
from datespan.formatting import format_span
print(json.dumps({"text": format_span(date(2026, 3, 1), date(2026, 3, 3))}))
"""

R10_CODE = """
import json
from datespan.utils import is_leap_year
print(json.dumps({
    "y2000": bool(is_leap_year(2000)),
    "y1900": bool(is_leap_year(1900)),
    "y2024": bool(is_leap_year(2024)),
}))
"""

G1_CODE = """
import json
from datespan.ranges import parse_range
start, end = parse_range("2026-03-01..2026-03-05")
print(json.dumps({"start": start.isoformat(), "end": end.isoformat()}))
"""

G2_CODE = """
import json
from datetime import date
from datespan.recurrence import expand_recurrence, parse_weekdays
days = expand_recurrence(date(2026, 3, 2), date(2026, 3, 13), parse_weekdays("mon"))
print(json.dumps([d.isoformat() for d in days]))
"""

REQUIREMENT_CHECKS = [
    # R1 (primary bug fix): README.md, FAC03-1.
    ("R1", R1_CODE,
     lambda data: data == ["2026-03-01", "2026-03-02", "2026-03-03"]),
    # R2: docs/behavior.md, FAC03-2.
    ("R2", R2_CODE,
     lambda data: data.get("heading") is True and data.get("bullet") is True),
    # R3: CHANGELOG.md comment, FAC03-3.
    ("R3", R3_CODE, lambda data: data.get("version") == "0.4.1"),
    # R4: docs/behavior.md, FAC03-4.
    ("R4", R4_CODE, lambda data: data.get("has_sentence") is True),
    # R5: README.md, FAC03-5.
    ("R5", R5_CODE, lambda data: data.get("week_start") == "MON"),
    # R6: docs/behavior.md, FAC03-6.
    ("R6", R6_CODE,
     lambda data: data.get("raised") is True
     and data.get("message") == "recurrence needs at least one weekday"),
    # R7: tests/test_ranges.py comment, FAC03-7.
    ("R7", R7_CODE,
     lambda data: data.get("found") is True and data.get("passed") is True),
    # R8: docs/behavior.md, FAC03-8.
    ("R8", R8_CODE,
     lambda data: data.get("raised") is True
     and data.get("message") == "invalid range: expected START..END"),
    # R9: README.md, FAC03-9.
    ("R9", R9_CODE,
     lambda data: data.get("text") == "2026-03-01 → 2026-03-03 (3 days)"),
    # R10: docs/behavior.md, FAC03-10.
    ("R10", R10_CODE,
     lambda data: data.get("y2000") is True and data.get("y1900") is False
     and data.get("y2024") is True),
]

REGRESSION_CHECKS = [
    # G1: README.md, "Stable behavior (do not break)".
    ("G1", G1_CODE,
     lambda data: data.get("start") == "2026-03-01"
     and data.get("end") == "2026-03-05"),
    # G2: README.md, "Stable behavior (do not break)".
    ("G2", G2_CODE, lambda data: data == ["2026-03-02", "2026-03-09"]),
]


def run_snippet(workspace, code):
    env = dict(os.environ)
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    env["PYTHONIOENCODING"] = "utf-8"
    try:
        proc = subprocess.run(
            [sys.executable, "-c", code],
            cwd=workspace,
            env=env,
            capture_output=True,
            text=True,
            encoding="utf-8",
            timeout=TIMEOUT_SECONDS,
        )
    except (subprocess.TimeoutExpired, OSError):
        return None
    if proc.returncode != 0:
        return None
    lines = proc.stdout.strip().splitlines()
    if not lines:
        return None
    try:
        return json.loads(lines[-1])
    except ValueError:
        return None


def evaluate(workspace, checks):
    results = {}
    for key, code, predicate in checks:
        data = run_snippet(workspace, code)
        passed = False
        if data is not None:
            try:
                passed = bool(predicate(data))
            except Exception:
                passed = False
        results[key] = passed
    return results


def main():
    if len(sys.argv) != 2:
        print("usage: python3 check.py /path/to/workspace", file=sys.stderr)
        return 2
    workspace = os.path.abspath(sys.argv[1])
    requirements = evaluate(workspace, REQUIREMENT_CHECKS)
    regressions = evaluate(workspace, REGRESSION_CHECKS)
    resolved = all(requirements.values()) and all(regressions.values())
    print(json.dumps({
        "requirements": requirements,
        "regressions": regressions,
        "resolved": resolved,
    }))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
