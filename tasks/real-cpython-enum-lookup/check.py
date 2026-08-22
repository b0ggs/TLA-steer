#!/usr/bin/env python3
"""Run private enum regression tests without mutating the supplied tree."""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path
from tempfile import TemporaryDirectory


ARTIFACT = Path("tests/test_enum_lookup_regression.py")
BEHAVIOR_TESTS = (
    "tests.test_enum_lookup_regression.EnumLookupRegressionTests."
    "test_nonhashable_matches_hashable",
)
REGRESSION_TESTS = (
    "tests.test_enum_lookup_regression.EnumLookupRegressionTests."
    "test_hashable_lookup_and_alias_still_work",
    "tests.test_enum_lookup_regression.EnumLookupRegressionTests."
    "test_unhashable_member_lookup_still_works",
)


def run_tests(root: Path, names: tuple[str, ...], environment: dict[str, str]) -> bool:
    process = subprocess.run(
        [sys.executable, "-m", "unittest", "-q", *names],
        cwd=root,
        env=environment,
        capture_output=True,
        timeout=12,
        check=False,
    )
    return process.returncode == 0


def artifact_passes(root: Path, environment: dict[str, str]) -> bool:
    artifact = root / ARTIFACT
    if not artifact.is_file() or artifact.is_symlink():
        return False
    data = artifact.read_bytes()
    try:
        compile(data, ARTIFACT.as_posix(), "exec")
    except (SyntaxError, ValueError, TypeError):
        return False
    artifact_environment = environment.copy()
    artifact_environment["PYTHONPATH"] = str(root)
    process = subprocess.run(
        [sys.executable, str(artifact)],
        cwd=root,
        env=artifact_environment,
        capture_output=True,
        timeout=12,
        check=False,
    )
    output = process.stdout + process.stderr
    return process.returncode == 0 and re.search(rb"Ran [1-9][0-9]* test", output) is not None


def main() -> int:
    workspace = Path(sys.argv[1]).resolve()
    private = Path(__file__).resolve().parent / "private"
    with TemporaryDirectory(prefix="phase3-enum-") as temporary:
        root = Path(temporary) / "workspace"
        shutil.copytree(workspace, root)

        environment = os.environ.copy()
        environment["PYTHONDONTWRITEBYTECODE"] = "1"
        artifact_ok = artifact_passes(root, environment)

        for source in sorted(path for path in private.rglob("*") if path.is_file()):
            target = root / source.relative_to(private)
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, target)

        environment["PYTHONPATH"] = str(root)
        requirements = {
            "R1": run_tests(root, BEHAVIOR_TESTS, environment),
            "R2": artifact_ok,
        }
        regressions = {"G1": run_tests(root, REGRESSION_TESTS, environment)}
        result = {
            "regressions": regressions,
            "requirements": requirements,
            "resolved": all((*requirements.values(), *regressions.values())),
        }
        print(json.dumps(result, sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
