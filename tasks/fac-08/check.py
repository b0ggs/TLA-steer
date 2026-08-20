#!/usr/bin/env python3
"""Checker for the pathsieve bug-fix task.

Usage: python3 check.py <workspace-path>

Runs entirely outside the workspace and writes nothing into it. One
subprocess per requirement; every asserted value is stated verbatim in
the workspace's public documentation (README.md, docs/patterns.md,
CHANGELOG.md, .issue-contract.md, tests/).
"""

import json
import os
import subprocess
import sys
import tempfile

TIMEOUT = 120


def run_snippet(ws, code):
    """Run *code* in a fresh interpreter with the workspace importable."""
    env = dict(os.environ)
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    env["PYTHONPATH"] = ws
    try:
        with tempfile.TemporaryDirectory() as tmp:
            proc = subprocess.run(
                [sys.executable, "-c", code],
                cwd=tmp,
                env=env,
                capture_output=True,
                text=True,
                timeout=TIMEOUT,
            )
    except (subprocess.TimeoutExpired, OSError):
        return False
    return proc.returncode == 0 and proc.stdout.strip().endswith("PASS")


def run_unittest_discover(ws):
    """Run the workspace's own test suite (regression G2)."""
    env = dict(os.environ)
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    try:
        with tempfile.TemporaryDirectory() as tmp:
            proc = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "unittest",
                    "discover",
                    "-s",
                    os.path.join(ws, "tests"),
                    "-t",
                    ws,
                ],
                cwd=tmp,
                env=env,
                capture_output=True,
                text=True,
                timeout=TIMEOUT,
            )
    except (subprocess.TimeoutExpired, OSError):
        return False
    return proc.returncode == 0


# R1 -- issue contract: last matching rule wins; negation re-includes.
R1 = """
from pathsieve import Sieve
s = Sieve(["build", "!keep.txt"])
assert s.excludes("build/keep.txt") is False
assert s.excludes("build/other.txt") is True
print("PASS")
"""

# R2 -- CHANGELOG.md: exact bullet under the Unreleased heading.
R2 = """
import io
ws = {ws!r}
with io.open(ws + "/CHANGELOG.md", encoding="utf-8") as fh:
    text = fh.read()
target = "- Fixed: negation patterns now re-include previously excluded paths."
in_unreleased = False
found = False
for line in text.splitlines():
    stripped = line.strip()
    if stripped.startswith("## "):
        in_unreleased = stripped[3:].strip().lower() == "unreleased"
        continue
    if in_unreleased and stripped == target:
        found = True
assert found
print("PASS")
"""

# R3 -- CHANGELOG.md: version bump to 0.4.1.
R3 = """
import pathsieve
assert pathsieve.__version__ == "0.4.1"
print("PASS")
"""

# R4 -- docs/patterns.md: lone "!" raises PatternError with exact message.
R4 = """
from pathsieve.errors import PatternError
from pathsieve.patterns import compile_pattern
try:
    compile_pattern("!")
except PatternError as exc:
    assert str(exc) == "negation requires a pattern body"
    print("PASS")
"""

# R5 -- docs/patterns.md: indented comment lines produce no rule.
R5 = """
from pathsieve.loader import load_text
rules = load_text("   # secret\\n\\t# tab comment\\n*.log\\n")
assert len(rules) == 1
print("PASS")
"""

# R6 -- docs/patterns.md: Sieve.decide docstring contains the sentence.
R6 = """
from pathsieve import Sieve
doc = Sieve.decide.__doc__ or ""
assert "The last matching rule wins." in doc
print("PASS")
"""

# R7 -- tests/test_engine.py comment: add test_negation_reinclude there.
R7 = """
import importlib.util
import inspect
import unittest
ws = {ws!r}
spec = importlib.util.spec_from_file_location(
    "ps_check_test_engine", ws + "/tests/test_engine.py")
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
ran = False
ok = True
for obj in vars(mod).values():
    if inspect.isclass(obj) and issubclass(obj, unittest.TestCase):
        if "test_negation_reinclude" in dir(obj):
            case = obj("test_negation_reinclude")
            result = unittest.TestResult()
            case.run(result)
            ran = True
            ok = ok and result.wasSuccessful()
if not ran:
    func = getattr(mod, "test_negation_reinclude", None)
    if callable(func):
        func()
        ran = True
assert ran and ok
print("PASS")
"""

# R8 -- docs/patterns.md: ignore_case defaults to False; True ignores case.
R8 = """
import inspect
from pathsieve import Sieve
default = inspect.signature(Sieve.__init__).parameters["ignore_case"].default
assert default is False
assert Sieve(["*.PY"]).excludes("main.py") is False
assert Sieve(["*.PY"], ignore_case=True).excludes("main.py") is True
print("PASS")
"""

# R9 -- README.md: filter_paths preserves input order.
R9 = """
from pathsieve import filter_paths
out = filter_paths(["zeta.txt", "app.log", "alpha.txt"], ["*.log"])
assert out == ["zeta.txt", "alpha.txt"]
print("PASS")
"""

# R10 -- README.md: PatternError importable from the package root.
R10 = """
from pathsieve import PatternError
from pathsieve.errors import PatternError as _inner
assert PatternError is _inner
print("PASS")
"""

# G1 -- regression: plain excludes keep working (README + docs examples).
G1 = """
from pathsieve import Sieve
s = Sieve(["*.log"])
assert s.excludes("app.log") is True
assert s.excludes("notes/app.log") is True
assert s.excludes("app.txt") is False
print("PASS")
"""


def main():
    if len(sys.argv) != 2:
        print(json.dumps({"error": "usage: check.py <workspace>"}))
        return 2
    ws = os.path.abspath(sys.argv[1])

    requirements = {}
    snippets = {
        "R1": R1,
        "R2": R2.format(ws=ws),
        "R3": R3,
        "R4": R4,
        "R5": R5,
        "R6": R6,
        "R7": R7.format(ws=ws),
        "R8": R8,
        "R9": R9,
        "R10": R10,
    }
    for key in ["R1", "R2", "R3", "R4", "R5", "R6", "R7", "R8", "R9", "R10"]:
        requirements[key] = run_snippet(ws, snippets[key])

    regressions = {
        "G1": run_snippet(ws, G1),
        "G2": run_unittest_discover(ws),
    }

    resolved = all(requirements.values()) and all(regressions.values())
    print(json.dumps(
        {
            "requirements": requirements,
            "regressions": regressions,
            "resolved": resolved,
        },
        sort_keys=False,
    ))
    return 0


if __name__ == "__main__":
    sys.exit(main())
