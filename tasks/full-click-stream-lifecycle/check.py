#!/usr/bin/env python3
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

R1_TESTS = (
    "tests/test_stream_lifecycle.py::test_wrapper_close_does_not_close_underlying_buffer",
    "tests/test_stream_lifecycle.py::test_multiple_wrappers_same_buffer",
    "tests/test_stream_lifecycle.py::test_wrapper_preserves_name_and_mode",
)
R2_TESTS = (
    "tests/test_stream_lifecycle.py::test_wrapper_del_does_not_close_underlying_buffer",
    "tests/test_stream_lifecycle.py::test_mixer_buffers_survive_wrapper_gc",
    "tests/test_stream_lifecycle.py::test_no_streammixer_del",
    "tests/test_stream_lifecycle.py::test_sequential_invokes_with_logging",
    "tests/test_stream_lifecycle.py::test_invoke_with_stream_handler_on_stderr",
    "tests/test_stream_lifecycle.py::test_invoke_with_thread_pool_and_exit",
    "tests/test_stream_lifecycle.py::test_exception_does_not_corrupt_next_invoke",
    "tests/test_stream_lifecycle.py::test_sys_streams_restored_after_exception",
)


def overlay_private(workspace: Path) -> None:
    for source in sorted(PRIVATE.rglob("*")):
        if source.is_file():
            target = workspace / source.relative_to(PRIVATE)
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, target)


def run_pytest(
    workspace: Path,
    tests: tuple[str, ...],
    *,
    extra: tuple[str, ...] = (),
    timeout: int = 12,
) -> bool:
    env = os.environ.copy()
    dependency_paths = [str(workspace / "src")]
    if SEALED_DEPS.is_dir():
        dependency_paths.append(str(SEALED_DEPS))
    env["PYTHONPATH"] = os.pathsep.join(dependency_paths)
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    env["PYTHONNOUSERSITE"] = "1"
    env["PYTEST_DISABLE_PLUGIN_AUTOLOAD"] = "1"
    command = [
        sys.executable,
        "-m",
        "pytest",
        "-q",
        "-o",
        "addopts=",
        "-p",
        "no:cacheprovider",
        *extra,
        *tests,
    ]
    try:
        result = subprocess.run(
            command,
            cwd=workspace,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=timeout,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return False
    return result.returncode == 0


def score(workspace: Path) -> dict[str, object]:
    with tempfile.TemporaryDirectory(prefix="click-stream-check-") as temp_name:
        trial = Path(temp_name) / "workspace"
        shutil.copytree(workspace, trial)
        overlay_private(trial)
        requirements = {
            "R1": run_pytest(trial, R1_TESTS),
            "R2": run_pytest(trial, R2_TESTS),
        }
        # G1 runs the complete unchanged pre-fix test tree. The private fix
        # module is ignored, and the pre-existing pager parametrization is
        # deselected because it uses a module-level shared output file and
        # external pager commands, making it environment- and cross-process-
        # dependent during host-side concurrent calibration. The remaining
        # selection is the broad upstream suite (1,280 host-side passes).
        regressions = {
            "G1": run_pytest(
                trial,
                ("tests",),
                extra=(
                    "--ignore=tests/test_stream_lifecycle.py",
                    "-k",
                    "not test_echo_via_pager",
                ),
                timeout=25,
            )
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
