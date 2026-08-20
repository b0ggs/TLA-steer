#!/usr/bin/env python3
"""Checker for FAC04: tocsmith `json` subcommand (release 1.2.0).

Usage: python3 check.py /path/to/workspace

Runs from outside the workspace, writes nothing into it, stdlib only.
Every asserted value below is stated verbatim in the workspace's public
files (README.md, docs/cli.md, CHANGELOG.md, examples/README.md,
.issue-contract.md).
"""

import json
import os
import subprocess
import sys
import tempfile

TIMEOUT = 120

# FAC04-2 (docs/cli.md)
HELP_SENTENCE = "Emit the table of contents as JSON instead of Markdown."
# FAC04-7 (README.md)
DEFAULTS_LINE = "Default JSON indent: 2 spaces; encoding: UTF-8."
# FAC04-6 (CHANGELOG.md)
CHANGELOG_HEADING_PREFIX = "## 1.2.0"
CHANGELOG_BULLET = "- Added the `json` subcommand."
# FAC04-9 (CHANGELOG.md)
VERSION_OUTPUT = "tocsmith 1.2.0"
# FAC04-4 (docs/cli.md)
ERROR_PREFIX = "tocsmith: error: cannot read "
# FAC04-8 (README.md)
JSON_TEST_NAME = "test_json_entries_for_sample"

# FAC04-1 (docs/cli.md): exact entries for examples/sample.md.
EXPECTED_ENTRIES = [
    {"level": 1, "title": "Tocsmith Sample", "anchor": "tocsmith-sample", "line": 1},
    {"level": 2, "title": "Getting Started", "anchor": "getting-started", "line": 5},
    {"level": 3, "title": "Install", "anchor": "install", "line": 7},
    {"level": 2, "title": "Usage", "anchor": "usage", "line": 15},
    {"level": 3, "title": "Install", "anchor": "install-1", "line": 17},
]

# G1: public examples/sample-toc.md content, restated by docs/cli.md as the
# exact `generate` output for examples/sample.md.
EXPECTED_TOC = (
    "- [Tocsmith Sample](#tocsmith-sample)\n"
    "  - [Getting Started](#getting-started)\n"
    "    - [Install](#install)\n"
    "  - [Usage](#usage)\n"
    "    - [Install](#install-1)\n"
)


def run(workspace, args):
    env = dict(os.environ)
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    env["COLUMNS"] = "200"
    return subprocess.run(
        [sys.executable] + args,
        cwd=workspace,
        env=env,
        capture_output=True,
        text=True,
        timeout=TIMEOUT,
    )


def read_text(workspace, rel):
    with open(os.path.join(workspace, rel), "r", encoding="utf-8") as fh:
        return fh.read()


def check_r1(workspace, tmpdir):
    """json subcommand: exact documented output for examples/sample.md, exit 0."""
    proc = run(workspace, ["-m", "tocsmith", "json", "examples/sample.md"])
    expected = json.dumps(EXPECTED_ENTRIES, indent=2) + "\n"
    return proc.returncode == 0 and proc.stdout == expected


def check_r2(workspace, tmpdir):
    """json --help contains the verbatim help sentence."""
    proc = run(workspace, ["-m", "tocsmith", "json", "--help"])
    return proc.returncode == 0 and HELP_SENTENCE in proc.stdout


def check_r3(workspace, tmpdir):
    """No headings: prints [] plus newline, exits 3."""
    path = os.path.join(tmpdir, "no_headings.md")
    with open(path, "w", encoding="utf-8") as fh:
        fh.write("just prose\n\nno headings here\n")
    proc = run(workspace, ["-m", "tocsmith", "json", path])
    return proc.returncode == 3 and proc.stdout == "[]\n"


def check_r4(workspace, tmpdir):
    """Unreadable file: exit 2, stderr begins with the documented message."""
    path = os.path.join(tmpdir, "does-not-exist.md")
    proc = run(workspace, ["-m", "tocsmith", "json", path])
    return proc.returncode == 2 and ERROR_PREFIX in proc.stderr


def check_r5(workspace, tmpdir):
    """examples/outline.json parses to the documented entries."""
    parsed = json.loads(read_text(workspace, os.path.join("examples", "outline.json")))
    return parsed == EXPECTED_ENTRIES


def check_r6(workspace, tmpdir):
    """CHANGELOG.md gains the 1.2.0 section with the exact bullet."""
    lines = [line.strip() for line in read_text(workspace, "CHANGELOG.md").splitlines()]
    has_heading = any(line.startswith(CHANGELOG_HEADING_PREFIX) for line in lines)
    has_bullet = any(line == CHANGELOG_BULLET for line in lines)
    return has_heading and has_bullet


def check_r7(workspace, tmpdir):
    """README.md contains the verbatim defaults line."""
    lines = [line.strip() for line in read_text(workspace, "README.md").splitlines()]
    return any(line == DEFAULTS_LINE for line in lines)


def check_r8(workspace, tmpdir):
    """tests/test_json.py: named test runs and passes."""
    proc = run(
        workspace,
        ["-m", "unittest", "discover", "-s", "tests", "-p", "test_json*.py", "-v"],
    )
    output = proc.stdout + proc.stderr
    return (
        proc.returncode == 0
        and JSON_TEST_NAME in output
        and "Ran 0 tests" not in output
    )


def check_r9(workspace, tmpdir):
    """--version prints exactly tocsmith 1.2.0."""
    proc = run(workspace, ["-m", "tocsmith", "--version"])
    return proc.returncode == 0 and proc.stdout.strip() == VERSION_OUTPUT


def check_r10(workspace, tmpdir):
    """scan_text("") returns [] without raising."""
    code = "import tocsmith.scanner as s\nprint(s.scan_text('') == [])"
    proc = run(workspace, ["-c", code])
    return proc.returncode == 0 and proc.stdout.strip() == "True"


def check_g1(workspace, tmpdir):
    """generate output for examples/sample.md is unchanged."""
    proc = run(workspace, ["-m", "tocsmith", "generate", "examples/sample.md"])
    return proc.returncode == 0 and proc.stdout == EXPECTED_TOC


def check_g2(workspace, tmpdir):
    """Existing test_core_*.py suite still passes."""
    proc = run(
        workspace,
        ["-m", "unittest", "discover", "-s", "tests", "-p", "test_core_*.py", "-v"],
    )
    output = proc.stdout + proc.stderr
    return proc.returncode == 0 and "Ran 0 tests" not in output


def main():
    if len(sys.argv) != 2:
        print("usage: check.py WORKSPACE", file=sys.stderr)
        return 2
    workspace = os.path.abspath(sys.argv[1])

    requirement_checks = [
        ("R1", check_r1),
        ("R2", check_r2),
        ("R3", check_r3),
        ("R4", check_r4),
        ("R5", check_r5),
        ("R6", check_r6),
        ("R7", check_r7),
        ("R8", check_r8),
        ("R9", check_r9),
        ("R10", check_r10),
    ]
    regression_checks = [
        ("G1", check_g1),
        ("G2", check_g2),
    ]

    requirements = {}
    regressions = {}
    with tempfile.TemporaryDirectory() as tmpdir:
        for key, fn in requirement_checks:
            try:
                requirements[key] = bool(fn(workspace, tmpdir))
            except Exception:
                requirements[key] = False
        for key, fn in regression_checks:
            try:
                regressions[key] = bool(fn(workspace, tmpdir))
            except Exception:
                regressions[key] = False

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
