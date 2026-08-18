#!/usr/bin/env python3
"""Objective checker for scout-a-feature-01."""

import argparse
import ast
import importlib
import json
import os
import subprocess
import sys
from pathlib import Path

sys.dont_write_bytecode = True

TASK_ID = "scout-a-feature-01"
EXPECTED_CONTRACT = """# Add JSONL severity summaries

PUBLIC-R1 (primary): Add `src/log_summary.py:summarize_jsonl` so it returns a key-sorted mapping of severity levels to counts for valid JSON object lines.

PUBLIC-R2: Normalize each level by trimming surrounding whitespace and converting it to lowercase in `normalize_level`.

PUBLIC-G1: Do not mutate the caller's input list while producing a summary.
"""
EXPECTED_FILES = (
    ".issue-contract.md",
    "CODER.md",
    "README.md",
    "CHANGELOG.md",
    "config/defaults.json",
    "docs/compatibility.md",
    "src/log_summary.py",
    "src/rendering.py",
    "tests/test_public.py",
)


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
    sys.path.insert(0, str(root / "src"))
    for name in ("log_summary", "rendering"):
        sys.modules.pop(name, None)
    return importlib.import_module("log_summary"), importlib.import_module("rendering")


_MISSING = object()


def call_name(node):
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        return node.attr
    return None


def static_value(node, values):
    if isinstance(node, ast.Name) and node.id in values:
        return values[node.id]
    try:
        return ast.literal_eval(node)
    except (ValueError, TypeError):
        return _MISSING


def equality_pairs(node):
    if isinstance(node, ast.Call) and call_name(node.func) == "assertEqual" and len(node.args) >= 2:
        return ((node.args[0], node.args[1]), (node.args[1], node.args[0]))
    expression = node.test if isinstance(node, ast.Assert) else None
    if isinstance(node, ast.Call) and call_name(node.func) == "assertTrue" and node.args:
        expression = node.args[0]
    if isinstance(expression, ast.Compare) and len(expression.ops) == 1 and isinstance(expression.ops[0], ast.Eq):
        return ((expression.left, expression.comparators[0]), (expression.comparators[0], expression.left))
    return ()


def has_plain_lowercase_assertion(source):
    tree = ast.parse(source)
    methods = [child for parent in ast.walk(tree) if isinstance(parent, ast.ClassDef) for child in parent.body if isinstance(child, ast.FunctionDef) and child.name == "test_plain_lowercase_level"]
    for method in methods:
        values = {}
        for node in ast.walk(method):
            if isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
                value = static_value(node.value, values)
                if value is not _MISSING:
                    values[node.targets[0].id] = value
        for node in ast.walk(method):
            for actual, expected in equality_pairs(node):
                if not isinstance(actual, ast.Call) or call_name(actual.func) != "normalize_level":
                    continue
                keywords = {item.arg: item.value for item in actual.keywords if item.arg}
                value_node = actual.args[0] if actual.args else keywords.get("value")
                if static_value(value_node, values) == "info" and static_value(expected, values) == "info":
                    return True
    return False


def check(root):
    environment = assertion(
        lambda: require(all((root / path).is_file() for path in EXPECTED_FILES), "required public file missing")
    )
    try:
        summary, rendering = load_modules(root)
    except Exception as exc:
        summary = rendering = None
        load_error = exc

    def modules_present():
        if summary is None:
            raise load_error

    def r1():
        modules_present()
        lines = ['{"level":"info"}', '{"level":"error"}', '{"level":"info"}']
        result = summary.summarize_jsonl(lines)
        require(list(result.items()) == [("error", 1), ("info", 2)], "summary counts are not key-sorted")

    def r2():
        modules_present()
        require(summary.normalize_level("  WARN \t") == "warn", "level normalization failed")

    def r3():
        modules_present()
        result = list(summary.iter_jsonl(["", "   ", '{"level":"info"}']))
        require(result == [{"level": "info"}], "blank JSONL lines were not ignored")

    def r4():
        data = json.loads((root / "config/defaults.json").read_text(encoding="utf-8"))
        require(data.get("missing_level") == "unknown", "missing_level default is not exact")

    def r5():
        modules_present()
        require(rendering.render_summary({"warn": 2, "error": 1}) == "error=1\nwarn=2", "rendered lines are not exact")

    def r6():
        text = (root / "docs/compatibility.md").read_text(encoding="utf-8")
        require("Summary keys and rendered lines are sorted lexically." in text.splitlines(), "compatibility sentence missing")

    def r7():
        text = (root / "CHANGELOG.md").read_text(encoding="utf-8")
        require("* Added deterministic JSONL severity summaries." in text.splitlines(), "changelog entry missing")

    def r8():
        source = (root / "tests/test_public.py").read_text(encoding="utf-8")
        require(has_plain_lowercase_assertion(source), "required plain-lowercase assertion missing")
        completed = subprocess.run(
            [sys.executable, "-m", "unittest", "discover", "-s", "tests", "-v"],
            cwd=root,
            capture_output=True,
            env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
            text=True,
            timeout=30,
            check=False,
        )
        require(completed.returncode == 0, "public tests did not pass")

    def g1():
        modules_present()
        lines = ['{"level":"info"}', '{"level":"error"}']
        before = list(lines)
        summary.summarize_jsonl(lines)
        require(lines == before, "caller input was mutated")

    def integrity_check():
        require((root / "CODER.md").read_bytes() == b"", "CODER.md is not zero-byte")
        require((root / ".issue-contract.md").read_text(encoding="utf-8") == EXPECTED_CONTRACT, "protected contract changed")

    requirements = {name: assertion(func) for name, func in (("R1", r1), ("R2", r2), ("R3", r3), ("R4", r4), ("R5", r5), ("R6", r6), ("R7", r7), ("R8", r8))}
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
