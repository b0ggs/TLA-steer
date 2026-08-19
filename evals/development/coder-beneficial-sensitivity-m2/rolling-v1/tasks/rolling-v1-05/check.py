#!/usr/bin/env python3
"""Objective checker for rolling-v1-05 (durafmt bug-fix).

Usage: python check.py <workspace-path>

Runs each requirement in an isolated subprocess and emits canonical
``scout-check-result-v1`` JSON.

Every asserted value, path, message string, and format below is stated
verbatim in the workspace's public files (.issue-contract.md, README.md,
docs/upgrading.md, CHANGELOG.md, examples/basic.py, tests/test_public.py).
Stdlib only; read-only with respect to the workspace (PYTHONDONTWRITEBYTECODE
prevents bytecode being written into the scanned tree).
"""

import ast
import hashlib
import json
import os
import subprocess
import sys

TIMEOUT = 60
TASK_ID = "rolling-v1-05"
EXPECTED_FILES = {
    ".issue-contract.md",
    "CHANGELOG.md",
    "CODER.md",
    "README.md",
    "docs/upgrading.md",
    "durafmt/__init__.py",
    "durafmt/config.py",
    "durafmt/formatter.py",
    "durafmt/parser.py",
    "examples/basic.py",
    "tests/__init__.py",
    "tests/test_public.py",
}
EXPECTED_PROTECTED_SHA256 = {
    ".issue-contract.md": "e8326bb61adf8f9a16f8197355d4af12c0cf1ff5d8b4ab0c711dd71ee1092667",
    "CODER.md": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    "docs/upgrading.md": "f8aa5fdbae9ecf4bcfa0318a6837bafcf50bdf8a97f12bfdc8ba67b706635961",
    "tests/__init__.py": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
}


def require(condition, message):
    if not condition:
        raise AssertionError(message)


def assertion(function, workspace):
    try:
        require(function(workspace), "objective predicate returned false")
        return {"passed": True, "details": "objective assertion passed"}
    except Exception as exc:
        return {"passed": False, "details": f"{type(exc).__name__}: {exc}"}


def _env(workspace):
    env = dict(os.environ)
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    env["PYTHONPATH"] = workspace
    return env


def _run(workspace, argv):
    """Run a python subprocess in the workspace; return CompletedProcess or None."""
    try:
        return subprocess.run(
            [sys.executable, "-B"] + argv,
            cwd=workspace,
            env=_env(workspace),
            capture_output=True,
            text=True,
            timeout=TIMEOUT,
        )
    except (subprocess.TimeoutExpired, OSError):
        return None


def run_code(workspace, code):
    proc = _run(workspace, ["-c", code])
    return proc is not None and proc.returncode == 0


def read_text(workspace, rel):
    try:
        with open(os.path.join(workspace, rel), encoding="utf-8") as fh:
            return fh.read()
    except (OSError, UnicodeDecodeError):
        return None


# --- Requirements -----------------------------------------------------------

def r1_minute_fix(ws):
    # .issue-contract.md (TRIAL-A-1): parse("90m") == 5400, parse("1h30m") == 5400
    return run_code(ws, (
        "import durafmt\n"
        "assert durafmt.parse('90m') == 5400\n"
        "assert durafmt.parse('1h30m') == 5400\n"
    ))


def r2_empty_message(ws):
    # docs/upgrading.md (TRIAL-A-2): parse("") raises ValueError('empty duration string')
    return run_code(ws, (
        "import durafmt\n"
        "try:\n"
        "    durafmt.parse('')\n"
        "except ValueError as exc:\n"
        "    assert str(exc) == 'empty duration string', str(exc)\n"
        "else:\n"
        "    raise AssertionError('no ValueError raised')\n"
    ))


def r3_zero_format(ws):
    # docs/upgrading.md (TRIAL-A-3): format_duration(0) == "0s"
    return run_code(ws, (
        "import durafmt\n"
        "assert durafmt.format_duration(0) == '0s'\n"
    ))


def r4_docstring(ws):
    # docs/upgrading.md (TRIAL-A-4): docstring contains the exact sentence.
    return run_code(ws, (
        "from durafmt import formatter\n"
        "doc = formatter.format_duration.__doc__ or ''\n"
        "assert 'Returns \"0s\" for a zero duration.' in doc\n"
    ))


def r5_precision(ws):
    # docs/upgrading.md (TRIAL-A-5): DEFAULT_PRECISION changed from 2 to 3.
    return run_code(ws, (
        "from durafmt import config\n"
        "assert config.DEFAULT_PRECISION == 3\n"
    ))


def r6_version(ws):
    # docs/upgrading.md (TRIAL-A-6): __version__ bumped to "1.2.1".
    return run_code(ws, (
        "import durafmt\n"
        "assert durafmt.__version__ == '1.2.1'\n"
    ))


def r7_changelog(ws):
    # TRIAL-A-7: the exact two-line section is directly above [1.2.0].
    text = read_text(ws, "CHANGELOG.md")
    if text is None:
        return False
    heading = "## [1.2.1] - Unreleased"
    entry = "- Fixed: minute multiplier in the duration parser (TRIAL-A-7)"
    prior = "## [1.2.0] - 2026-05-02"
    nonempty = [line for line in text.splitlines() if line]
    return (
        nonempty.count(heading) == 1
        and nonempty.count(entry) == 1
        and nonempty.count(prior) == 1
        and any(
            nonempty[index:index + 3] == [heading, entry, prior]
            for index in range(len(nonempty) - 2)
        )
    )


