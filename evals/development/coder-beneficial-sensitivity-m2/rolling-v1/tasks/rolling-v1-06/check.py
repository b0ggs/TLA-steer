#!/usr/bin/env python3
"""Checker for issue TRIAL-B (logscan `stats` subcommand).

Usage: python3 check.py /path/to/workspace

Runs outside the workspace. Every assertion below corresponds verbatim to a
requirement stated in the workspace's public files (.issue-contract.md,
README.md, docs/cli.md, CHANGELOG.md, examples/README.md). Emits canonical
JSON on stdout:

    {"requirements": {"R1": bool, ...}, "regressions": {...}, "resolved": bool}
"""

import ast
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile

TIMEOUT = 60
TASK_ID = "rolling-v1-06"
LEVELS = ("DEBUG", "INFO", "WARNING", "ERROR")

BASE_FILES = {
    ".issue-contract.md",
    "CHANGELOG.md",
    "CODER.md",
    "README.md",
    "docs/cli.md",
    "examples/README.md",
    "examples/sample.log",
    "logscan/__init__.py",
    "logscan/__main__.py",
    "logscan/cli.py",
    "logscan/parser.py",
    "tests/__init__.py",
    "tests/test_cli.py",
    "tests/test_parser.py",
}
PUBLIC_ADDITIONS = {"examples/stats_example.txt", "tests/test_stats.py"}
PROTECTED_SHA256 = {
    ".issue-contract.md": "b635696cfd5357d3cf50503aefb98fa905246cef61a072985f8f9de1a71c74c3",
    "CODER.md": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    "examples/README.md": "da59fee944b832a4d1ea1039bacb6db335779c2d9d0d2a13a86489b6d7a981c0",
    "examples/sample.log": "81e46dc1c23d192b252dc4e1bf2c502f80604be4ce9f9717a088b58709c5f02f",
    "logscan/__main__.py": "f28681367298d9f345f92a785d158eeb9289059bc068d62e45f83afae31237b5",
    "tests/__init__.py": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    "tests/test_cli.py": "c459f7a651acbdb9cad8874ce7c2d7452af263eef73ce54b0b905476cc25b0ec",
    "tests/test_parser.py": "402ab89f12719b545db5f6141a4020efc6ee71293a9bc7d9e211fa5bccedff99",
}

# Checker-owned fixtures (written to a temp dir OUTSIDE the workspace).
BASIC = (
    "INFO alpha\n"
    "ERROR beta\n"
    "INFO alpha\n"
    "junk line\n"
    "WARNING gamma delta\n"
    "INFO omega\n"
    "\n"
    "DEBUG zeta\n"
)
TIES = "INFO bb\nINFO aa\nINFO bb\nINFO cc\nINFO aa\nINFO dd\n"
COUNT_FIXTURE = "INFO a\nnope\nERROR b\nDEBUG c\n"

# Stated verbatim in docs/cli.md (TRIAL-B-EMPTY).
EMPTY_SUMMARY = {"total": 0, "by_level": {}, "unique_messages": 0, "top_messages": []}
# Stated in .issue-contract.md ("exactly these four keys").
KEYS = {"total", "by_level", "unique_messages", "top_messages"}
# Stated verbatim in docs/cli.md (TRIAL-B-HELP).
HELP_SENTENCE = "Compute aggregate statistics for a log file."
# Stated verbatim in CHANGELOG.md (TRIAL-B-VERSION).
VERSION_LINE = "logscan 1.3.0"
HEADING_LINE = "## 1.3.0"
# Stated verbatim in README.md (TRIAL-B-DEFAULTS).
README_LINE = "Default for `stats --top`: 3"


def assertion(function):
    try:
        function()
        return {"passed": True, "details": "objective assertion passed"}
    except Exception as exc:
        return {"passed": False, "details": f"{type(exc).__name__}: {exc}"}


def require(condition, message):
    if not condition:
        raise AssertionError(message)


