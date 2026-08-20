#!/usr/bin/env python3
"""Checker for factory task 06: recval `summarize` subcommand.

Usage: python3 check.py /path/to/workspace

Runs from outside the workspace and writes nothing into it. Every value
asserted below is stated verbatim in the workspace's public files
(README.md, docs/cli.md, CHANGELOG.md, examples/README.md), tagged
FAC06-1 .. FAC06-10 and routed from public/.issue-contract.md.
Output: canonical JSON on stdout:
  {"requirements": {"R1": bool, ...}, "regressions": {...}, "resolved": bool}
"""
import json
import os
import subprocess
import sys
import tempfile

TIMEOUT = 120

# FAC06-2 / FAC06-6 (docs/cli.md, examples/README.md)
EXPECTED_SUMMARY = {
    "total": 6,
    "valid": 4,
    "invalid": 2,
    "errors_by_field": {"age": 1, "name": 1},
}
# FAC06-5 (README.md)
EMPTY_SUMMARY = {"total": 0, "valid": 0, "invalid": 0, "errors_by_field": {}}
# FAC06-3 (docs/cli.md)
HELP_SENTENCE = "Summarize validation results as machine-readable JSON counts."
# FAC06-1 (docs/cli.md)
SUMMARY_KEYS = {"total", "valid", "invalid", "errors_by_field"}


def run(workspace, args):
    """Run one python subprocess with cwd=workspace; never writes .pyc."""
    env = dict(os.environ)
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    return subprocess.run(
        [sys.executable] + args,
        cwd=workspace,
        env=env,
        capture_output=True,
        text=True,
        timeout=TIMEOUT,
    )


def read_text(workspace, rel):
    path = os.path.join(workspace, rel)
    try:
        with open(path, encoding="utf-8") as fh:
            return fh.read()
    except OSError:
        return None


def parse_json(text):
    try:
        return json.loads(text)
    except (TypeError, ValueError):
        return None


def main():
    if len(sys.argv) != 2:
        print("usage: check.py WORKSPACE", file=sys.stderr)
        return 2
    workspace = os.path.abspath(sys.argv[1])
    rules = os.path.join("examples", "rules.json")
    records = os.path.join("examples", "records.jsonl")
    valid_only = os.path.join("examples", "valid_only.jsonl")

    requirements = {}
    regressions = {}

    def check(table, key, fn):
        try:
            table[key] = bool(fn())
        except Exception:
            table[key] = False

    # R1 (FAC06-1): summarize runs on the documented example, exits 0,
    # prints a JSON object with exactly the four documented keys.
    def r1():
        proc = run(workspace, ["-m", "recval", "summarize", rules, records])
        if proc.returncode != 0:
            return False
        data = parse_json(proc.stdout)
        return isinstance(data, dict) and set(data) == SUMMARY_KEYS

    # R2 (FAC06-2): the printed summary equals the documented object
    # (semantic JSON comparison).
    def r2():
        proc = run(workspace, ["-m", "recval", "summarize", rules, records])
        return (
            proc.returncode == 0
            and parse_json(proc.stdout) == EXPECTED_SUMMARY
        )

    # R3 (FAC06-3): summarize --help exits 0 and contains the documented
    # sentence verbatim.
    def r3():
        proc = run(workspace, ["-m", "recval", "summarize", "--help"])
        return proc.returncode == 0 and HELP_SENTENCE in proc.stdout

    # R4 (FAC06-4): missing records file -> exit 2 and the documented
    # stderr message including the path.
    def r4():
        with tempfile.TemporaryDirectory() as tmp:
            missing = os.path.join(tmp, "missing_records.jsonl")
            proc = run(workspace, ["-m", "recval", "summarize", rules, missing])
            return (
                proc.returncode == 2
                and "error: records file not found:" in proc.stderr
                and missing in proc.stderr
            )

    # R5 (FAC06-5): empty (zero-byte) records file -> zero summary, exit 0.
    def r5():
        with tempfile.TemporaryDirectory() as tmp:
            empty = os.path.join(tmp, "empty.jsonl")
            with open(empty, "w", encoding="utf-8"):
                pass
            proc = run(workspace, ["-m", "recval", "summarize", rules, empty])
            return (
                proc.returncode == 0
                and parse_json(proc.stdout) == EMPTY_SUMMARY
            )

    # R6 (FAC06-6): examples/summary.json holds exactly the documented
    # summary object (semantic JSON comparison).
    def r6():
        text = read_text(workspace, os.path.join("examples", "summary.json"))
        return parse_json(text) == EXPECTED_SUMMARY

    # R7 (FAC06-7): CHANGELOG.md gained the documented section and bullet.
    def r7():
        text = read_text(workspace, "CHANGELOG.md")
        return (
            text is not None
            and "## 0.3.0" in text
            and "- Added the summarize subcommand." in text
        )

    # R8 (FAC06-8): README.md Defaults list gained the documented line.
    def r8():
        text = read_text(workspace, "README.md")
        return text is not None and "Default summary indent: 2 spaces." in text

    # R9 (FAC06-9): version bumped; --version prints exactly the
    # documented string.
    def r9():
        proc = run(workspace, ["-m", "recval", "--version"])
        return proc.returncode == 0 and proc.stdout.strip() == "recval 0.3.0"

    # R10 (FAC06-10): tests/test_summarize.py exists; the discovered
    # suite passes and mentions test_summarize.
    def r10():
        if not os.path.isfile(
            os.path.join(workspace, "tests", "test_summarize.py")
        ):
            return False
        proc = run(workspace, ["-m", "unittest", "discover", "-s", "tests", "-v"])
        return (
            proc.returncode == 0
            and "test_summarize" in (proc.stdout + proc.stderr)
        )

    # G1: documented validate behaviour on examples/records.jsonl
    # (exit 1 plus the two documented error lines).
    def g1():
        proc = run(workspace, ["-m", "recval", "validate", rules, records])
        return (
            proc.returncode == 1
            and "record 3: name: missing required key" in proc.stdout
            and "record 5: age: out of range 0..130" in proc.stdout
        )

    # G2: documented validate behaviour on all-valid input (prints ok,
    # exit 0).
    def g2():
        proc = run(workspace, ["-m", "recval", "validate", rules, valid_only])
        return proc.returncode == 0 and proc.stdout.strip() == "ok"

    check(requirements, "R1", r1)
    check(requirements, "R2", r2)
    check(requirements, "R3", r3)
    check(requirements, "R4", r4)
    check(requirements, "R5", r5)
    check(requirements, "R6", r6)
    check(requirements, "R7", r7)
    check(requirements, "R8", r8)
    check(requirements, "R9", r9)
    check(requirements, "R10", r10)
    check(regressions, "G1", g1)
    check(regressions, "G2", g2)

    resolved = all(requirements.values()) and all(regressions.values())
    print(
        json.dumps(
            {
                "requirements": requirements,
                "regressions": regressions,
                "resolved": resolved,
            }
        )
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
