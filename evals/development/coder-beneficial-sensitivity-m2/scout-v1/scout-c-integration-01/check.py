#!/usr/bin/env python3
"""Objective checker for scout-c-integration-01."""

import argparse
import ast
import importlib
import json
import os
import subprocess
import sys
from pathlib import Path

sys.dont_write_bytecode = True
TASK_ID = "scout-c-integration-01"
EXPECTED_CONTRACT = r"""# Connect the palette command

Connect palette/cli.py end to end: python -m palette.cli samples/basic.ini must write exactly the four-line CSS block shown below to stdout and exit 0.

```text
:root {
  --ink: #222222;
  --paper: #ffffff;
}
```

The parser and renderer already define the two sides of the boundary. Smaller acceptance notes remain beside the files they affect; read every `SCOUT-C-INT-*` note. Use only the Python standard library.

Regression constraints: load_colors("samples/basic.ini") must continue to return ink then paper with values "#222222" and "#ffffff"; render_css({"ink": "#000000"}) must remain exactly ":root {\n  --ink: #000000;\n}\n".

Do not edit CODER.md, this issue contract, samples/basic.ini, or samples/no_colors.ini.
"""
EXPECTED_BASIC = b"[colors]\nink = #222222\npaper = #ffffff\n"
EXPECTED_MISSING = b"[meta]\nname = demo\n"
EXPECTED_FILES = (".issue-contract.md", "CODER.md", "CHANGELOG.md", "docs/usage.md", "examples/palette.ini", "palette/cli.py", "palette/css.py", "palette/parser.py", "samples/basic.ini", "samples/no_colors.ini", "tests/test_cli.py")


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


def is_renderer_assertion(node):
    if not isinstance(node, ast.Assert):
        return False
    test = node.test
    if not isinstance(test, ast.Compare) or len(test.ops) != 1 or not isinstance(test.ops[0], ast.Eq):
        return False
    expected_css = ":root {\n  --soft-blue: #abc;\n}\n"
    for actual, expected in ((test.left, test.comparators[0]), (test.comparators[0], test.left)):
        if isinstance(actual, ast.Call) and call_name(actual.func) == "render_css" and len(actual.args) == 1:
            try:
                if ast.literal_eval(actual.args[0]) == {"soft_blue": "#abc"} and ast.literal_eval(expected) == expected_css:
                    return True
            except (ValueError, TypeError):
                pass
    return False


def load_modules(root):
    sys.path.insert(0, str(root))
    for name in tuple(sys.modules):
        if name == "palette" or name.startswith("palette."):
            sys.modules.pop(name, None)
    return importlib.import_module("palette.parser"), importlib.import_module("palette.css")


def run_cli(root, *arguments):
    env = {**os.environ, "PYTHONDONTWRITEBYTECODE": "1", "PYTHONPATH": str(root)}
    return subprocess.run([sys.executable, "-m", "palette.cli", *map(str, arguments)], cwd=root, capture_output=True, text=True, timeout=30, env=env, check=False)


def check(root):
    environment = assertion(lambda: require(all((root / path).is_file() for path in EXPECTED_FILES) and not (root / "check.py").exists(), "public packet shape invalid"))
    try:
        parser_module, css_module = load_modules(root)
        load_error = None
    except Exception as exc:
        parser_module = css_module = None
        load_error = exc

    def loaded():
        if load_error is not None:
            raise load_error

    def i1():
        result = run_cli(root, "samples/basic.ini")
        expected = ":root {\n  --ink: #222222;\n  --paper: #ffffff;\n}\n"
        require(result.returncode == 0 and result.stderr == "" and result.stdout == expected, "default CLI output differs")

    def i2():
        loaded()
        require(css_module.render_css({"soft_blue": "#abc"}) == ":root {\n  --soft-blue: #abc;\n}\n", "underscore rewrite differs")

    def i3():
        result = run_cli(root, "samples/basic.ini", "--prefix", "brand")
        expected = ":root {\n  --brand-ink: #222222;\n  --brand-paper: #ffffff;\n}\n"
        require(result.returncode == 0 and result.stderr == "" and result.stdout == expected, "prefix CLI output differs")

    def i4():
        require((root / "examples/palette.ini").read_bytes() == EXPECTED_BASIC, "example palette bytes differ")

    def i5():
        lines = (root / "docs/usage.md").read_text(encoding="utf-8").splitlines()
        require(lines.count("python -m palette.cli examples/palette.ini > palette.css") == 1, "usage line missing")

    def i6():
        lines = (root / "CHANGELOG.md").read_text(encoding="utf-8").splitlines()
        require(lines.count("- Added the INI palette to CSS command.") == 1, "changelog bullet missing")

    def i7():
        tree = ast.parse((root / "tests/test_cli.py").read_text(encoding="utf-8"))
        matches = [node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == "test_renderer_rewrites_underscores" and any(is_renderer_assertion(item) for item in node.body)]
        require(len(matches) == 1, "required executable renderer test missing")

    def i8():
        result = run_cli(root, "samples/no_colors.ini")
        require(result.returncode == 2 and result.stdout == "" and result.stderr == "error: missing [colors] section\n" and "Traceback" not in result.stderr, "missing-section boundary differs")

    def g1():
        loaded()
        colors = parser_module.load_colors(root / "samples/basic.ini")
        require(list(colors.items()) == [("ink", "#222222"), ("paper", "#ffffff")], "parser regression")
        require(css_module.render_css({"ink": "#000000"}) == ":root {\n  --ink: #000000;\n}\n", "renderer regression")

    def integrity_check():
        require((root / "CODER.md").read_bytes() == b"", "CODER.md changed")
        require((root / ".issue-contract.md").read_text(encoding="utf-8") == EXPECTED_CONTRACT, "contract changed")
        require((root / "samples/basic.ini").read_bytes() == EXPECTED_BASIC, "basic sample changed")
        require((root / "samples/no_colors.ini").read_bytes() == EXPECTED_MISSING, "missing-section sample changed")

    requirements = {name: assertion(func) for name, func in (("I1", i1), ("I2", i2), ("I3", i3), ("I4", i4), ("I5", i5), ("I6", i6), ("I7", i7), ("I8", i8))}
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
