#!/usr/bin/env python3
"""Objective checker for rolling-v1-01."""

import argparse
import importlib
import io
import json
import os
import subprocess
import sys
from pathlib import Path
from unittest import mock

sys.dont_write_bytecode = True

TASK_ID = "rolling-v1-01"
EXPECTED_FILES = {
    ".issue-contract.md",
    "CODER.md",
    "README.md",
    "eventrollup/__init__.py",
    "eventrollup/__main__.py",
    "eventrollup/formatting.py",
    "eventrollup/rollup.py",
    "examples/events.ndjson",
    "tests/test_formatting.py",
}
EXPECTED_PROTECTED_SHA256 = {
    ".issue-contract.md": "0ac2d68e1073b426958ea9ae96c5bcfa4bf8656b4fe38feb585a8bb5da11900d",
    "CODER.md": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    "README.md": "3b762f028eb35e47b5a7647e93a10da74f0df807ef29a11504dfd0b3b16ef38a",
    "eventrollup/__init__.py": "7ed12719aa763234d7220c926f8d54efcbe718b64e238d3b04b86ec28a6f6eca",
    "eventrollup/formatting.py": "288aa6606a86e8a457313a8b27c19bde1c7a4ed767bb1767469a7072d5f6d584",
    "examples/events.ndjson": "430db23c871dd8bd10d80a9ee3f3190d1b7240694b52e9c1352b056d4f09a0a8",
    "tests/test_formatting.py": "9121f157b94030c8fb346633b27537767e36a886179a79a67585677d8404d480",
}


def assertion(function):
    try:
        function()
        return {"passed": True, "details": "objective assertion passed"}
    except Exception as exc:
        return {"passed": False, "details": f"{type(exc).__name__}: {exc}"}


def require(condition, message):
    if not condition:
        raise AssertionError(message)


def exact_value_error(function, message):
    try:
        function()
    except ValueError as exc:
        require(str(exc) == message, f"wrong ValueError text: {exc}")
    else:
        raise AssertionError("ValueError was not raised")


def event(user, at, action, **extra):
    return json.dumps(
        {"user": user, "at": at, "action": action, **extra},
        ensure_ascii=False,
        separators=(",", ":"),
    )


def load_modules(root):
    sys.path.insert(0, str(root))
    for name in tuple(sys.modules):
        if name == "eventrollup" or name.startswith("eventrollup."):
            sys.modules.pop(name, None)
    rollup_module = importlib.import_module("eventrollup.rollup")
    main_module = importlib.import_module("eventrollup.__main__")
    formatting_module = importlib.import_module("eventrollup.formatting")
    return rollup_module, main_module, formatting_module


def run_main(main_module, argv, stdin_text):
    stdout = io.StringIO()
    stderr = io.StringIO()
    with (
        mock.patch.object(main_module.sys, "stdin", io.StringIO(stdin_text)),
        mock.patch.object(main_module.sys, "stdout", stdout),
        mock.patch.object(main_module.sys, "stderr", stderr),
    ):
        status = main_module.main(argv)
    return status, stdout.getvalue(), stderr.getvalue()


