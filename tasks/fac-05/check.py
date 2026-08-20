#!/usr/bin/env python3
"""Checker for FAC05: logrotor `prune` subcommand (feature-addition).

Usage: python3 check.py /path/to/workspace

Runs entirely outside the workspace: every scratch directory the tool is
pointed at lives in the checker's own temporary directory, and
PYTHONDONTWRITEBYTECODE=1 prevents bytecode from being written into the
scanned tree.  Every value asserted below is stated verbatim in the
workspace's public files (README.md, docs/cli.md, CHANGELOG.md,
examples/README.md — acceptance notes FAC05-1..FAC05-9).
"""

import json
import os
import re
import subprocess
import sys
import tempfile

TIMEOUT = 120  # generous per-subprocess timeout, seconds


# ---------------------------------------------------------------- helpers

def make_env(workspace):
    env = dict(os.environ)
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    env["PYTHONPATH"] = workspace
    return env


def run_cli(workspace, args, cwd):
    """Run `python -m logrotor <args>` with cwd outside the workspace."""
    return subprocess.run(
        [sys.executable, "-m", "logrotor"] + list(args),
        cwd=cwd,
        env=make_env(workspace),
        capture_output=True,
        text=True,
        timeout=TIMEOUT,
    )


def touch(path, content=""):
    with open(path, "w") as fh:
        fh.write(content)


def stdout_lines(text):
    """Non-empty stdout lines with trailing whitespace stripped."""
    return [line.rstrip() for line in text.splitlines() if line.strip()]


def read_text(path):
    with open(path, "r", encoding="utf-8") as fh:
        return fh.read()


def section_lines(markdown_text, heading):
    """Lines of the markdown section whose heading line equals *heading*,
    up to (not including) the next line starting with '## '."""
    lines = markdown_text.splitlines()
    collected = []
    inside = False
    for line in lines:
        if line.strip() == heading:
            inside = True
            continue
        if inside and line.startswith("## "):
            break
        if inside:
            collected.append(line)
    return collected


def archive_name(base, day):
    return "%s.log.202601%02d000000" % (base, day)


# ------------------------------------------------------------ requirements

def check_r1(ws, tmp):
    """prune --keep N deletes older archives per log base name, prints
    `pruned: <filename>` lines in ascending order, exits 0 (FAC05-1)."""
    d = os.path.join(tmp, "r1")
    os.mkdir(d)
    app = [archive_name("app", day) for day in range(1, 6)]   # 5 archives
    web = [archive_name("web", day) for day in range(1, 4)]   # 3 archives
    for name in app + web:
        touch(os.path.join(d, name), "old data\n")
    touch(os.path.join(d, "app.log"), "live\n")
    touch(os.path.join(d, "notes.txt"), "not an archive\n")
    proc = run_cli(ws, ["prune", "--keep", "2", d], tmp)
    if proc.returncode != 0:
        return False
    doomed = sorted(app[:3] + web[:1])
    if stdout_lines(proc.stdout) != ["pruned: " + n for n in doomed]:
        return False
    expected_left = sorted(app[3:] + web[1:] + ["app.log", "notes.txt"])
    if sorted(os.listdir(d)) != expected_left:
        return False
    return read_text(os.path.join(d, "app.log")) == "live\n"


def check_r2(ws, tmp):
    """--dry-run prints `would prune: <filename>` lines, deletes nothing,
    exits 0 (FAC05-4)."""
    d = os.path.join(tmp, "r2")
    os.mkdir(d)
    app = [archive_name("app", day) for day in range(1, 5)]   # 4 archives
    for name in app:
        touch(os.path.join(d, name), "x\n")
    touch(os.path.join(d, "app.log"), "live\n")
    proc = run_cli(ws, ["prune", "--dry-run", "--keep", "1", d], tmp)
    if proc.returncode != 0:
        return False
    if stdout_lines(proc.stdout) != ["would prune: " + n for n in app[:3]]:
        return False
    return sorted(os.listdir(d)) == sorted(app + ["app.log"])


def check_r3(ws, tmp):
    """Missing directory: `error: no such directory: <directory>` on
    stderr, exit status 3 (FAC05-3)."""
    missing = os.path.join(tmp, "r3_no_such_dir")
    proc = run_cli(ws, ["prune", "--keep", "2", missing], tmp)
    if proc.returncode != 3:
        return False
    return "error: no such directory: " in proc.stderr and missing in proc.stderr


def check_r4(ws, tmp):
    """Directory with no archives: prints exactly `nothing to prune`,
    exits 0 (FAC05-5)."""
    d = os.path.join(tmp, "r4")
    os.mkdir(d)
    proc = run_cli(ws, ["prune", "--keep", "3", d], tmp)
    return proc.returncode == 0 and proc.stdout.strip() == "nothing to prune"


def check_r5(ws, tmp):
    """logrotor.scan.find_archives(directory) returns [] for a directory
    containing no archives (FAC05-5, empty-input boundary in scan.py)."""
    d = os.path.join(tmp, "r5")
    os.mkdir(d)
    code = (
        "import sys\n"
        "from logrotor.scan import find_archives\n"
        "result = find_archives(sys.argv[1])\n"
        "sys.exit(0 if result == [] else 1)\n"
    )
    proc = subprocess.run(
        [sys.executable, "-c", code, d],
        cwd=tmp,
        env=make_env(ws),
        capture_output=True,
        text=True,
        timeout=TIMEOUT,
    )
    return proc.returncode == 0


