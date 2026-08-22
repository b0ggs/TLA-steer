#!/usr/bin/env python3
from __future__ import annotations

import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile


ARTIFACT = Path("tests/test_dotted_keys_regression.py")
PRIVATE = Path(__file__).resolve().parent / "private"


def run_unittest(cwd: Path, target: str) -> bool:
    env = os.environ.copy()
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    env["PYTHONNOUSERSITE"] = "1"
    env["PYTHONPATH"] = str(cwd)
    try:
        result = subprocess.run(
            [sys.executable, "-m", "unittest", "-q", target],
            cwd=cwd,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=8,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return False
    return result.returncode == 0


def overlay_private(workspace: Path) -> None:
    for source in sorted(PRIVATE.rglob("*")):
        if not source.is_file():
            continue
        target = workspace / source.relative_to(PRIVATE)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)


def score(workspace: Path) -> dict[str, object]:
    requirements = {"R1": False, "R2": False, "R3": False}
    regressions = {"G1": False}
    with tempfile.TemporaryDirectory(prefix="tomli-check-") as temp_name:
        temp = Path(temp_name)

        artifact_tree = temp / "artifact-workspace"
        shutil.copytree(workspace, artifact_tree)
        artifact = artifact_tree / ARTIFACT
        artifact_bytes = artifact.read_bytes() if artifact.is_file() else b""
        requirements["R3"] = bool(artifact_bytes) and run_unittest(
            artifact_tree, "tests.test_dotted_keys_regression"
        )

        private_tree = temp / "private-workspace"
        shutil.copytree(workspace, private_tree)
        overlay_private(private_tree)
        module = "_phase3_private_tests.test_private"
        requirements["R1"] = run_unittest(
            private_tree, f"{module}.ExplicitTableBehavior"
        )
        requirements["R2"] = run_unittest(
            private_tree, f"{module}.ArrayOfTablesBehavior"
        )
        regressions["G1"] = run_unittest(
            private_tree, f"{module}.ExistingBehaviorRegression"
        )

    resolved = all(requirements.values()) and all(regressions.values())
    return {"requirements": requirements, "regressions": regressions, "resolved": resolved}


def main() -> int:
    fallback = {
        "requirements": {"R1": False, "R2": False, "R3": False},
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