def check(root):
    def environment_check():
        actual = {
            path.relative_to(root).as_posix()
            for path in root.rglob("*")
            if path.is_file() and "__pycache__" not in path.parts
        }
        require(actual == EXPECTED_FILES, "public file inventory changed")

    environment = assertion(environment_check)
    try:
        rollup_module, main_module, formatting_module = load_modules(root)
    except Exception as exc:
        rollup_module = main_module = formatting_module = None
        load_error = exc

    def modules_present():
        if rollup_module is None:
            raise load_error

    def r1():
        modules_present()

        class OnePass:
            def __init__(self, values):
                self.values = values
                self.calls = 0

            def __iter__(self):
                self.calls += 1
                if self.calls > 1:
                    raise AssertionError("events iterable was iterated more than once")
                return iter(self.values)

        source = OnePass([event("u", "2026-01-01T00:00:00Z", "open")])
        result = rollup_module.rollup(source, 60)
        require(source.calls == 1, "events iterable was not consumed exactly once")
        require(
            source.values == [event("u", "2026-01-01T00:00:00Z", "open")],
            "caller-owned iterable contents were mutated",
        )
        require(isinstance(result, list) and len(result) == 1, "one-pass result is not one session")
        first = rollup_module.rollup([], 60)
        second = rollup_module.rollup([], 60)
        require(first == [] and second == [] and first is not second, "calls did not return fresh lists")

    def r2():
        modules_present()
        message = "idle_seconds must be a positive integer"
        for value in (0, -1, True, False, 1.5, "60"):
            exact_value_error(lambda value=value: rollup_module.rollup([], value), message)
        require(rollup_module.rollup([], 1) == [], "positive integer threshold was rejected")

    def r3():
        modules_present()
        lines = ["", "   ", "\t", event("u", "2026-01-01T00:00:00Z", "open")]
        result = rollup_module.rollup(lines, 60)
        require(len(result) == 1 and result[0]["user"] == "u", "blank lines were not ignored")
        exact_value_error(
            lambda: rollup_module.rollup(["", "{"], 60),
            "line 2: expected a JSON object with non-empty string user, at, and action",
        )

    def r4():
        modules_present()
        valid = event("u", "2026-01-01T00:00:00Z", "open")
        exact_value_error(
            lambda: rollup_module.rollup([valid, "{"], 60),
            "line 2: expected a JSON object with non-empty string user, at, and action",
        )
        invalid = (
            json.dumps(["not", "an", "object"]),
            json.dumps({"at": "2026-01-01T00:00:00Z", "action": "open"}),
            event("u", "2026-01-01T00:00:00Z", ""),
            json.dumps({"user": "u", "at": 1, "action": "open"}),
        )
        for line in invalid:
            exact_value_error(
                lambda line=line: rollup_module.rollup([line], 60),
                "line 1: expected a JSON object with non-empty string user, at, and action",
            )

    def r5():
        modules_present()
        invalid = (
            "2026-01-01 00:00:00Z",
            "2026-01-01T00:00:00.1Z",
            "2026-01-01T00:00:00+00:00",
            "2026-02-30T00:00:00Z",
        )
        for timestamp in invalid:
            exact_value_error(
                lambda timestamp=timestamp: rollup_module.rollup([event("u", timestamp, "open")], 60),
                "line 1: at must be a real UTC whole-second timestamp",
            )
        result = rollup_module.rollup([event("u", "2024-02-29T23:59:59Z", "open")], 60)
        require(result[0]["started_at"] == "2024-02-29T23:59:59Z", "valid leap day was rejected")

    def r6():
        modules_present()
        lines = [
            event("u", "2026-01-01T00:00:10Z", "open"),
            event("v", "2026-01-01T00:00:01Z", "open"),
            event("u", "2026-01-01T00:00:09Z", "close"),
        ]
        exact_value_error(
            lambda: rollup_module.rollup(lines, 60),
            "line 3: timestamps for user u must be nondecreasing",
        )
        equal = [
            event("u", "2026-01-01T00:00:10Z", "open"),
            event("u", "2026-01-01T00:00:10Z", "close"),
        ]
        require(len(rollup_module.rollup(equal, 60)) == 1, "equal timestamps were rejected")

    def r7():
        modules_present()
        exact = [
            event("u", "2026-01-01T00:00:00Z", "open"),
            event("u", "2026-01-01T00:01:00Z", "close"),
        ]
        below = [
            event("u", "2026-01-01T00:00:00Z", "open"),
            event("u", "2026-01-01T00:00:59Z", "close"),
        ]
        require(len(rollup_module.rollup(exact, 60)) == 2, "equal threshold did not split")
        require(len(rollup_module.rollup(below, 60)) == 1, "below-threshold gap split")

    def r8():
        modules_present()
        lines = [
            event("u", "2026-01-01T00:00:00Z", "view"),
            event("u", "2026-01-01T00:00:10Z", "view"),
            event("u", "2026-01-01T00:00:20Z", " deploy "),
        ]
        expected = [{
            "user": "u",
            "started_at": "2026-01-01T00:00:00Z",
            "ended_at": "2026-01-01T00:00:20Z",
            "actions": {"view": 2, " deploy ": 1},
        }]
        result = rollup_module.rollup(lines, 60)
        require(result == expected, "exact session schema or values differ")
        require(type(result[0]) is dict and type(result[0]["actions"]) is dict, "session mappings are not plain dictionaries")
        require(
            all(type(count) is int for count in result[0]["actions"].values()),
            "action counts are not integers",
        )

    def r9():
        modules_present()
        lines = [
            event("b", "2026-01-01T00:00:00Z", "open"),
            event("a", "2026-01-01T00:00:00Z", "open"),
            event("b", "2026-01-01T00:02:00Z", "close"),
        ]
        result = rollup_module.rollup(lines, 60)
        order = [(item["started_at"], item["user"]) for item in result]
        require(order == [
            ("2026-01-01T00:00:00Z", "a"),
            ("2026-01-01T00:00:00Z", "b"),
            ("2026-01-01T00:02:00Z", "b"),
        ], "sessions are not sorted by started_at then user")

    def cli(argv, stdin_text):
        completed = subprocess.run(
            [sys.executable, "-m", "eventrollup", *argv],
            cwd=root,
            input=stdin_text,
            capture_output=True,
            text=True,
            encoding="utf-8",
            env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
            timeout=30,
            check=False,
        )
        return completed.returncode, completed.stdout, completed.stderr

    def r10():
        modules_present()
        stdin_line = event("zoë", "2026-01-01T00:00:00Z", "café") + "\n"
        stdin_expected = '{"actions":{"café":1},"ended_at":"2026-01-01T00:00:00Z","started_at":"2026-01-01T00:00:00Z","user":"zoë"}\n'
        for argv in (["--idle-seconds", "60"], ["--idle-seconds", "60", "-"]):
            require(cli(argv, stdin_line) == (0, stdin_expected, ""), "stdin CLI output differs")
        default_input = (root / "examples/events.ndjson").read_text(encoding="utf-8")
        default_expected = '{"actions":{"edit":1,"view":1},"ended_at":"2026-01-01T00:02:00Z","started_at":"2026-01-01T00:00:00Z","user":"ada"}\n'
        require(cli([], default_input) == (0, default_expected, ""), "default idle threshold is not 300 seconds")
        file_expected = (
            '{"actions":{"view":1},"ended_at":"2026-01-01T00:00:00Z","started_at":"2026-01-01T00:00:00Z","user":"ada"}\n'
            '{"actions":{"edit":1},"ended_at":"2026-01-01T00:02:00Z","started_at":"2026-01-01T00:02:00Z","user":"ada"}\n'
        )
        require(
            cli(["--idle-seconds", "60", "examples/events.ndjson"], "") == (0, file_expected, ""),
            "file CLI output differs",
        )

    def r11():
        modules_present()
        valid = event("u", "2026-01-01T00:00:00Z", "open")
        status, stdout, stderr = run_main(main_module, [], valid + "\n{\n")
        require(status == 2, "processing error status is not 2")
        require(stdout == "", "processing error leaked buffered stdout")
        require(
            stderr == "error: line 2: expected a JSON object with non-empty string user, at, and action\n",
            "processing error stderr differs",
        )
        missing = root / ".scored-missing-events.ndjson"
        try:
            open(missing, "r", encoding="utf-8")
        except OSError as exc:
            expected = f"error: {exc}\n"
        else:
            raise AssertionError("scored missing path unexpectedly exists")
        status, stdout, stderr = run_main(main_module, [str(missing)], "")
        require(status == 2, "file error status is not 2")
        require(stdout == "", "file error wrote stdout")
        require(stderr == expected, "file error stderr differs from str(OSError)")

    def g1():
        modules_present()
        require(
            formatting_module.compact_json({"beta": "β", "alpha": 1}) == '{"alpha":1,"beta":"β"}',
            "protected compact_json behavior changed",
        )
        completed = subprocess.run(
            [sys.executable, "-m", "unittest", "discover", "-s", "tests", "-v"],
            cwd=root,
            capture_output=True,
            text=True,
            env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
            timeout=30,
            check=False,
        )
        require(completed.returncode == 0, "protected public tests failed")

    def integrity_check():
        import hashlib

        for relative, expected in EXPECTED_PROTECTED_SHA256.items():
            actual = hashlib.sha256((root / relative).read_bytes()).hexdigest()
            require(actual == expected, f"protected path changed: {relative}")
        require((root / "CODER.md").read_bytes() == b"", "CODER.md is not zero-byte")

    requirements = {
        name: assertion(function)
        for name, function in (
            ("R1", r1),
            ("R2", r2),
            ("R3", r3),
            ("R4", r4),
            ("R5", r5),
            ("R6", r6),
            ("R7", r7),
            ("R8", r8),
            ("R9", r9),
            ("R10", r10),
            ("R11", r11),
        )
    }
    regressions = {"G1": assertion(g1)}
    integrity = assertion(integrity_check)
    resolved = (
        environment["passed"]
        and integrity["passed"]
        and all(item["passed"] for item in requirements.values())
        and all(item["passed"] for item in regressions.values())
    )
    return {
        "environment": environment,
        "integrity": integrity,
        "regressions": regressions,
        "requirements": requirements,
        "resolved": resolved,
        "schema": "scout-check-result-v1",
        "task_id": TASK_ID,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("workspace", type=Path)
    arguments = parser.parse_args()
    print(json.dumps(check(arguments.workspace.resolve()), ensure_ascii=False, sort_keys=True, separators=(",", ":")))


if __name__ == "__main__":
    main()