def r8_readme(ws):
    # docs/upgrading.md (TRIAL-A-8): README example shows 5400; 4500 gone.
    text = read_text(ws, "README.md")
    if text is None:
        return False
    lines = text.splitlines()
    snippet = any(
        lines[index:index + 2] == ['>>> durafmt.parse("90m")', "5400"]
        for index in range(len(lines) - 1)
    )
    return snippet and "4500" not in text


def r9_example(ws):
    # docs/upgrading.md (TRIAL-A-9): examples/basic.py exits 0, prints exactly
    # one line: total: 5400
    proc = _run(ws, ["examples/basic.py"])
    return (
        proc is not None
        and proc.returncode == 0
        and proc.stdout == "total: 5400\n"
        and proc.stderr == ""
    )


def _is_parse_days_call(node):
    return (
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "parse"
        and len(node.args) == 1
        and not node.keywords
        and isinstance(node.args[0], ast.Constant)
        and node.args[0].value == "2d"
    )


def _is_172800(node):
    return isinstance(node, ast.Constant) and node.value == 172800


def _method_asserts_parse_days(method):
    for node in ast.walk(method):
        if (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and node.func.attr == "assertEqual"
            and len(node.args) >= 2
            and (
                (_is_parse_days_call(node.args[0]) and _is_172800(node.args[1]))
                or (_is_172800(node.args[0]) and _is_parse_days_call(node.args[1]))
            )
        ):
            return True
        if (
            isinstance(node, ast.Assert)
            and isinstance(node.test, ast.Compare)
            and len(node.test.ops) == 1
            and isinstance(node.test.ops[0], ast.Eq)
            and len(node.test.comparators) == 1
            and (
                (_is_parse_days_call(node.test.left) and _is_172800(node.test.comparators[0]))
                or (_is_172800(node.test.left) and _is_parse_days_call(node.test.comparators[0]))
            )
        ):
            return True
    return False


def r10_new_test(ws):
    # TRIAL-A-10: the named TestParse method contains the stated assertion.
    text = read_text(ws, "tests/test_public.py")
    if text is None:
        return False
    try:
        tree = ast.parse(text)
    except SyntaxError:
        return False
    methods = [
        item
        for node in tree.body
        if isinstance(node, ast.ClassDef) and node.name == "TestParse"
        for item in node.body
        if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef))
        and item.name == "test_parse_days"
    ]
    if len(methods) != 1 or not _method_asserts_parse_days(methods[0]):
        return False
    proc = _run(ws, ["-m", "unittest", "tests.test_public.TestParse.test_parse_days"])
    return proc is not None and proc.returncode == 0


# --- Regressions (behaviour that must keep working) -------------------------

def g1_parse_regressions(ws):
    # .issue-contract.md: parse("1h") == 3600 and parse("45s") == 45
    return run_code(ws, (
        "import durafmt\n"
        "assert durafmt.parse('1h') == 3600\n"
        "assert durafmt.parse('45s') == 45\n"
    ))


def g2_format_regression(ws):
    # .issue-contract.md: format_duration(3661) == "1h 1m 1s"
    return run_code(ws, (
        "import durafmt\n"
        "assert durafmt.format_duration(3661) == '1h 1m 1s'\n"
    ))


REQUIREMENTS = [
    ("R1", r1_minute_fix),
    ("R2", r2_empty_message),
    ("R3", r3_zero_format),
    ("R4", r4_docstring),
    ("R5", r5_precision),
    ("R6", r6_version),
    ("R7", r7_changelog),
    ("R8", r8_readme),
    ("R9", r9_example),
    ("R10", r10_new_test),
]

REGRESSIONS = [
    ("G1", g1_parse_regressions),
    ("G2", g2_format_regression),
]


def environment_check(workspace):
    actual = set()
    for directory, directories, files in os.walk(workspace):
        directories[:] = [
            name for name in directories
            if name not in {".git", "__pycache__"}
        ]
        for name in files:
            path = os.path.join(directory, name)
            relative = os.path.relpath(path, workspace).replace(os.sep, "/")
            parts = relative.split("/")
            if parts[0] == ".git" or "__pycache__" in parts:
                continue
            if os.path.splitext(name)[1] in {".pyc", ".pyo"}:
                continue
            actual.add(relative)
    return actual == EXPECTED_FILES


def integrity_check(workspace):
    for relative, expected in EXPECTED_PROTECTED_SHA256.items():
        path = os.path.join(workspace, relative)
        with open(path, "rb") as source:
            actual = hashlib.sha256(source.read()).hexdigest()
        if actual != expected:
            return False
    with open(os.path.join(workspace, "CODER.md"), "rb") as source:
        return source.read() == b""


def check(workspace):
    requirements = {
        key: assertion(function, workspace)
        for key, function in REQUIREMENTS
    }
    regressions = {
        key: assertion(function, workspace)
        for key, function in REGRESSIONS
    }
    environment = assertion(environment_check, workspace)
    integrity = assertion(integrity_check, workspace)
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
    if len(sys.argv) != 2:
        print("usage: check.py <workspace-path>", file=sys.stderr)
        return 2
    workspace = os.path.abspath(sys.argv[1])
    if not os.path.isdir(workspace):
        print(f"not a directory: {workspace}", file=sys.stderr)
        return 2

    print(json.dumps(
        check(workspace),
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ))
    return 0


if __name__ == "__main__":
    sys.exit(main())
