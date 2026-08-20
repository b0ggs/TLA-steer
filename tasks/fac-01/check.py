#!/usr/bin/env python3
"""Checker for the colstat bug-fix task.

Usage: python check.py <workspace>

Runs entirely outside the workspace: subprocesses use a private temporary
directory as cwd, PYTHONDONTWRITEBYTECODE=1, and PYTHONPATH pointing at the
workspace. Nothing is written into the scanned tree. One subprocess per
requirement; file-content requirements are checked by parsing text read from
the workspace. Every asserted literal appears verbatim in the workspace's
public files (README.md, docs/algorithms.md, CHANGELOG.md,
tests/test_stats.py, .issue-contract.md).
"""

import json
import os
import subprocess
import sys
import tempfile

TIMEOUT = 120

DOCSTRING_LINE = "Returns the mean of the two middle values when n is even."
CHANGELOG_HEADING = "## 0.4.1"
CHANGELOG_BULLET = (
    "- Fixed: median now averages the two middle values for even-sized columns"
)
UNKNOWN_COLUMN_LINE = "colstat: unknown column: nosuchcol"
VERSION_LINE = "colstat 0.4.1"
KEY_ORDER = ["count", "min", "max", "mean", "median", "stdev"]


def run_py(workspace, tmpdir, args, timeout=TIMEOUT):
    env = dict(os.environ)
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    env["PYTHONPATH"] = workspace
    return subprocess.run(
        [sys.executable] + list(args),
        capture_output=True,
        text=True,
        timeout=timeout,
        cwd=tmpdir,
        env=env,
    )


def read_text(workspace, *parts):
    with open(os.path.join(workspace, *parts), encoding="utf-8") as handle:
        return handle.read()


def guarded(fn):
    try:
        return bool(fn())
    except Exception:
        return False


def main():
    workspace = os.path.abspath(sys.argv[1])
    tmpdir = tempfile.mkdtemp(prefix="colstat-check-")
    scores_csv = os.path.join(workspace, "examples", "scores.csv")

    def r1():
        # FAC01-1 (docs/algorithms.md): median([1.0, 2.0, 3.0, 4.0]) must return 2.5
        proc = run_py(
            workspace,
            tmpdir,
            [
                "-c",
                "from colstat.stats import median; "
                "print(repr(median([1.0, 2.0, 3.0, 4.0])))",
            ],
        )
        return proc.returncode == 0 and abs(float(proc.stdout.strip()) - 2.5) < 1e-9

    def r2():
        # FAC01-2 (README.md): __version__ must be "0.4.1"
        proc = run_py(
            workspace, tmpdir, ["-c", "import colstat; print(colstat.__version__)"]
        )
        return proc.returncode == 0 and proc.stdout.strip() == "0.4.1"

    def r3():
        # FAC01-3 (CHANGELOG.md): heading and bullet lines, matched line-wise
        lines = [line.strip() for line in read_text(workspace, "CHANGELOG.md").splitlines()]
        return CHANGELOG_HEADING in lines and CHANGELOG_BULLET in lines

    def r4():
        # FAC01-4 (docs/algorithms.md): docstring line, read from the live object
        proc = run_py(
            workspace,
            tmpdir,
            ["-c", "from colstat.stats import median; print(median.__doc__)"],
        )
        return proc.returncode == 0 and DOCSTRING_LINE in proc.stdout

    def r5():
        # FAC01-5 (docs/algorithms.md): DEFAULT_PRECISION must be 4
        proc = run_py(
            workspace,
            tmpdir,
            ["-c", "from colstat.config import DEFAULT_PRECISION; print(DEFAULT_PRECISION)"],
        )
        return proc.returncode == 0 and proc.stdout.strip() == "4"

    def r6():
        # FAC01-6 (docs/algorithms.md): header-only input raises ValueError
        code = (
            "import os, tempfile\n"
            "from colstat.reader import load_rows\n"
            "d = tempfile.mkdtemp()\n"
            "p = os.path.join(d, 'headeronly.csv')\n"
            "with open(p, 'w', newline='') as h:\n"
            "    h.write('score\\n')\n"
            "try:\n"
            "    load_rows(p)\n"
            "    print('NOERROR')\n"
            "except ValueError as exc:\n"
            "    print('VALUEERROR:' + str(exc))\n"
        )
        proc = run_py(workspace, tmpdir, ["-c", code])
        return (
            proc.returncode == 0
            and proc.stdout.strip() == "VALUEERROR:no data rows in input"
        )

    def r7():
        # FAC01-7 (tests/test_stats.py): named test exists and full suite passes
        source = read_text(workspace, "tests", "test_stats.py")
        proc = run_py(
            workspace,
            tmpdir,
            [
                "-m",
                "unittest",
                "discover",
                "-s",
                os.path.join(workspace, "tests"),
                "-t",
                workspace,
            ],
        )
        return "def test_median_even_count" in source and proc.returncode == 0

    def r8():
        # FAC01-8 (README.md): unknown-column stderr line and exit status 2
        proc = run_py(
            workspace, tmpdir, ["-m", "colstat.cli", "stats", scores_csv, "nosuchcol"]
        )
        return proc.returncode == 2 and proc.stderr.strip() == UNKNOWN_COLUMN_LINE

    def r9():
        # FAC01-9 (README.md): --version prints "colstat 0.4.1", exit status 0
        proc = run_py(workspace, tmpdir, ["-m", "colstat.cli", "--version"])
        return proc.returncode == 0 and proc.stdout.strip() == VERSION_LINE

    def r10():
        # FAC01-10 (docs/algorithms.md): JSON key order of the stats command
        proc = run_py(
            workspace, tmpdir, ["-m", "colstat.cli", "stats", scores_csv, "score"]
        )
        if proc.returncode != 0:
            return False
        pairs = json.loads(proc.stdout, object_pairs_hook=list)
        return [key for key, _ in pairs] == KEY_ORDER

    def g1():
        # docs/algorithms.md documented example: mean([2.0, 4.0, 9.0]) == 5.0
        proc = run_py(
            workspace,
            tmpdir,
            ["-c", "from colstat.stats import mean; print(repr(mean([2.0, 4.0, 9.0])))"],
        )
        return proc.returncode == 0 and abs(float(proc.stdout.strip()) - 5.0) < 1e-9

    def g2():
        # docs/algorithms.md documented example: median([5.0, 1.0, 9.0]) == 5.0
        proc = run_py(
            workspace,
            tmpdir,
            [
                "-c",
                "from colstat.stats import median; "
                "print(repr(median([5.0, 1.0, 9.0])))",
            ],
        )
        return proc.returncode == 0 and abs(float(proc.stdout.strip()) - 5.0) < 1e-9

    requirements = {
        "R1": guarded(r1),
        "R2": guarded(r2),
        "R3": guarded(r3),
        "R4": guarded(r4),
        "R5": guarded(r5),
        "R6": guarded(r6),
        "R7": guarded(r7),
        "R8": guarded(r8),
        "R9": guarded(r9),
        "R10": guarded(r10),
    }
    regressions = {
        "G1": guarded(g1),
        "G2": guarded(g2),
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