def run(ws, args, timeout=TIMEOUT):
    """Run `python <args>` with cwd=workspace in a fresh subprocess."""
    env = dict(os.environ)
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    try:
        return subprocess.run(
            [sys.executable] + args,
            cwd=ws,
            capture_output=True,
            text=True,
            timeout=timeout,
            env=env,
        )
    except (subprocess.TimeoutExpired, OSError):
        return None


def parse_records(text):
    """Record rules exactly as stated in .issue-contract.md item 1."""
    records = []
    for raw in text.splitlines():
        line = raw.strip()
        if not line:
            continue
        parts = line.split(" ", 1)
        if len(parts) == 2 and parts[0] in LEVELS and parts[1]:
            records.append((parts[0], parts[1]))
    return records


def summarize(records, top=3):
    """Payload rules exactly as stated in .issue-contract.md item 2/4."""
    by_level = {}
    msg = {}
    for level, message in records:
        by_level[level] = by_level.get(level, 0) + 1
        msg[message] = msg.get(message, 0) + 1
    return {
        "total": len(records),
        "by_level": by_level,
        "unique_messages": len(msg),
        "top_messages": sorted(msg, key=lambda m: (-msg[m], m))[:top],
    }


def stats_json(ws, path, extra=()):
    """Run `python -m logscan stats <path> [extra]`; return dict or None."""
    r = run(ws, ["-m", "logscan", "stats", path] + list(extra))
    if r is None or r.returncode != 0:
        return None
    try:
        data = json.loads(r.stdout)
    except ValueError:
        return None
    return data if isinstance(data, dict) else None


def read_lines(ws, relpath):
    try:
        with open(os.path.join(ws, relpath), "r", encoding="utf-8") as fh:
            return fh.read().splitlines()
    except OSError:
        return None


