from __future__ import annotations

import json
import re
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Iterable

from mdseval.hashing import sha256_file, sha256_text, tree_sha256

_TASK_ID = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*")
_MAIN_IMPORT = re.compile(r"(?m)^\s*(?:import\s+__main__\b|from\s+__main__\s+import\b)")
_SUBJECT_STATUSES = frozenset({"COMPLETED", "TIMEOUT", "NONCOMPLETION"})
_FROZEN_TASK_IDS = frozenset({
    "delivery-dispatch-manifest", "delivery-retire-legacy-quote",
    "stockroom-failed-reservation-atomic", "stockroom-low-stock-query",
})
def _write(path: Path, value: str) -> None:
    with path.open("x", encoding="utf-8") as stream:
        stream.write(value)
def _write_json(path: Path, value: object) -> None:
    _write(path, json.dumps(value, indent=2, sort_keys=True) + "\n")
def _inside(path: Path, directory: Path) -> bool:
    try:
        path.relative_to(directory)
    except ValueError:
        return False
    return True
def _as_text(value: str | bytes | None) -> str:
    if value is None:
        return ""
    return value.decode("utf-8", errors="replace") if isinstance(value, bytes) else value

def _pack_hashes(instruction: Path, manifest: Path, checker: Path,
                 fixture: Path) -> dict[str, str]:
    values = {
        "instruction_sha256": sha256_file(instruction),
        "task_manifest_sha256": sha256_file(manifest),
        "checker_sha256": sha256_file(checker),
        "fixture_sha256": tree_sha256(fixture),
    }
    values["task_sha256"] = sha256_text(json.dumps(values, sort_keys=True, separators=(",", ":")))
    return values

def _targets_main(repo: Path) -> bool:
    return any(_MAIN_IMPORT.search(path.read_text(encoding="utf-8")) is not None
               for path in repo.rglob("*.py"))

def _observation(valid: bool, resolved: bool | None, integrity: bool,
                 diagnostics: dict[str, Any]) -> dict[str, Any]:
    return {
        "observation_valid": valid,
        "objective_resolved": resolved,
        "subject_integrity": integrity,
        "diagnostics": diagnostics,
    }

