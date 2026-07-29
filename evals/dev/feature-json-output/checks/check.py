"""Hidden subprocess check for JSON and default CLI behavior."""

import argparse
import json
from pathlib import Path
import subprocess
import sys


def require(condition, message):
    if not condition:
        raise AssertionError(message)


def invoke(repo, *arguments):
    return subprocess.run(
        [sys.executable, "sample_cli.py", *arguments],
        cwd=repo,
        text=True,
        capture_output=True,
        check=False,
        timeout=2,
    )


def run_checks(repo):
    text_result = invoke(repo, "Ada")
    require(text_result.returncode == 0, "default text command did not exit 0")
    require(text_result.stdout == "Hello, Ada!\n", "default text output changed")
    require(text_result.stderr == "", "default text command wrote stderr")

    json_result = invoke(repo, "--json", "Ada")
    require(
        json_result.returncode == 0,
        f"JSON command did not exit 0: {json_result.stderr.strip()}",
    )
    require(json_result.stderr == "", "JSON command wrote stderr")
    require(json_result.stdout.endswith("\n"), "JSON output lacks a trailing newline")
    payload = json.loads(json_result.stdout)
    require(
        payload == {"greeting": "Hello, Ada!", "name": "Ada"},
        "JSON payload has incorrect keys or values",
    )
    require(set(payload) == {"greeting", "name"}, "JSON payload has extra keys")

    missing = invoke(repo, "--json")
    require(missing.returncode == 2, "missing name did not exit 2")
    require(missing.stdout == "", "missing name wrote stdout")
    require("usage:" in missing.stderr.lower(), "missing name did not print usage")

    unknown = invoke(repo, "--unknown", "Ada")
    require(unknown.returncode == 2, "unknown option did not exit 2")
    require(unknown.stdout == "", "unknown option wrote stdout")
    require("usage:" in unknown.stderr.lower(), "unknown option did not print usage")


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

    print("PASS: text and JSON CLI modes have the specified behavior")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
