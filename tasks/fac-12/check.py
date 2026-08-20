#!/usr/bin/env python3
"""Checker for the dirlens `newest` task.

Usage: python check.py /path/to/workspace

Runs entirely outside the workspace and writes nothing into it. All fixture
trees are created in the checker's own temporary directories; the tool under
test is pointed at those fixtures. Every value asserted below is stated in the
workspace's public documentation (README.md, docs/cli.md, CHANGELOG.md,
examples/README.md).
"""

import json
import os
import re
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

TIMEOUT = 120
BASE = 1_700_000_000

# (relative path, mtime offset from BASE, size in bytes) — all distinct mtimes.
FIXTURE = [
    ("alpha.txt", 600, 5),
    ("beta.log", 500, 7),
    ("sub/gamma.txt", 400, 3),
    ("sub/delta", 300, 11),
    ("epsilon.log", 200, 2),
    ("sub/deep/zeta.txt", 100, 9),
    ("omega.txt", 50, 4),
]

HELP_SENTENCE = "List the most recently modified files in a directory tree."
EXAMPLE_COMMAND = "python -m dirlens newest examples/sample --limit 3"
CHANGELOG_HEADING = "## 0.3.0"
CHANGELOG_BULLET = "- Added the newest subcommand."
VERSION_LINE = "dirlens 0.3.0"


def iso(timestamp):
    """docs/cli.md: UTC, whole seconds, YYYY-MM-DDTHH:MM:SSZ."""
    moment = datetime.fromtimestamp(int(timestamp), timezone.utc)
    return moment.strftime("%Y-%m-%dT%H:%M:%SZ")


def build_fixture(tmp):
    root = Path(tmp) / "tree"
    for rel, offset, size in FIXTURE:
        path = root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(b"x" * size)
        os.utime(path, (BASE + offset, BASE + offset))
    return root


def newest_expected():
    """(relpath, iso-mtime) tuples ordered newest first, path ascending on ties."""
    ordered = sorted(FIXTURE, key=lambda row: (-(BASE + row[1]), row[0]))
    return [(rel, iso(BASE + offset)) for rel, offset, _size in ordered]


def run_cli(workspace, args):
    env = dict(os.environ)
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    env["COLUMNS"] = "200"
    return subprocess.run(
        [sys.executable, "-m", "dirlens"] + list(args),
        cwd=str(workspace),
        env=env,
        capture_output=True,
        text=True,
        timeout=TIMEOUT,
    )


def run_unittest(workspace, target):
    env = dict(os.environ)
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    return subprocess.run(
        [sys.executable, "-m", "unittest", target],
        cwd=str(workspace),
        env=env,
        capture_output=True,
        text=True,
        timeout=TIMEOUT,
    )


def fenced_lines(text):
    """Stripped lines that sit inside ``` fenced code blocks."""
    lines = []
    in_fence = False
    for line in text.splitlines():
        if line.strip().startswith("```"):
            in_fence = not in_fence
            continue
        if in_fence:
            lines.append(line.strip())
    return lines


# --- requirement checks -----------------------------------------------------


def check_r1(workspace, tree, expected):
    """newest with no options: default of five entries, newest first,
    each line `<mtime-iso>\\t<relpath>` (README default + docs/cli.md format)."""
    proc = run_cli(workspace, ["newest", str(tree)])
    want = ["%s\t%s" % (ts, rel) for rel, ts in expected[:5]]
    return proc.returncode == 0 and proc.stdout.splitlines() == want


def check_r2(workspace, tree, expected):
    """--limit N prints at most N entries (docs/cli.md)."""
    proc = run_cli(workspace, ["newest", str(tree), "--limit", "2"])
    want = ["%s\t%s" % (ts, rel) for rel, ts in expected[:2]]
    return proc.returncode == 0 and proc.stdout.splitlines() == want


def check_r3(workspace, tree, expected):
    """--json: JSON array, same order/limit, objects with exactly path+mtime."""
    proc = run_cli(workspace, ["newest", str(tree), "--limit", "3", "--json"])
    if proc.returncode != 0:
        return False
    payload = json.loads(proc.stdout)
    want = [{"path": rel, "mtime": ts} for rel, ts in expected[:3]]
    return payload == want


