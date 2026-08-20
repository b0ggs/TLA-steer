#!/usr/bin/env python3
"""Checker for trial task A (durafmt bug-fix).

Usage: python check.py <workspace-path>

Runs each requirement in an isolated subprocess against the workspace and
emits canonical JSON:
  {"requirements": {"R1": bool, ...}, "regressions": {"G1": bool, ...},
   "resolved": bool}

Every asserted value, path, message string, and format below is stated
verbatim in the workspace's public files (.issue-contract.md, README.md,
docs/upgrading.md, CHANGELOG.md, examples/basic.py, tests/test_public.py).
Stdlib only; read-only with respect to the workspace (PYTHONDONTWRITEBYTECODE
prevents bytecode being written into the scanned tree).
"""

import json
import os
import re
import subprocess
import sys

TIMEOUT = 60


def _env(workspace):
    env = dict(os.environ)
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    env["PYTHONPATH"] = workspace
    return env


def _run(workspace, argv):
    """Run a python subprocess in the workspace; return CompletedProcess or None."""
    try:
        return subprocess.run(
            [sys.executable, "-B"] + argv,
            cwd=workspace,
            env=_env(workspace),
            capture_output=True,
            text=True,
            timeout=TIMEOUT,
        )
    except (subprocess.TimeoutExpired, OSError):
        return None


def run_code(workspace, code):
    proc = _run(workspace, ["-c", code])
    return proc is not None and proc.returncode == 0


def read_text(workspace, rel):
    try:
        with open(os.path.join(workspace, rel), encoding="utf-8") as fh:
            return fh.read()
    except (OSError, UnicodeDecodeError):
        return None


# --- Requirements -----------------------------------------------------------

def r1_minute_fix(ws):
    # .issue-contract.md (TRIAL-A-1): parse("90m") == 5400, parse("1h30m") == 5400
    return run_code(ws, (
        "import durafmt\n"
        "assert durafmt.parse('90m') == 5400\n"
        "assert durafmt.parse('1h30m') == 5400\n"
    ))


def r2_empty_message(ws):
    # docs/upgrading.md (TRIAL-A-2): parse("") raises ValueError('empty duration string')
    return run_code(ws, (
        "import durafmt\n"
        "try:\n"
        "    durafmt.parse('')\n"
        "except ValueError as exc:\n"
        "    assert str(exc) == 'empty duration string', str(exc)\n"
        "else:\n"
        "    raise AssertionError('no ValueError raised')\n"
    ))


def r3_zero_format(ws):
    # docs/upgrading.md (TRIAL-A-3): format_duration(0) == "0s"
    return run_code(ws, (
        "import durafmt\n"
        "assert durafmt.format_duration(0) == '0s'\n"
    ))


def r4_docstring(ws):
    # docs/upgrading.md (TRIAL-A-4): docstring contains the exact sentence.
    return run_code(ws, (
        "from durafmt import formatter\n"
        "doc = formatter.format_duration.__doc__ or ''\n"
        "assert 'Returns \"0s\" for a zero duration.' in doc\n"
    ))


def r5_precision(ws):
    # docs/upgrading.md (TRIAL-A-5): DEFAULT_PRECISION changed from 2 to 3.
    return run_code(ws, (
        "from durafmt import config\n"
        "assert config.DEFAULT_PRECISION == 3\n"
    ))


def r6_version(ws):
    # docs/upgrading.md (TRIAL-A-6): __version__ bumped to "1.2.1".
    return run_code(ws, (
        "import durafmt\n"
        "assert durafmt.__version__ == '1.2.1'\n"
    ))


def r7_changelog(ws):
    # docs/upgrading.md (TRIAL-A-7): CHANGELOG.md gains exactly these two lines.
    text = read_text(ws, "CHANGELOG.md")
    if text is None:
        return False
    lines = [line.strip() for line in text.splitlines()]
    return (
        "## [1.2.1] - Unreleased" in lines
        and "- Fixed: minute multiplier in the duration parser (TRIAL-A-7)" in lines
    )


def r8_readme(ws):
    # docs/upgrading.md (TRIAL-A-8): README example shows 5400; 4500 gone.
    text = read_text(ws, "README.md")
    if text is None:
        return False
    snippet = re.search(r'>>> durafmt\.parse\("90m"\)\s*\n\s*5400\b', text)
    return snippet is not None and "4500" not in text


def r9_example(ws):
    # docs/upgrading.md (TRIAL-A-9): examples/basic.py exits 0, prints exactly
    # one line: total: 5400
    proc = _run(ws, ["examples/basic.py"])
    return (
        proc is not None
        and proc.returncode == 0
        and proc.stdout.strip() == "total: 5400"
    )


def r10_new_test(ws):
    # docs/upgrading.md (TRIAL-A-10): the named unittest exists and passes.
    proc = _run(ws, ["-m", "unittest", "tests.test_public.TestParse.test_parse_days"])
    return proc is not None and proc.returncode == 0


# --- Regressions (behaviour that must keep working) -------------------------

def g1_parse_regressions(ws):
    # .issue-contract.md: parse("1h") == 3600 and parse("45s") == 45
    return run_code(ws, (
        "import durafmt\n"
        "assert durafmt.parse('1h') == 3600\n"
        "assert durafmt.parse('45s') == 45\n"
    ))


def g2_format_regression(ws):
    # .issue-contract.md: format_duration(3661) == "1h 1m 1s"
    return run_code(ws, (
        "import durafmt\n"
        "assert durafmt.format_duration(3661) == '1h 1m 1s'\n"
    ))


REQUIREMENTS = [
    ("R1", r1_minute_fix),
    ("R2", r2_empty_message),
    ("R3", r3_zero_format),
    ("R4", r4_docstring),
    ("R5", r5_precision),
    ("R6", r6_version),
    ("R7", r7_changelog),
    ("R8", r8_readme),
    ("R9", r9_example),
    ("R10", r10_new_test),
]

REGRESSIONS = [
    ("G1", g1_parse_regressions),
    ("G2", g2_format_regression),
]


def main():
    if len(sys.argv) != 2:
        print("usage: check.py <workspace-path>", file=sys.stderr)
        return 2
    workspace = os.path.abspath(sys.argv[1])
    if not os.path.isdir(workspace):
        print(f"not a directory: {workspace}", file=sys.stderr)
        return 2

    requirements = {}
    for key, fn in REQUIREMENTS:
        try:
            requirements[key] = bool(fn(workspace))
        except Exception:
            requirements[key] = False

    regressions = {}
    for key, fn in REGRESSIONS:
        try:
            regressions[key] = bool(fn(workspace))
        except Exception:
            regressions[key] = False

    resolved = all(requirements.values()) and all(regressions.values())
    print(json.dumps(
        {"requirements": requirements, "regressions": regressions,
         "resolved": resolved},
    ))
    return 0


if __name__ == "__main__":
    sys.exit(main())