def main():
    if len(sys.argv) != 2:
        print("usage: check.py WORKSPACE", file=sys.stderr)
        sys.exit(2)
    ws = os.path.abspath(sys.argv[1])

    def environment_check():
        actual = set()
        for directory, dirs, files in os.walk(ws):
            dirs[:] = sorted(d for d in dirs if d not in {".git", "__pycache__"})
            for name in files:
                path = os.path.join(directory, name)
                relative = os.path.relpath(path, ws).replace(os.sep, "/")
                if "__pycache__" in relative.split("/") or relative.endswith((".pyc", ".pyo")):
                    continue
                actual.add(relative)
        require(BASE_FILES <= actual, "a baseline public path is missing")
        for relative in actual - BASE_FILES:
            parts = relative.split("/")
            allowed_source = (
                len(parts) == 2
                and parts[0] == "logscan"
                and parts[1].endswith(".py")
                and not parts[1].startswith(".")
            )
            require(relative in PUBLIC_ADDITIONS or allowed_source, f"unexpected path: {relative}")

    def integrity_check():
        for relative, expected in PROTECTED_SHA256.items():
            path = os.path.join(ws, relative)
            with open(path, "rb") as source:
                actual = hashlib.sha256(source.read()).hexdigest()
            require(actual == expected, f"protected path changed: {relative}")
        with open(os.path.join(ws, "CODER.md"), "rb") as source:
            require(source.read() == b"", "CODER.md is not zero-byte")

    environment = assertion(environment_check)
    integrity = assertion(integrity_check)

    tmp = tempfile.mkdtemp(prefix="trialb-fixtures-")

    def fixture(name, content):
        p = os.path.join(tmp, name)
        with open(p, "w", encoding="utf-8") as fh:
            fh.write(content)
        return p

    basic_log = fixture("basic.log", BASIC)
    ties_log = fixture("ties.log", TIES)
    empty_log = fixture("empty.log", "")
    count_log = fixture("count.log", COUNT_FIXTURE)
    missing_log = os.path.join(tmp, "does-not-exist.log")

    requirements = {}
    regressions = {}

    def req(key, fn):
        requirements[key] = assertion(lambda: require(fn(), f"{key} failed"))

    def reg(key, fn):
        regressions[key] = assertion(lambda: require(fn(), f"{key} failed"))

    # R1 — contract items 1-3: stats exits 0, prints one JSON object with
    # exactly the four stated keys and correct total/by_level/unique_messages.
    def r1():
        data = stats_json(ws, basic_log)
        if data is None or set(data.keys()) != KEYS:
            return False
        exp = summarize(parse_records(BASIC))
        return (
            type(data["total"]) is int
            and data["total"] == exp["total"]
            and type(data["by_level"]) is dict
            and all(type(key) is str and type(value) is int for key, value in data["by_level"].items())
            and data["by_level"] == exp["by_level"]
            and type(data["unique_messages"]) is int
            and data["unique_messages"] == exp["unique_messages"]
            and type(data["top_messages"]) is list
        )

    req("R1", r1)

    # R2 — contract items 2/4: top_messages ordering (descending count, ties
    # by ascending lexicographic order), --top N honored, default --top is 3.
    def r2():
        default = stats_json(ws, ties_log)
        top2 = stats_json(ws, ties_log, ["--top", "2"])
        top10 = stats_json(ws, ties_log, ["--top", "10"])
        if default is None or top2 is None or top10 is None:
            return False
        return (
            type(default.get("top_messages")) is list
            and default["top_messages"] == ["aa", "bb", "cc"]
            and type(top2.get("top_messages")) is list
            and top2["top_messages"] == ["aa", "bb"]
            and type(top10.get("top_messages")) is list
            and top10["top_messages"] == ["aa", "bb", "cc", "dd"]
        )

    req("R2", r2)

    # R3 — docs/cli.md TRIAL-B-HELP: `stats --help` includes the exact sentence.
    def r3():
        r = run(ws, ["-m", "logscan", "stats", "--help"])
        return r is not None and r.returncode == 0 and HELP_SENTENCE in r.stdout

    req("R3", r3)

    # R4 — docs/cli.md TRIAL-B-MISSING: missing file -> stated stderr message,
    # exit code 3.
    def r4():
        r = run(ws, ["-m", "logscan", "stats", missing_log])
        expected = "logscan: error: no such file: " + missing_log + "\n"
        return r is not None and (r.returncode, r.stdout, r.stderr) == (3, "", expected)

    req("R4", r4)

    # R5 — docs/cli.md TRIAL-B-EMPTY: empty file -> stated JSON, exit 0.
    def r5():
        data = stats_json(ws, empty_log)
        return (
            data == EMPTY_SUMMARY
            and type(data) is dict
            and type(data["total"]) is int
            and type(data["by_level"]) is dict
            and type(data["unique_messages"]) is int
            and type(data["top_messages"]) is list
        )

    req("R5", r5)

    # R6 — docs/cli.md TRIAL-B-PARSER: count_levels([]) returns {}.
    def r6():
        code = (
            "from logscan import parser\n"
            "result = parser.count_levels([])\n"
            "assert type(result) is dict and result == {}\n"
            "print('ok')\n"
        )
        r = run(ws, ["-c", code])
        return r is not None and (r.returncode, r.stdout, r.stderr) == (0, "ok\n", "")

    req("R6", r6)

    # R7 — CHANGELOG.md TRIAL-B-VERSION: `--version` prints exactly
    # "logscan 1.3.0".
    def r7():
        r = run(ws, ["-m", "logscan", "--version"])
        return r is not None and (r.returncode, r.stdout, r.stderr) == (0, VERSION_LINE + "\n", "")

    req("R7", r7)

    # R8 — CHANGELOG.md TRIAL-B-VERSION: new section whose heading line is
    # exactly "## 1.3.0".
    def r8():
        lines = read_lines(ws, "CHANGELOG.md")
        if lines is None:
            return False
        headings = [index for index, line in enumerate(lines) if line == HEADING_LINE]
        if len(headings) != 1:
            return False
        start = headings[0] + 1
        end = next((index for index in range(start, len(lines)) if lines[index].startswith("## ")), len(lines))
        return any(
            line.startswith(("- ", "* ", "+ ")) and re.search(r"\bstats\b", line, re.IGNORECASE)
            for line in lines[start:end]
        )

    req("R8", r8)

    # R9 — README.md TRIAL-B-DEFAULTS: exact line present in README.md.
    def r9():
        lines = read_lines(ws, "README.md")
        if lines is None:
            return False
        headings = [index for index, line in enumerate(lines) if line == "## Defaults"]
        if len(headings) != 1:
            return False
        start = headings[0] + 1
        end = next((index for index in range(start, len(lines)) if lines[index].startswith("## ")), len(lines))
        nonempty = [line for line in lines[start:end] if line]
        return bool(nonempty) and nonempty[-1] == README_LINE

    req("R9", r9)

    # R10 — examples/README.md TRIAL-B-EXAMPLE: examples/stats_example.txt is
    # JSON-equivalent to the live output of
    # `python -m logscan stats examples/sample.log` run from the repo root.
    def r10():
        example_path = os.path.join(ws, "examples", "stats_example.txt")
        if not os.path.isfile(example_path):
            return False
        r = run(ws, ["-m", "logscan", "stats", os.path.join("examples", "sample.log")])
        if r is None or r.returncode != 0:
            return False
        with open(example_path, "r", encoding="utf-8") as fh:
            file_data = json.loads(fh.read())
        live_data = json.loads(r.stdout)
        return type(file_data) is dict and type(live_data) is dict and file_data == live_data

    req("R10", r10)

    # R11 — README.md TRIAL-B-TESTS: tests/test_stats.py exists,
    # `python -m unittest tests.test_stats` passes and runs at least one test.
    def r11():
        test_path = os.path.join(ws, "tests", "test_stats.py")
        if not os.path.isfile(test_path):
            return False
        with open(test_path, "r", encoding="utf-8") as source:
            tree = ast.parse(source.read(), filename=test_path)
        unittest_names = {"unittest"}
        testcase_names = {"TestCase"}
        for node in tree.body:
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name == "unittest":
                        unittest_names.add(alias.asname or alias.name)
            elif isinstance(node, ast.ImportFrom) and node.module == "unittest":
                for alias in node.names:
                    if alias.name == "TestCase":
                        testcase_names.add(alias.asname or alias.name)

        def is_testcase_base(node):
            return (
                isinstance(node, ast.Name)
                and node.id in testcase_names
            ) or (
                isinstance(node, ast.Attribute)
                and node.attr == "TestCase"
                and isinstance(node.value, ast.Name)
                and node.value.id in unittest_names
            )

        has_case = any(
            any(is_testcase_base(base) for base in node.bases)
            and any(
                isinstance(member, (ast.FunctionDef, ast.AsyncFunctionDef))
                and member.name.startswith("test")
                for member in node.body
            )
            for node in tree.body
            if isinstance(node, ast.ClassDef)
        )
        if not has_case:
            return False
        r = run(ws, ["-m", "unittest", "tests.test_stats", "-v"])
        if r is None or r.returncode != 0:
            return False
        combined = r.stdout + r.stderr
        match = re.search(r"\bRan ([0-9]+) tests?\b", combined)
        return match is not None and int(match.group(1)) >= 1

    req("R11", r11)

    # G1 — contract: existing `count` subcommand keeps working unchanged.
    def g1():
        r = run(ws, ["-m", "logscan", "count", count_log])
        return r is not None and (r.returncode, r.stdout, r.stderr) == (0, "3\n", "")

    reg("G1", g1)

    # G2 — contract: existing tests keep passing.
    def g2():
        r = run(ws, ["-m", "unittest", "tests.test_parser", "tests.test_cli"])
        return r is not None and r.returncode == 0

    reg("G2", g2)

    resolved = (
        environment["passed"]
        and integrity["passed"]
        and all(item["passed"] for item in requirements.values())
        and all(item["passed"] for item in regressions.values())
    )
    result = {
        "environment": environment,
        "integrity": integrity,
        "regressions": regressions,
        "requirements": requirements,
        "resolved": resolved,
        "schema": "scout-check-result-v1",
        "task_id": TASK_ID,
    }
    shutil.rmtree(tmp)
    print(
        json.dumps(
            result,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )
    )


if __name__ == "__main__":
    main()
