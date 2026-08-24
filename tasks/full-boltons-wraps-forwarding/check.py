#!/usr/bin/env python3
"""Overlay the upstream fix tests and run focused pytest groups."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


TASK_ROOT = Path(__file__).resolve().parent
PRIVATE = TASK_ROOT / "private"
FILES = ("tests/test_funcutils_fb.py", "tests/test_funcutils_fb_py3.py")
REQUIREMENT_TESTS = {
    "R1": (
        "tests/test_funcutils_fb_py3.py::test_wraps_defaulted_arg_keyword_forwarding",
        "tests/test_funcutils_fb.py::test_wraps_expected",
    ),
    "R2": (
        "tests/test_funcutils_fb.py::test_get_invocation_sig_str",
        "tests/test_funcutils_fb_py3.py::test_wraps_inner_kwarg_only",
        "tests/test_funcutils_fb_py3.py::test_wraps_defaulted_arg_before_varargs",
        "tests/test_funcutils_fb_py3.py::test_wraps_posonly_defaulted_arg",
    ),
}
REGRESSION_FILTER = (
    "not test_wraps_expected and not test_get_invocation_sig_str and "
    "not test_wraps_inner_kwarg_only and "
    "not test_wraps_defaulted_arg_keyword_forwarding and "
    "not test_wraps_defaulted_arg_before_varargs and "
    "not test_wraps_posonly_defaulted_arg"
)


def run_pytest(workspace: Path, selectors: tuple[str, ...], *, expression: str | None = None) -> bool:
    environment = os.environ.copy()
    environment.update({
        "PYTHONDONTWRITEBYTECODE": "1",
        "PYTEST_DISABLE_PLUGIN_AUTOLOAD": "1",
        "PYTHONHASHSEED": "0",
    })
    command = [sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider", *selectors]
    if expression is not None:
        command.extend(("-k", expression))
    try:
        result = subprocess.run(
            command,
            cwd=workspace,
            env=environment,
            capture_output=True,
            text=True,
            timeout=15,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise RuntimeError(f"pytest invocation failed: {type(exc).__name__}: {exc}") from exc
    if result.returncode not in (0, 1):
        detail = (result.stderr or result.stdout)[-1000:]
        raise RuntimeError(f"pytest infrastructure exit {result.returncode}: {detail}")
    return result.returncode == 0


def main() -> int:
    if len(sys.argv) != 2:
        raise SystemExit("usage: check.py WORKSPACE")
    source = Path(sys.argv[1]).resolve()
    with tempfile.TemporaryDirectory(prefix="full-boltons-wraps-check-") as name:
        workspace = Path(name) / "workspace"
        shutil.copytree(source, workspace)
        for relative in FILES:
            destination = workspace / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(PRIVATE / relative, destination)
        requirements = {
            key: run_pytest(workspace, selectors)
            for key, selectors in REQUIREMENT_TESTS.items()
        }
        regressions = {
            "G1": run_pytest(workspace, FILES, expression=REGRESSION_FILTER),
        }
    resolved = all((*requirements.values(), *regressions.values()))
    print(json.dumps({
        "regressions": regressions,
        "requirements": requirements,
        "resolved": resolved,
    }, sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
