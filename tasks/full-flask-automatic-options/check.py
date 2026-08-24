#!/usr/bin/env python3
"""Overlay the landed regression tests and run Flask's real pytest suite."""

from __future__ import annotations

import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile


PRIVATE = Path(__file__).resolve().parent / "private"
SEALED_DEPS = Path("/sealed-deps")
PRIVATE_FILES = (
    "tests/test_basic.py",
    "tests/test_blueprints.py",
    "tests/test_cli.py",
    "tests/test_views.py",
)
R1_TESTS = (
    "tests/test_basic.py::test_provide_automatic_options_attr_enable",
)
R2_TESTS = (
    "tests/test_views.py::test_view_provide_automatic_options_attr_enable",
)
REGRESSION_TESTS = (
    "tests/test_basic.py",
    "tests/test_views.py",
)
REGRESSION_FILTER = (
    "not test_provide_automatic_options_attr_enable and "
    "not test_view_provide_automatic_options_attr_enable and "
    "not test_session and not test_extended_flashing"
)


def overlay_private(workspace: Path) -> None:
    for relative in PRIVATE_FILES:
        source = PRIVATE / relative
        destination = workspace / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination)


def run_pytest(
    workspace: Path,
    selectors: tuple[str, ...],
    *,
    expression: str | None = None,
    timeout: int = 12,
) -> bool:
    environment = os.environ.copy()
    dependency_paths = [str(workspace / "src")]
    if SEALED_DEPS.is_dir():
        dependency_paths.append(str(SEALED_DEPS))
    environment["PYTHONPATH"] = os.pathsep.join(dependency_paths)
    environment["PYTHONDONTWRITEBYTECODE"] = "1"
    environment["PYTHONNOUSERSITE"] = "1"
    environment["PYTEST_DISABLE_PLUGIN_AUTOLOAD"] = "1"
    command = [
        sys.executable,
        "-m",
        "pytest",
        "-q",
        "-o",
        "addopts=",
        "-p",
        "no:cacheprovider",
        *selectors,
    ]
    if expression is not None:
        command.extend(("-k", expression))
    try:
        result = subprocess.run(
            command,
            cwd=workspace,
            env=environment,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=timeout,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return False
    return result.returncode == 0


def score(workspace: Path) -> dict[str, object]:
    with tempfile.TemporaryDirectory(prefix="flask-options-check-") as temp_name:
        trial = Path(temp_name) / "workspace"
        shutil.copytree(workspace, trial)
        overlay_private(trial)
        requirements = {
            "R1": run_pytest(trial, R1_TESTS),
            "R2": run_pytest(trial, R2_TESTS),
        }
        # The two full modules provide a broad unchanged regression group. The
        # requirement nodes are removed, as are session-cookie cases whose
        # pre-fix tree requires Werkzeug's newer ``partitioned`` argument and
        # therefore vary with the unsealed host's installed Werkzeug version.
        regressions = {
            "G1": run_pytest(
                trial,
                REGRESSION_TESTS,
                expression=REGRESSION_FILTER,
                timeout=25,
            ),
        }
    return {
        "requirements": requirements,
        "regressions": regressions,
        "resolved": all((*requirements.values(), *regressions.values())),
    }


def main() -> int:
    fallback = {
        "requirements": {"R1": False, "R2": False},
        "regressions": {"G1": False},
        "resolved": False,
    }
    try:
        workspace = Path(sys.argv[1]).resolve()
        result = score(workspace) if workspace.is_dir() else fallback
    except (IndexError, OSError, UnicodeError):
        result = fallback
    print(json.dumps(result, sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