def check_r4(workspace):
    """newest --help contains the sentence given in docs/cli.md."""
    proc = run_cli(workspace, ["newest", "--help"])
    collapsed = " ".join(proc.stdout.split())
    return proc.returncode == 0 and HELP_SENTENCE in collapsed


def check_r5(workspace, tmp):
    """Nonexistent PATH: message on stderr, exit status 3 (docs/cli.md)."""
    missing = Path(tmp) / "definitely-missing" / "nope"
    proc = run_cli(workspace, ["newest", str(missing)])
    return proc.returncode == 3 and proc.stderr.strip() != ""


def check_r6(workspace):
    """examples/README.md shows the exact newest invocation inside a fence."""
    text = (workspace / "examples" / "README.md").read_text(encoding="utf-8")
    return EXAMPLE_COMMAND in fenced_lines(text)


def check_r7(workspace):
    """CHANGELOG.md has a `## 0.3.0` section whose bullet matches exactly."""
    text = (workspace / "CHANGELOG.md").read_text(encoding="utf-8")
    lines = [line.strip() for line in text.splitlines()]
    if CHANGELOG_HEADING not in lines:
        return False
    start = lines.index(CHANGELOG_HEADING)
    for line in lines[start + 1:]:
        if line.startswith("## "):
            return False
        if line == CHANGELOG_BULLET:
            return True
    return False


def check_r8(workspace):
    """--version reports dirlens 0.3.0 (README)."""
    proc = run_cli(workspace, ["--version"])
    return proc.returncode == 0 and proc.stdout.strip() == VERSION_LINE


def check_r9(workspace):
    """tests/test_newest.py passes with at least one test (README)."""
    if not (workspace / "tests" / "test_newest.py").is_file():
        return False
    proc = run_unittest(workspace, "tests.test_newest")
    ran = re.search(r"Ran ([0-9]+) tests?", proc.stderr)
    return proc.returncode == 0 and ran is not None and int(ran.group(1)) >= 1


def check_r10(workspace, tmp):
    """Empty directory: no stdout output, exit status 0 (docs/cli.md)."""
    empty = Path(tmp) / "empty-tree"
    empty.mkdir()
    proc = run_cli(workspace, ["newest", str(empty)])
    return proc.returncode == 0 and proc.stdout.strip() == ""


def check_g1(workspace, tree):
    """Regression: scan still prints `<relpath>\\t<size>` sorted by path."""
    proc = run_cli(workspace, ["scan", str(tree)])
    want = [
        "%s\t%d" % (rel, size)
        for rel, _offset, size in sorted(FIXTURE, key=lambda row: row[0])
    ]
    return proc.returncode == 0 and proc.stdout.splitlines() == want


def check_g2(workspace, tree):
    """Regression: ext still counts per extension, `(none)` for none, sorted."""
    proc = run_cli(workspace, ["ext", str(tree)])
    counts = {}
    for rel, _offset, _size in FIXTURE:
        name = rel.rsplit("/", 1)[-1]
        label = name.rsplit(".", 1)[1] if "." in name else "(none)"
        counts[label] = counts.get(label, 0) + 1
    want = ["%s\t%d" % (label, counts[label]) for label in sorted(counts)]
    return proc.returncode == 0 and proc.stdout.splitlines() == want


def main():
    workspace = Path(sys.argv[1]).resolve()

    def safe(func, *args):
        try:
            return bool(func(*args))
        except Exception:
            return False

    with tempfile.TemporaryDirectory() as tmp:
        tree = build_fixture(tmp)
        expected = newest_expected()

        requirements = {
            "R1": safe(check_r1, workspace, tree, expected),
            "R2": safe(check_r2, workspace, tree, expected),
            "R3": safe(check_r3, workspace, tree, expected),
            "R4": safe(check_r4, workspace),
            "R5": safe(check_r5, workspace, tmp),
            "R6": safe(check_r6, workspace),
            "R7": safe(check_r7, workspace),
            "R8": safe(check_r8, workspace),
            "R9": safe(check_r9, workspace),
            "R10": safe(check_r10, workspace, tmp),
        }
        regressions = {
            "G1": safe(check_g1, workspace, tree),
            "G2": safe(check_g2, workspace, tree),
        }

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


if __name__ == "__main__":
    main()
