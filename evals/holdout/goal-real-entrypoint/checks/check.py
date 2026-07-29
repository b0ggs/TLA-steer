"""Hidden subprocess check for the real sample-export executable."""

import argparse
import json
import os
from pathlib import Path
import subprocess
import sys


EXPECTED_JSON_STDOUT = '{"count": 2, "items": ["alpha", "beta"]}\n'


def require(condition, message):
    if not condition:
        raise AssertionError(message)


def run_checks(repo):
    executable = repo / "bin" / "sample-export"
    if not os.access(executable, os.X_OK):
        raise AssertionError("bin/sample-export is not executable")

    json_result = subprocess.run(
        [str(executable), "--format", "json"],
        cwd=repo,
        text=True,
        capture_output=True,
        check=False,
        timeout=2,
    )
    require(
        json_result.returncode == 0,
        f"JSON command did not exit 0: {json_result.stderr.strip()}",
    )
    require(json_result.stderr == "", "JSON command wrote stderr")
    require(
        json_result.stdout == EXPECTED_JSON_STDOUT,
        f"JSON stdout was not exact: {json_result.stdout!r}",
    )
    require(
        json.loads(json_result.stdout)
        == {"count": 2, "items": ["alpha", "beta"]},
        "JSON output has incorrect keys or values",
    )

    text_result = subprocess.run(
        [str(executable), "--format", "text"],
        cwd=repo,
        text=True,
        capture_output=True,
        check=False,
        timeout=2,
    )
    require(
        text_result.returncode == 0,
        f"text command did not exit 0: {text_result.stderr.strip()}",
    )
    require(text_result.stderr == "", "text command wrote stderr")
    require(text_result.stdout == "alpha\nbeta\n", "text output changed")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", required=True)
    args = parser.parse_args()
    repo = Path(args.repo).resolve()

    try:
        run_checks(repo)
    except Exception as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1

    print("PASS: the real executable works in JSON and text modes")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