def run_observation(
    *,
    task_id: str,
    checker: Path,
    repo: Path,
    artifact_dir: Path,
    instruction_path: Path,
    task_manifest_path: Path,
    subject_status: str = "COMPLETED", evidence_complete: bool = True,
    subject_integrity: bool = True,
    diagnostics: dict[str, Any] | None = None,
    timeout_seconds: int = 10,
) -> dict[str, Any]:
    checker = Path(checker)
    repo = Path(repo)
    artifact_dir = Path(artifact_dir)
    instruction_path = Path(instruction_path)
    task_manifest_path = Path(task_manifest_path)
    fixture = checker.parent / "fixture"
    if repo.is_dir() and not repo.is_symlink() and _inside(artifact_dir.resolve(), repo.resolve(strict=True)):
        raise ValueError("artifact directory must be outside the subject repo")
    if artifact_dir.exists() or artifact_dir.is_symlink():
        raise FileExistsError(f"artifact directory already exists: {artifact_dir}")
    artifact_dir.mkdir()

    stdout = ""
    stderr = ""
    started = time.monotonic()
    command = [sys.executable, str(checker), "--task", task_id, "--repo", str(repo)]
    details: dict[str, Any] = {
        "task_id": task_id,
        "subject_status": subject_status,
        "command": command,
        "checker_exit_code": None,
        "instruction_sha256": None,
        "task_manifest_sha256": None,
        "checker_sha256": None,
        "fixture_sha256": None,
        "task_sha256": None,
        "repo_tree_sha256": None,
        "failure_class": None,
    }
    def finish(valid: bool, resolved: bool | None, failure: str | None) -> dict[str, Any]:
        details["failure_class"] = failure
        details["duration_seconds"] = round(time.monotonic() - started, 6)
        _write_json(artifact_dir / "command.json", {"argv": command, "timeout_seconds": timeout_seconds})
        _write(artifact_dir / "stdout.txt", stdout)
        _write(artifact_dir / "stderr.txt", stderr)
        result = _observation(valid, resolved, subject_integrity, details)
        _write_json(artifact_dir / "observation.json", result)
        return result
    try:
        details["subject_diagnostics"] = json.loads(json.dumps(diagnostics or {}))
        if (
            type(evidence_complete) is not bool
            or type(subject_integrity) is not bool
            or subject_status not in _SUBJECT_STATUSES
            or type(timeout_seconds) is not int
            or timeout_seconds <= 0
        ):
            return finish(False, None, "INVALID_CALLER_EVIDENCE")
        if not evidence_complete:
            return finish(False, None, "MISSING_EVIDENCE")
        if _TASK_ID.fullmatch(task_id) is None:
            return finish(False, None, "UNSAFE_TASK_ID")
        if (
            checker.is_symlink()
            or not checker.is_file()
            or instruction_path.is_symlink()
            or not instruction_path.is_file()
            or task_manifest_path.is_symlink()
            or not task_manifest_path.is_file()
            or fixture.is_symlink()
            or not fixture.is_dir()
            or repo.is_symlink()
            or not repo.is_dir()
        ):
            return finish(False, None, "UNSAFE_INPUT_PATH")
        checker_real = checker.resolve(strict=True)
        repo_real = repo.resolve(strict=True)
        instruction_real = instruction_path.resolve(strict=True)
        manifest_real = task_manifest_path.resolve(strict=True)
        fixture_real = fixture.resolve(strict=True)
        if checker_real.parent != manifest_real.parent or any(
            _inside(path, repo_real)
            for path in (checker_real, instruction_real, manifest_real, fixture_real, artifact_dir.resolve())
        ):
            return finish(False, None, "UNSAFE_INPUT_BOUNDARY")
        manifest = json.loads(task_manifest_path.read_text(encoding="utf-8"))
        task_ids = {item.get("id") for item in manifest.get("tasks", []) if isinstance(item, dict)}
        if task_id not in task_ids:
            return finish(False, None, "TASK_NOT_IN_MANIFEST")
        before_pack = _pack_hashes(instruction_real, manifest_real, checker_real, fixture_real)
        details.update(before_pack)
        before_hash = tree_sha256(repo)
        details["repo_tree_sha256"] = before_hash
        targets_main = _targets_main(repo_real)
    except (OSError, ValueError, TypeError, json.JSONDecodeError) as exc:
        details["error"] = type(exc).__name__
        return finish(False, None, "INVALID_INPUT_EVIDENCE")
    command = [sys.executable, str(checker_real), "--task", task_id, "--repo", str(repo_real)]
    details["command"] = command
    try:
        process = subprocess.run(
            command,
            cwd=checker_real.parent,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=timeout_seconds,
            check=False,
        )
        stdout, stderr = process.stdout, process.stderr
        details["checker_exit_code"] = process.returncode
    except subprocess.TimeoutExpired as exc:
        stdout, stderr = _as_text(exc.stdout), _as_text(exc.stderr)
        return finish(False, None, "CHECKER_TIMEOUT")
    except OSError as exc:
        details["error"] = type(exc).__name__
        return finish(False, None, "CHECKER_CRASH")
    try:
        payload = json.loads(stdout)
        if not isinstance(payload, dict) or payload.get("task") != task_id:
            raise ValueError("checker evidence mismatch")
        checker_resolved = payload.get("resolved")
        subject_error = (payload.get("acceptance") is False
                         and payload.get("regressions") is False
                         and isinstance(payload.get("error"), str))
        if type(checker_resolved) is not bool:
            if process.returncode != 1 or not subject_error:
                raise ValueError("checker evidence mismatch")
            checker_resolved = False
        elif process.returncode != (0 if checker_resolved else 1):
            raise ValueError("checker evidence mismatch")
    except (KeyError, TypeError, ValueError, json.JSONDecodeError, OSError) as exc:
        details["error"] = type(exc).__name__
        return finish(False, None, "MALFORMED_CHECKER_EVIDENCE")
    changes = ["subject-imported-__main__"] if targets_main else []
    try:
        if _pack_hashes(instruction_real, manifest_real, checker_real, fixture_real) != before_pack:
            changes.append("protected-task-pack")
        if tree_sha256(repo_real) != before_hash:
            changes.append("subject-repo")
    except (OSError, ValueError) as exc:
        details["post_hash_error"] = type(exc).__name__
        changes.append("protected-task-pack")
    if changes:
        subject_integrity = False
        details["integrity_changes"] = changes
    subject_failed = subject_status != "COMPLETED" or not subject_integrity
    details["checker_resolved"] = checker_resolved
    failure = "SUBJECT_FAILURE" if subject_failed or not checker_resolved else None
    return finish(True, False if subject_failed else checker_resolved, failure)

def compare_pilot(
    left_observations: Iterable[dict[str, Any]],
    right_observations: Iterable[dict[str, Any]],
) -> dict[str, Any]:
    def index(items: Iterable[dict[str, Any]]) -> tuple[dict[str, dict[str, Any]], bool]:
        result: dict[str, dict[str, Any]] = {}
        sound = True
        for item in items:
            task_id = item.get("diagnostics", {}).get("task_id") if isinstance(item, dict) else None
            if not isinstance(task_id, str) or task_id in result:
                sound = False
            else:
                result[task_id] = item
        return result, sound

    left, left_sound = index(left_observations)
    right, right_sound = index(right_observations)
    paired = (left_sound and right_sound and set(left) == _FROZEN_TASK_IDS
              and set(right) == _FROZEN_TASK_IDS)
    valid = paired and all(
        side[task].get("observation_valid") is True
        and type(side[task].get("objective_resolved")) is bool
        for task in left
        for side in (left, right)
    )
    return {
        "status": "PILOT" if valid else "INCONCLUSIVE",
        "task_ids": sorted(set(left) | set(right)),
        "resolved_counts": {
            "left": sum(item.get("objective_resolved") is True for item in left.values() if item.get("observation_valid") is True),
            "right": sum(item.get("objective_resolved") is True for item in right.values() if item.get("observation_valid") is True),
        } if valid else None,
        "valid_counts": {
            "left": sum(item.get("observation_valid") is True for item in left.values()),
            "right": sum(item.get("observation_valid") is True for item in right.values()),
        },
    }
