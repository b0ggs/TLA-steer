#!/usr/bin/env python3
"""Checker for the PulseMetrics weighted-rollup task.

Usage: python check.py /path/to/workspace

Runs entirely outside the workspace, writes nothing into it, and launches
one subprocess per requirement. Emits canonical JSON:
{"requirements": {"R1": bool, ...}, "regressions": {"G1": bool, "G2": bool},
 "resolved": bool}
"""

import json
import math
import os
import subprocess
import sys
import tempfile

TIMEOUT = 120


def run_py(ws, code):
    """Run a python -c snippet with the workspace on PYTHONPATH.

    Returns the parsed JSON object printed on the snippet's last stdout
    line, or None on any failure (non-zero exit, timeout, bad JSON).
    """
    env = dict(os.environ)
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    env["PYTHONPATH"] = ws
    with tempfile.TemporaryDirectory() as td:
        try:
            proc = subprocess.run(
                [sys.executable, "-c", code],
                cwd=td,
                env=env,
                capture_output=True,
                text=True,
                timeout=TIMEOUT,
            )
        except (subprocess.TimeoutExpired, OSError):
            return None
    if proc.returncode != 0:
        return None
    lines = [ln for ln in proc.stdout.splitlines() if ln.strip()]
    if not lines:
        return None
    try:
        return json.loads(lines[-1])
    except (ValueError, TypeError):
        return None


def close(a, b):
    try:
        return math.isclose(float(a), float(b), rel_tol=1e-9, abs_tol=1e-9)
    except (TypeError, ValueError):
        return False


def check_r1(ws):
    # Weighted mean + weight_total, using the worked examples given
    # verbatim in public/.issue-contract.md.
    code = """
import json
from pulsemetrics.rollup import rollup
a = rollup([
    {"metric": "cpu", "value": 10.0, "weight": 1.0},
    {"metric": "cpu", "value": 20.0, "weight": 3.0},
])["cpu"]
b = rollup([
    {"metric": "cpu", "value": 4.0},
    {"metric": "cpu", "value": 8.0, "weight": 3.0},
])["cpu"]
c = rollup([
    {"metric": "cpu", "value": 5.0, "weight": None},
])["cpu"]
print(json.dumps({"a": a, "b": b, "c": c}))
"""
    data = run_py(ws, code)
    if not isinstance(data, dict):
        return False
    try:
        a, b, c = data["a"], data["b"], data["c"]
        return (
            close(a["mean"], 17.5)
            and close(a["weight_total"], 4.0)
            and close(b["mean"], 7.0)
            and close(b["weight_total"], 4.0)
            and close(c["mean"], 5.0)
            and close(c["weight_total"], 1.0)
        )
    except (KeyError, TypeError):
        return False


def check_r2(ws):
    # CHANGELOG.md gains a "## 0.4.0" section whose first bullet line reads
    # exactly "- Weighted means: rollup now honors per-sample weights."
    # (heading and bullet text given verbatim in README.md, Releasing).
    code = """
import json
lines = open({path!r}, encoding="utf-8").read().splitlines()
in_section = False
bullet = None
for ln in lines:
    stripped = ln.strip()
    if stripped.startswith("## "):
        if in_section:
            break
        in_section = stripped.startswith("## 0.4.0")
        continue
    if in_section and stripped.startswith("-") and bullet is None:
        bullet = stripped
        break
print(json.dumps({{"bullet": bullet}}))
""".format(path=os.path.join(ws, "CHANGELOG.md"))
    data = run_py(ws, code)
    if not isinstance(data, dict):
        return False
    return data.get("bullet") == "- Weighted means: rollup now honors per-sample weights."


def check_r3(ws):
    # __version__ bumped to "0.4.0" (stated in CHANGELOG.md, Unreleased).
    code = """
import json, pulsemetrics
print(json.dumps({"version": pulsemetrics.__version__}))
"""
    data = run_py(ws, code)
    return isinstance(data, dict) and data.get("version") == "0.4.0"


def check_r4(ws):
    # rollup docstring contains the exact sentence given in
    # docs/aggregation.md.
    code = """
import json
from pulsemetrics.rollup import rollup
print(json.dumps({"doc": rollup.__doc__ or ""}))
"""
    data = run_py(ws, code)
    if not isinstance(data, dict):
        return False
    return "Weights default to 1.0 when a sample omits them." in data.get("doc", "")


def check_r5(ws):
    # DEFAULT_PRECISION in pulsemetrics/report.py changes from 2 to 4
    # (stated in README.md, Reports).
    code = """
import json
from pulsemetrics import report
print(json.dumps({"precision": report.DEFAULT_PRECISION}))
"""
    data = run_py(ws, code)
    return isinstance(data, dict) and data.get("precision") == 4


def check_r6(ws):
    # mean_value([]) returns 0.0 instead of raising (stated in the
    # maintenance note at the top of tests/test_stats.py).
    code = """
import json
from pulsemetrics.stats import mean_value
try:
    out = {"ok": True, "value": mean_value([])}
except Exception as exc:
    out = {"ok": False, "error": type(exc).__name__}
print(json.dumps(out))
"""
    data = run_py(ws, code)
    return isinstance(data, dict) and data.get("ok") is True and close(data.get("value"), 0.0)