def check_r6(ws, tmp):
    """--keep defaults to 5, and README's `## Defaults` section carries
    the verbatim retention bullet (FAC05-6)."""
    d = os.path.join(tmp, "r6")
    os.mkdir(d)
    app = [archive_name("app", day) for day in range(1, 8)]   # 7 archives
    for name in app:
        touch(os.path.join(d, name), "x\n")
    proc = run_cli(ws, ["prune", d], tmp)
    if proc.returncode != 0:
        return False
    if stdout_lines(proc.stdout) != ["pruned: " + n for n in app[:2]]:
        return False
    if sorted(os.listdir(d)) != app[2:]:
        return False
    readme = read_text(os.path.join(ws, "README.md"))
    defaults = section_lines(readme, "## Defaults")
    wanted = "- The default retention for prune is 5 archives per log."
    return any(line.strip() == wanted for line in defaults)


def check_r7(ws, tmp):
    """`prune --help` contains the verbatim help sentence (FAC05-2)."""
    proc = run_cli(ws, ["prune", "--help"], tmp)
    sentence = "Remove old rotated archives, keeping the newest N per log."
    return proc.returncode == 0 and sentence in proc.stdout


def check_r8(ws, tmp):
    """`--version` prints exactly `logrotor 1.4.0` (FAC05-7)."""
    proc = run_cli(ws, ["--version"], tmp)
    if proc.returncode != 0:
        return False
    return (proc.stdout + proc.stderr).strip() == "logrotor 1.4.0"


def check_r9(ws, tmp):
    """CHANGELOG.md has a `## 1.4.0` section containing the verbatim
    bullet `- Added the prune subcommand.` (FAC05-7)."""
    changelog = read_text(os.path.join(ws, "CHANGELOG.md"))
    lines = section_lines(changelog, "## 1.4.0")
    return any(line.strip() == "- Added the prune subcommand." for line in lines)


def check_r10(ws, tmp):
    """examples/prune-session.txt exists with exactly the transcript
    given in examples/README.md (FAC05-8)."""
    path = os.path.join(ws, "examples", "prune-session.txt")
    if not os.path.isfile(path):
        return False
    expected = [
        "$ python -m logrotor prune --dry-run --keep 2 logs/",
        "would prune: app.log.20260301090000",
        "would prune: app.log.20260302090000",
        "$ python -m logrotor prune --keep 2 logs/",
        "pruned: app.log.20260301090000",
        "pruned: app.log.20260302090000",
        "$ python -m logrotor prune --keep 2 logs/",
        "nothing to prune",
    ]
    lines = [line.rstrip() for line in read_text(path).splitlines()]
    while lines and not lines[-1]:
        lines.pop()
    return lines == expected


def check_r11(ws, tmp):
    """tests/test_prune.py exists; `python -m unittest tests.test_prune`
    passes and runs at least one test (FAC05-9)."""
    if not os.path.isfile(os.path.join(ws, "tests", "test_prune.py")):
        return False
    proc = subprocess.run(
        [sys.executable, "-m", "unittest", "tests.test_prune"],
        cwd=tmp,
        env=make_env(ws),
        capture_output=True,
        text=True,
        timeout=TIMEOUT,
    )
    if proc.returncode != 0:
        return False
    return re.search(r"Ran [1-9][0-9]* tests?", proc.stderr) is not None


# ------------------------------------------------------------- regressions

def check_g1(ws, tmp):
    """rotate still archives to NAME.log.<14 digits> and recreates an
    empty NAME.log (docs/cli.md, Archive naming / rotate)."""
    d = os.path.join(tmp, "g1")
    os.mkdir(d)
    touch(os.path.join(d, "app.log"), "hello\n")
    proc = run_cli(ws, ["rotate", d], tmp)
    if proc.returncode != 0:
        return False
    entries = os.listdir(d)
    if "app.log" not in entries:
        return False
    if os.path.getsize(os.path.join(d, "app.log")) != 0:
        return False
    archives = [n for n in entries if re.fullmatch(r"app\.log\.\d{14}", n)]
    if len(archives) != 1:
        return False
    return read_text(os.path.join(d, archives[0])) == "hello\n"


def check_g2(ws, tmp):
    """list still prints archive filenames one per line in ascending
    order, exit 0 (docs/cli.md, list)."""
    d = os.path.join(tmp, "g2")
    os.mkdir(d)
    archives = [archive_name("app", day) for day in (3, 1, 2)]
    for name in archives:
        touch(os.path.join(d, name), "x\n")
    touch(os.path.join(d, "app.log"), "live\n")
    touch(os.path.join(d, "readme.txt"), "not an archive\n")
    proc = run_cli(ws, ["list", d], tmp)
    if proc.returncode != 0:
        return False
    return stdout_lines(proc.stdout) == sorted(archives)


# ------------------------------------------------------------------- main

REQUIREMENTS = [
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
    ("R11", check_r11),
]

REGRESSIONS = [
    ("G1", check_g1),
    ("G2", check_g2),
]


def main():
    if len(sys.argv) != 2:
        print("usage: check.py WORKSPACE", file=sys.stderr)
        return 2
    workspace = os.path.abspath(sys.argv[1])
    requirements = {}
    regressions = {}
    with tempfile.TemporaryDirectory(prefix="fac05-check-") as tmp:
        for key, fn in REQUIREMENTS:
            try:
                requirements[key] = bool(fn(workspace, tmp))
            except Exception:
                requirements[key] = False
        for key, fn in REGRESSIONS:
            try:
                regressions[key] = bool(fn(workspace, tmp))
            except Exception:
                regressions[key] = False
    resolved = all(requirements.values()) and all(regressions.values())
    print(json.dumps(
        {"requirements": requirements, "regressions": regressions,
         "resolved": resolved}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
