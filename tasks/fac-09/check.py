#!/usr/bin/env python3
"""Checker for the wordfreq `stats` feature-addition task.

Usage: python3 check.py /absolute/path/to/workspace

Runs OUTSIDE the workspace and writes nothing into it. All fixture files are
created in a private temporary directory. Every asserted value below is stated
verbatim in the workspace's public documentation (README.md, docs/cli.md,
CHANGELOG.md, examples/README.md).

Output: canonical JSON
  {"requirements": {"R1": bool, ...}, "regressions": {"G1": bool, "G2": bool},
   "resolved": bool}
"""

import json
import os
import re
import subprocess
import sys
import tempfile

TIMEOUT = 120


def run(cmd, cwd, extra_env=None):
    """Run one subprocess; return (returncode, stdout, stderr) or None on timeout."""
    env = dict(os.environ)
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    if extra_env:
        env.update(extra_env)
    try:
        proc = subprocess.run(
            cmd,
            cwd=cwd,
            env=env,
            capture_output=True,
            text=True,
            timeout=TIMEOUT,
        )
    except (subprocess.TimeoutExpired, OSError):
        return None
    return proc.returncode, proc.stdout, proc.stderr


def out_lines(text):
    """Non-empty lines with trailing whitespace stripped (semantic compare)."""
    return [line.rstrip() for line in text.splitlines() if line.strip()]


def read_file(workspace, relpath):
    try:
        with open(os.path.join(workspace, relpath), "r", encoding="utf-8") as fh:
            return fh.read()
    except OSError:
        return None


def main():
    if len(sys.argv) != 2:
        print("usage: check.py WORKSPACE", file=sys.stderr)
        return 2
    workspace = os.path.abspath(sys.argv[1])
    py = sys.executable

    requirements = {}
    regressions = {}

    with tempfile.TemporaryDirectory(prefix="wordfreq-check-") as tmp:

        def fixture(name, content):
            path = os.path.join(tmp, name)
            with open(path, "w", encoding="utf-8") as fh:
                fh.write(content)
            return path

        # R1: stats subcommand prints the three-line report.
        # Example stated verbatim in docs/cli.md ("stats" section):
        # input "the cat and the hat and the bat" ->
        # total_words: 8 / unique_words: 5 / top_word: the (3), exit status 0.
        path = fixture("r1.txt", "the cat and the hat and the bat\n")
        res = run([py, "-m", "wordfreq", "stats", path], cwd=workspace)
        requirements["R1"] = bool(
            res
            and res[0] == 0
            and out_lines(res[1])
            == ["total_words: 8", "unique_words: 5", "top_word: the (3)"]
        )

        # R2: help text sentence, stated verbatim in docs/cli.md:
        # "Show summary statistics for the input files."
        res = run([py, "-m", "wordfreq", "stats", "--help"], cwd=workspace)
        requirements["R2"] = bool(
            res
            and res[0] == 0
            and "Show summary statistics for the input files." in res[1]
        )

        # R3: no words -> line "no words found" on stderr, exit status 4
        # (docs/cli.md, stats section and exit status summary).
        path = fixture("r3.txt", "")
        res = run([py, "-m", "wordfreq", "stats", path], cwd=workspace)
        requirements["R3"] = bool(
            res and res[0] == 4 and "no words found" in res[2]
        )

        # R4: examples/stats-output.txt holds the exact three lines stated in
        # examples/README.md for examples/moby.txt. No subprocess needed.
        text = read_file(workspace, os.path.join("examples", "stats-output.txt"))
        requirements["R4"] = bool(
            text is not None
            and out_lines(text)
            == ["total_words: 43", "unique_words: 38", "top_word: and (2)"]
        )

        # R5: CHANGELOG.md gains a "## 1.3.0" section containing the line
        # "Added the stats subcommand." (stated in CHANGELOG.md, Unreleased).
        text = read_file(workspace, "CHANGELOG.md")
        requirements["R5"] = bool(
            text is not None
            and re.search(r"(?m)^##\s+\[?v?1\.3\.0", text)
            and "Added the stats subcommand." in text
        )

        # R6: README Defaults list gains the entry
        # "stats --min-length defaults to 1." (stated in README.md, Defaults:
        # 'this Defaults list must also gain the entry ...'). Checked as a
        # whole list line so the instruction sentence itself does not count.
        text = read_file(workspace, "README.md")
        found_entry = False
        if text is not None:
            for line in text.splitlines():
                item = line.strip()
                item = re.sub(r"^[-*+]\s*", "", item)
                item = item.replace("`", "").strip()
                if item == "stats --min-length defaults to 1.":
                    found_entry = True
                    break
        requirements["R6"] = found_entry

        # R7: --min-length filter; example stated verbatim in docs/cli.md:
        # file "aa b ccc b" with --min-length 2 ->
        # total_words: 2 / unique_words: 2 / top_word: aa (1).
        path = fixture("r7.txt", "aa b ccc b\n")
        res = run(
            [py, "-m", "wordfreq", "stats", "--min-length", "2", path],
            cwd=workspace,
        )
        requirements["R7"] = bool(
            res
            and res[0] == 0
            and out_lines(res[1])
            == ["total_words: 2", "unique_words: 2", "top_word: aa (1)"]
        )

        # R8: new test module tests/test_stats.py passes on its own
        # (README.md, Testing: "python -m unittest tests.test_stats must pass").
        res = run([py, "-m", "unittest", "tests.test_stats", "-v"], cwd=workspace)
        ran_some = bool(res and re.search(r"Ran [1-9]\d* tests?", res[1] + res[2]))
        requirements["R8"] = bool(res and res[0] == 0 and ran_some)

        # R9: version bump; CHANGELOG.md states that after the bump
        # "python -m wordfreq --version" prints "wordfreq 1.3.0".
        res = run([py, "-m", "wordfreq", "--version"], cwd=workspace)
        requirements["R9"] = bool(
            res and res[0] == 0 and (res[1] + res[2]).strip() == "wordfreq 1.3.0"
        )

        # R10: summarize in wordfreq/report.py returns None for an empty
        # mapping (stated in docs/cli.md, stats section).
        code = (
            "import sys\n"
            "from wordfreq.report import summarize\n"
            "sys.exit(0 if summarize({}) is None else 1)\n"
        )
        res = run([py, "-c", code], cwd=workspace)
        requirements["R10"] = bool(res and res[0] == 0)

        # G1: count subcommand keeps its documented behavior; example stated
        # verbatim in docs/cli.md ("count"): file "b a b" -> "b 2" / "a 1".
        path = fixture("g1.txt", "b a b\n")
        res = run([py, "-m", "wordfreq", "count", path], cwd=workspace)
        regressions["G1"] = bool(
            res and res[0] == 0 and out_lines(res[1]) == ["b 2", "a 1"]
        )

        # G2: pre-existing test modules still pass.
        res = run(
            [py, "-m", "unittest", "tests.test_tokenizer", "tests.test_counter"],
            cwd=workspace,
        )
        regressions["G2"] = bool(res and res[0] == 0)

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
