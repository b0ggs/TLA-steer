#!/usr/bin/env python3
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


TASK = Path(__file__).resolve().parent


def run(workspace, *args):
    env = os.environ.copy()
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    env["PYTHONPATH"] = str(workspace)
    process = subprocess.run(
        [sys.executable, *args], cwd=workspace, env=env,
        capture_output=True, text=True, timeout=15, check=False,
    )
    return process.returncode == 0, process.stdout + process.stderr


def main():
    source = Path(sys.argv[1]).resolve()
    with tempfile.TemporaryDirectory(prefix="phase3-urljoin-") as temporary:
        workspace = Path(temporary) / "workspace"
        shutil.copytree(source, workspace)
        artifact = workspace / "tests" / "test_urljoin_relative.py"
        artifact_ok = False
        if artifact.is_file() and not artifact.is_symlink():
            passed, output = run(workspace, str(artifact))
            artifact_ok = passed and "Ran " in output and "Ran 0 tests" not in output
        for private in sorted((TASK / "private").rglob("*")):
            if private.is_file():
                target = workspace / private.relative_to(TASK / "private")
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(private, target)
        issue_ok, _ = run(workspace, "_phase3_tests.py", "issue")
        regression_ok, _ = run(workspace, "_phase3_tests.py", "regression")
    requirements = {"R1": issue_ok, "R2": artifact_ok}
    regressions = {"G1": regression_ok}
    print(json.dumps({
        "requirements": requirements,
        "regressions": regressions,
        "resolved": all(requirements.values()) and all(regressions.values()),
    }, sort_keys=True))


if __name__ == "__main__":
    main()
