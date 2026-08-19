#!/usr/bin/env python3
"""Objective checker for rolling-v1-03."""

import argparse
import copy
import hashlib
import importlib
import inspect
import io
import json
import os
import subprocess
import sys
import tempfile
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from unittest import mock

sys.dont_write_bytecode = True

TASK_ID = "rolling-v1-03"
EXPECTED_FILES = {
    ".issue-contract.md",
    "CODER.md",
    "README.md",
    "badge_cli.py",
    "badge_manifest.py",
    "badge_policy.json",
    "fixtures/attendees.json",
    "fixtures/empty-attendees.json",
    "fixtures/malformed-attendees.json",
    "tests/test_public.py",
}
EXPECTED_PROTECTED_SHA256 = {
    ".issue-contract.md": "73263f38c973a81f1b943ac1889d94851b8ab6d78f5ff5881a65bda265f78b13",
    "CODER.md": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    "README.md": "9ceebc4d7d52270f3e4045f56ab2d4d10ac9912acce8ccfdda74bc4b64c69862",
    "badge_policy.json": "6f1188293e485dab08da22060c67b6c291d477cb7094ddeaf642219e6917e093",
    "fixtures/attendees.json": "ace7bce021be99a9d2eca594e567f71db6ee5268c9cfdf1f24a65e4137b6d6e8",
    "fixtures/empty-attendees.json": "37517e5f3dc66819f61f5a7bb8ace1921282415f10551d2defa5c3eb0985b570",
    "fixtures/malformed-attendees.json": "1b4bc3fcd71240af8dcf8f4ae5b38de18e2c17a6b13aab1ca4c5fe393f20c529",
    "tests/test_public.py": "84c0fe36410f6c59a7e6f4e336d0b6f9eb244138db3d2e81214afc5820c22f7f",
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


def load_modules(root):
    sys.path.insert(0, str(root))
    for name in ("badge_cli", "badge_manifest"):
        sys.modules.pop(name, None)
    manifest_module = importlib.import_module("badge_manifest")
    cli_module = importlib.import_module("badge_cli")
    return manifest_module, cli_module


def load_json(path):
    with path.open(encoding="utf-8") as source:
        return json.load(source)


def check(root):
    policy_path = root / "badge_policy.json"
    attendees_path = root / "fixtures/attendees.json"
    empty_path = root / "fixtures/empty-attendees.json"
    malformed_path = root / "fixtures/malformed-attendees.json"
    missing_path = root / "fixtures/missing-attendees.json"

    def environment_check():
        actual = set()
        for path in root.rglob("*"):
            if not path.is_file():
                continue
            relative = path.relative_to(root)
            if (
                relative.parts[0] == ".git"
                or "__pycache__" in relative.parts
                or path.suffix in {".pyc", ".pyo"}
            ):
                continue
            actual.add(relative.as_posix())
        require(actual == EXPECTED_FILES, "public file inventory changed")

    environment = assertion(environment_check)
    try:
        manifest_module, cli_module = load_modules(root)
        load_error = None
    except Exception as exc:
        manifest_module = cli_module = None
        load_error = exc

    def modules_present():
        if load_error is not None:
            raise load_error

    def raises_manifest_error(function):
        try:
            function()
        except manifest_module.BadgeManifestError:
            return
        raise AssertionError("BadgeManifestError was not raised")

    def valid_attendee(**changes):
        attendee = {
            "id": "V-200",
            "name": "Kai Reed",
            "role": "runner",
            "active": True,
            "late_shift": False,
        }
        attendee.update(changes)
        return attendee

    def r1():
        modules_present()
        error_type = manifest_module.BadgeManifestError
        require(error_type.__bases__ == (ValueError,), "BadgeManifestError is not a direct ValueError subclass")
        require(error_type.__dict__.get("__init__") is None, "BadgeManifestError overrides the inherited constructor")
        parameters = list(inspect.signature(manifest_module.build_manifest).parameters.values())
        require([item.name for item in parameters] == ["attendees", "policy"], "build_manifest parameter names or order differ")
        require(all(item.kind is inspect.Parameter.POSITIONAL_OR_KEYWORD for item in parameters), "parameter kind differs")
        require(all(item.default is inspect.Parameter.empty for item in parameters), "build_manifest has a default")
        attendees = []
        policy = load_json(policy_path)
        attendees_before, policy_before = copy.deepcopy(attendees), copy.deepcopy(policy)
        result = manifest_module.build_manifest(attendees, policy)
        require(type(result) is list and result == [], "empty manifest result differs")
        require(attendees == attendees_before and policy == policy_before, "build_manifest mutated an input")

    def r2():
        modules_present()
        policy = load_json(policy_path)
        extra_key = valid_attendee()
        extra_key["note"] = "desk"
        negatives = [
            "not-a-list",
            [extra_key],
            [valid_attendee(active=1)],
            [valid_attendee(), valid_attendee(name="Jo Bell")],
            [valid_attendee(role="usher")],
        ]
        for attendees in negatives:
            raises_manifest_error(lambda attendees=attendees: manifest_module.build_manifest(attendees, policy))

    def r3():
        modules_present()
        extra_key = load_json(policy_path)
        extra_key["version"] = 1
        wrong_common = load_json(policy_path)
        wrong_common["common_area"] = 7
        empty_roles = load_json(policy_path)
        empty_roles["role_area"] = {}
        wrong_role_area = load_json(policy_path)
        wrong_role_area["role_area"] = {"checkin": 9}
        for policy in (extra_key, wrong_common, empty_roles, wrong_role_area):
            raises_manifest_error(lambda policy=policy: manifest_module.build_manifest([], policy))

    def r4():
        modules_present()
        result = manifest_module.build_manifest(load_json(attendees_path), load_json(policy_path))
        require({item["badge_id"] for item in result} == {"V-099", "V-101", "V-104"}, "active badge selection differs")

    def r5():
        modules_present()
        attendee = {
            "id": "V-500",
            "name": "Noah Green",
            "role": "runner",
            "active": True,
            "late_shift": True,
        }
        result = manifest_module.build_manifest([attendee], load_json(policy_path))
        require(result[0]["areas"] == ["lobby", "supply-room", "staff-exit"], "area grants differ")

    def r6():
        modules_present()
        attendees = [
            {"id": "V-9", "name": "Zed Wu", "role": "runner", "active": True, "late_shift": False},
            {"id": "V-2", "name": "Ana Fox", "role": "checkin", "active": True, "late_shift": True},
        ]
        result = manifest_module.build_manifest(attendees, load_json(policy_path))
        require(type(result) is list, "manifest is not an exact list")
        require(all(type(item) is dict for item in result), "manifest entry is not an exact dictionary")
        require(all(set(item) == {"badge_id", "display", "areas", "late_shift"} for item in result), "entry keys differ")
        observed = [(item["badge_id"], item["display"], item["late_shift"]) for item in result]
        require(observed == [("V-2", "Ana Fox [checkin]", True), ("V-9", "Zed Wu [runner]", False)], "display fields or order differ")

    def subprocess_cli(argv):
        completed = subprocess.run(
            [sys.executable, str(root / "badge_cli.py"), *argv],
            cwd=root,
            text=True,
            capture_output=True,
            env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
            timeout=30,
            check=False,
        )
        return completed.returncode, completed.stdout, completed.stderr

    def capture_main(argv):
        stdout, stderr = io.StringIO(), io.StringIO()
        try:
            with redirect_stdout(stdout), redirect_stderr(stderr):
                status = cli_module.main(argv)
        except SystemExit as exc:
            raise AssertionError(f"main propagated SystemExit({exc.code})") from exc
        return status, stdout.getvalue(), stderr.getvalue()

    def r7():
        modules_present()
        parameters = list(inspect.signature(cli_module.main).parameters.values())
        require(len(parameters) == 1 and parameters[0].name == "argv", "main signature name differs")
        require(parameters[0].kind is inspect.Parameter.POSITIONAL_OR_KEYWORD, "main parameter kind differs")
        require(parameters[0].default is None, "main argv default differs")
        direct = subprocess_cli([str(empty_path), str(policy_path)])
        require(direct == (0, "[]\n", ""), "direct-entry CLI success differs")
        serialization_value = [{"zeta": "café", "alpha": "雪", "nested": {"b": 2, "a": 1}}]
        stdout, stderr = io.StringIO(), io.StringIO()
        with mock.patch.object(cli_module, "build_manifest", return_value=serialization_value) as build:
            with redirect_stdout(stdout), redirect_stderr(stderr):
                status = cli_module.main([str(empty_path), str(policy_path)])
        expected = '[{"alpha":"\\u96ea","nested":{"a":1,"b":2},"zeta":"caf\\u00e9"}]\n'
        require((status, stdout.getvalue(), stderr.getvalue()) == (0, expected, ""), "isolated serialization differs")
        require(build.call_count == 1 and build.call_args.args == ([], load_json(policy_path)) and not build.call_args.kwargs, "CLI passed wrong values to build_manifest")

    def r8():
        modules_present()
        probes = [
            [],
            [str(missing_path), str(policy_path)],
            [str(malformed_path), str(policy_path)],
        ]
        for argv in probes:
            status, stdout, stderr = capture_main(argv)
            require(type(status) is int and status == 2 and stdout == "" and stderr != "", "ordinary CLI failure differs")
        with tempfile.NamedTemporaryFile() as source:
            source.write(b"\xff")
            source.flush()
            status, stdout, stderr = capture_main([source.name, str(policy_path)])
        require(type(status) is int and status == 2 and stdout == "" and stderr != "", "Unicode CLI failure differs")
        error = manifest_module.BadgeManifestError("forced application failure")
        with mock.patch.object(cli_module, "build_manifest", side_effect=error):
            status, stdout, stderr = capture_main([str(empty_path), str(policy_path)])
        require(type(status) is int and status == 2 and stdout == "" and stderr != "", "application CLI failure differs")

    def g1():
        require(
            load_json(policy_path)
            == {
                "common_area": "lobby",
                "late_shift_area": "staff-exit",
                "role_area": {"checkin": "welcome-desk", "runner": "supply-room", "setup": "main-hall"},
            },
            "protected policy literals differ",
        )
        require([item["id"] for item in load_json(attendees_path)] == ["V-104", "V-099", "V-120", "V-101"], "protected attendee order differs")
        require(load_json(empty_path) == [] and malformed_path.read_bytes() == b'{"id":\n', "protected fixture bytes differ")

    def integrity_check():
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
