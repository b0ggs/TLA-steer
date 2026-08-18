#!/usr/bin/env python3
"""Objective checker for scout-c-bug-01."""

import argparse
import ast
import configparser
import importlib
import json
import sys
from pathlib import Path

sys.dont_write_bytecode = True
TASK_ID = "scout-c-bug-01"
EXPECTED_CONTRACT = """# Repair zero-degree compass labels

Repair direction_name in src/starmap/compass.py so direction_name(0) returns "N" while direction_name(None) still returns "unknown".

This is the salient defect. The smaller acceptance notes are deliberately kept beside the source, test, configuration, documentation, example, and changelog files they affect. Read every `SCOUT-C-BUG-*` note before editing. Use only the Python standard library.

Regression constraints: direction_name(90), direction_name(180), and direction_name(270) must remain "E", "S", and "W"; normalize_degrees(15) and normalize_degrees(450) must remain 15 and 90.

Do not edit CODER.md, this issue contract, or samples/readings.json.
"""
EXPECTED_SAMPLE = b'[{"bearing":0,"label":"dock"},{"bearing":90,"label":"gate"}]\n'
EXPECTED_FILES = (".issue-contract.md", "CODER.md", "CHANGELOG.md", "config/display.ini", "docs/compass.md", "examples/compass.txt", "samples/readings.json", "src/starmap/__init__.py", "src/starmap/angles.py", "src/starmap/compass.py", "tests/test_compass.py")


def assertion(function):
    try:
        function()
        return {"passed": True, "details": "objective assertion passed"}
    except Exception as exc:
        return {"passed": False, "details": f"{type(exc).__name__}: {exc}"}


def require(condition, message):
    if not condition:
        raise AssertionError(message)


def call_name(node):
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        return node.attr
    return None


def is_zero_test(function):
    if len(function.body) != 1 or not isinstance(function.body[0], ast.Assert):
        return False
    test = function.body[0].test
    if not isinstance(test, ast.Compare) or len(test.ops) != 1 or not isinstance(test.ops[0], ast.Eq):
        return False
    pairs = ((test.left, test.comparators[0]), (test.comparators[0], test.left))
    for actual, expected in pairs:
        if isinstance(actual, ast.Call) and call_name(actual.func) == "direction_name" and len(actual.args) == 1:
            try:
                if ast.literal_eval(actual.args[0]) == 0 and ast.literal_eval(expected) == "N":
                    return True
            except (ValueError, TypeError):
                pass
    return False


def load_modules(root):
    sys.path.insert(0, str(root / "src"))
    for name in tuple(sys.modules):
        if name == "starmap" or name.startswith("starmap."):
            sys.modules.pop(name, None)
    package = importlib.import_module("starmap")
    return package, importlib.import_module("starmap.angles"), importlib.import_module("starmap.compass")


def check(root):
    environment = assertion(lambda: require(all((root / path).is_file() for path in EXPECTED_FILES) and not (root / "check.py").exists(), "public packet shape invalid"))
    try:
        package, angles, compass = load_modules(root)
        load_error = None
    except Exception as exc:
        package = angles = compass = None
        load_error = exc

    def loaded():
        if load_error is not None:
            raise load_error

    def b1():
        loaded()
        require(compass.direction_name(0) == "N" and compass.direction_name(None) == "unknown", "zero/missing behavior differs")

    def b2():
        loaded()
        require(angles.normalize_degrees(-450) == 270, "negative normalization differs")

    def b3():
        parser = configparser.ConfigParser()
        parser.read(root / "config/display.ini", encoding="utf-8")
        require(parser.get("display", "north_label", fallback=None) == "N", "north_label setting differs")

    def b4():
        lines = (root / "docs/compass.md").read_text(encoding="utf-8").splitlines()
        require(lines.count("A numeric bearing of 0 is north; only a missing bearing is unknown.") == 1, "compass sentence missing")

    def b5():
        lines = (root / "CHANGELOG.md").read_text(encoding="utf-8").splitlines()
        require(lines.count("- Fixed zero-degree bearings being displayed as unknown.") == 1, "changelog bullet missing")

    def b6():
        tree = ast.parse((root / "tests/test_compass.py").read_text(encoding="utf-8"))
        matches = [node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == "test_zero_degrees_is_north" and is_zero_test(node)]
        require(len(matches) == 1, "required executable zero-degree test missing")

    def b7():
        loaded()
        exported = getattr(package, "direction_name", None)
        require(callable(exported) and exported(90) == "E", "package export missing")

    def b8():
        require((root / "examples/compass.txt").read_bytes() == b"0 -> N\n90 -> E\n", "example bytes differ")

    def g1():
        loaded()
        require([compass.direction_name(value) for value in (90, 180, 270)] == ["E", "S", "W"], "cardinal regression")
        require([angles.normalize_degrees(value) for value in (15, 450)] == [15, 90], "normalization regression")

    def integrity_check():
        require((root / "CODER.md").read_bytes() == b"", "CODER.md changed")
        require((root / ".issue-contract.md").read_text(encoding="utf-8") == EXPECTED_CONTRACT, "contract changed")
        require((root / "samples/readings.json").read_bytes() == EXPECTED_SAMPLE, "sample changed")

    requirements = {name: assertion(func) for name, func in (("B1", b1), ("B2", b2), ("B3", b3), ("B4", b4), ("B5", b5), ("B6", b6), ("B7", b7), ("B8", b8))}
    regressions = {"G1": assertion(g1)}
    integrity = assertion(integrity_check)
    resolved = environment["passed"] and integrity["passed"] and all(item["passed"] for item in requirements.values()) and all(item["passed"] for item in regressions.values())
    return {"environment": environment, "integrity": integrity, "regressions": regressions, "requirements": requirements, "resolved": resolved, "schema": "scout-check-result-v1", "task_id": TASK_ID}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("workspace", type=Path)
    args = parser.parse_args()
    print(json.dumps(check(args.workspace.resolve()), sort_keys=True, separators=(",", ":")))


if __name__ == "__main__":
    main()