def check_r7(ws):
    # tests/test_rollup.py contains a test function named
    # test_weighted_mean, and the whole suite passes
    # (python -m unittest discover -s tests), per README.md, Testing.
    code = """
import ast, io, json, unittest
src = open({path!r}, encoding="utf-8").read()
names = set()
for node in ast.walk(ast.parse(src)):
    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
        names.add(node.name)
suite = unittest.defaultTestLoader.discover({tests!r})
buf = io.StringIO()
result = unittest.TextTestRunner(stream=buf, verbosity=0).run(suite)
print(json.dumps({{
    "has_test": "test_weighted_mean" in names,
    "passed": result.wasSuccessful(),
    "ran": result.testsRun,
}}))
""".format(
        path=os.path.join(ws, "tests", "test_rollup.py"),
        tests=os.path.join(ws, "tests"),
    )
    data = run_py(ws, code)
    if not isinstance(data, dict):
        return False
    return (
        data.get("has_test") is True
        and data.get("passed") is True
        and isinstance(data.get("ran"), int)
        and data.get("ran") >= 1
    )


def check_r8(ws):
    # group_samples raises ValueError("sample is missing a metric name")
    # for a sample without a "metric" key (exact wording given in
    # docs/aggregation.md).
    code = """
import json
from pulsemetrics.grouping import group_samples
try:
    group_samples([{"value": 1.0}])
    out = {"raised": False}
except ValueError as exc:
    out = {"raised": True, "message": str(exc)}
except Exception as exc:
    out = {"raised": False, "other": type(exc).__name__}
print(json.dumps(out))
"""
    data = run_py(ws, code)
    if not isinstance(data, dict):
        return False
    return data.get("raised") is True and data.get("message") == "sample is missing a metric name"


def check_r9(ws):
    # rollup lists metric names in ascending alphabetical order (stated in
    # docs/aggregation.md, Rollup).
    code = """
import json
from pulsemetrics.rollup import rollup
result = rollup([
    {"metric": "mem", "value": 1.0},
    {"metric": "cpu", "value": 2.0},
    {"metric": "disk", "value": 3.0},
])
print(json.dumps({"order": list(result.keys())}))
"""
    data = run_py(ws, code)
    return isinstance(data, dict) and data.get("order") == ["cpu", "disk", "mem"]


def check_r10(ws):
    # parse_line strips leading and trailing whitespace before splitting:
    # "  cpu.load 1.5 " parses to metric cpu.load, value 1.5, weight None
    # (example given in CHANGELOG.md, Unreleased).
    code = """
import json
from pulsemetrics.samples import parse_line
try:
    out = {"ok": True, "sample": parse_line("  cpu.load 1.5 ")}
except Exception as exc:
    out = {"ok": False, "error": type(exc).__name__}
print(json.dumps(out))
"""
    data = run_py(ws, code)
    if not isinstance(data, dict) or data.get("ok") is not True:
        return False
    sample = data.get("sample")
    if not isinstance(sample, dict):
        return False
    return (
        sample.get("metric") == "cpu.load"
        and close(sample.get("value"), 1.5)
        and sample.get("weight") is None
    )


def check_g1(ws):
    # Regression: count/min/max semantics and the plain mean of unweighted
    # samples are unchanged.
    code = """
import json
from pulsemetrics.rollup import rollup
result = rollup([
    {"metric": "cpu", "value": 1.0},
    {"metric": "cpu", "value": 3.0},
    {"metric": "mem", "value": 2.0},
])
print(json.dumps({"cpu": result["cpu"], "mem": result["mem"]}))
"""
    data = run_py(ws, code)
    if not isinstance(data, dict):
        return False
    try:
        cpu, mem = data["cpu"], data["mem"]
        return (
            cpu["count"] == 2
            and close(cpu["min"], 1.0)
            and close(cpu["max"], 3.0)
            and close(cpu["mean"], 2.0)
            and mem["count"] == 1
            and close(mem["mean"], 2.0)
        )
    except (KeyError, TypeError):
        return False


def check_g2(ws):
    # Regression: the end-to-end example still runs and reports cpu.load.
    env = dict(os.environ)
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    script = os.path.join(ws, "examples", "basic.py")
    with tempfile.TemporaryDirectory() as td:
        try:
            proc = subprocess.run(
                [sys.executable, script],
                cwd=td,
                env=env,
                capture_output=True,
                text=True,
                timeout=TIMEOUT,
            )
        except (subprocess.TimeoutExpired, OSError):
            return False
    return proc.returncode == 0 and "cpu.load" in proc.stdout


def main():
    if len(sys.argv) != 2:
        print(json.dumps({"error": "usage: check.py <workspace>"}))
        sys.exit(2)
    ws = os.path.abspath(sys.argv[1])

    requirements = {
        "R1": check_r1(ws),
        "R2": check_r2(ws),
        "R3": check_r3(ws),
        "R4": check_r4(ws),
        "R5": check_r5(ws),
        "R6": check_r6(ws),
        "R7": check_r7(ws),
        "R8": check_r8(ws),
        "R9": check_r9(ws),
        "R10": check_r10(ws),
    }
    regressions = {
        "G1": check_g1(ws),
        "G2": check_g2(ws),
    }
    resolved = all(requirements.values()) and all(regressions.values())
    print(json.dumps({
        "requirements": requirements,
        "regressions": regressions,
        "resolved": resolved,
    }))


if __name__ == "__main__":
    main()
