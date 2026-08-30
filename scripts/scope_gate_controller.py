#!/usr/bin/env python3
"""Minimal trusted controller required by Scope Gate's integration guide."""

from __future__ import annotations

import argparse
import base64
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import stat
import subprocess
import sys
from typing import Any, Callable, Mapping, Sequence


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
CONTRACT_PATH = REPOSITORY_ROOT / ".scope-gate/contracts/tla-steer-prototype-r1.json"
SCOPE_GATE = REPOSITORY_ROOT / ".scope-gate-venv/bin/scope-gate"
STATE_SCHEMA = "scope-gate-controller-state-v1"
RESULT_SCHEMA = "scope-gate-controller-result-v1"
EXPECTED_STATE_KEYS = {
    "schema_version",
    "repository_root",
    "expected_scope_revision",
    "contract_b64",
    "baseline_manifest",
}
TRANSIENT_DIRECTORY_NAMES = {".git", ".pytest_cache", "__pycache__"}
TRANSIENT_FILE_NAMES = {".DS_Store"}


class IntegrationError(RuntimeError):
    """A controller or Scope Gate integration failure that must fail closed."""

    def __init__(self, message: str, *, scope_gate_exit: int | None = None):
        super().__init__(message)
        self.scope_gate_exit = scope_gate_exit


def canonical_bytes(value: Any) -> bytes:
    return (
        json.dumps(value, ensure_ascii=False, separators=(",", ":"), sort_keys=True)
        + "\n"
    ).encode("utf-8")


def _reject_constant(value: str) -> None:
    raise ValueError(f"non-finite JSON number: {value}")


def _unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def strict_json(data: bytes | str, *, source: str) -> Any:
    try:
        text = data.decode("utf-8") if isinstance(data, bytes) else data
        return json.loads(
            text,
            object_pairs_hook=_unique_object,
            parse_constant=_reject_constant,
        )
    except (UnicodeDecodeError, json.JSONDecodeError, ValueError) as exc:
        raise IntegrationError(f"invalid JSON from {source}: {exc}") from exc


def _scope_gate_process(
    executable: Path,
    operation: str,
    payload: Mapping[str, Any],
) -> subprocess.CompletedProcess[bytes]:
    try:
        return subprocess.run(
            [str(executable), operation, "-"],
            input=canonical_bytes(payload),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
    except OSError as exc:
        raise IntegrationError(f"unable to execute Scope Gate: {exc}") from exc


def contract_digest(contract: Mapping[str, Any], executable: Path = SCOPE_GATE) -> str:
    unsigned = dict(contract)
    unsigned.pop("canonical_digest", None)
    process = _scope_gate_process(executable, "digest", unsigned)
    if process.returncode != 0:
        raise IntegrationError(
            f"Scope Gate digest failed with exit {process.returncode}",
            scope_gate_exit=process.returncode,
        )
    if process.stderr:
        raise IntegrationError("Scope Gate digest wrote unexpected stderr")
    output = strict_json(process.stdout, source="scope-gate digest")
    if not isinstance(output, dict) or set(output) != {
        "schema_version",
        "canonical_digest",
    }:
        raise IntegrationError("malformed Scope Gate digest output")
    if output["schema_version"] != "scope-gate-digest-v1":
        raise IntegrationError("unexpected Scope Gate digest schema")
    digest = output["canonical_digest"]
    if (
        not isinstance(digest, str)
        or len(digest) != 64
        or any(character not in "0123456789abcdef" for character in digest)
    ):
        raise IntegrationError("malformed Scope Gate digest value")
    return digest


def verify_contract(contract: Mapping[str, Any], executable: Path = SCOPE_GATE) -> None:
    stored = contract.get("canonical_digest")
    if not isinstance(stored, str) or stored != contract_digest(contract, executable):
        raise IntegrationError("contract canonical digest mismatch")
    revision = contract.get("scope_revision")
    if not isinstance(revision, str) or not revision:
        raise IntegrationError("contract scope revision is missing")


def _fingerprint(path: Path) -> str:
    metadata = path.lstat()
    if stat.S_ISLNK(metadata.st_mode):
        return "symlink:" + os.readlink(path)
    if stat.S_ISREG(metadata.st_mode):
        digest = hashlib.sha256()
        with path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(chunk)
        return "file:" + digest.hexdigest()
    return f"special:{stat.S_IFMT(metadata.st_mode):o}"


def repository_manifest(root: Path) -> dict[str, str]:
    root = root.resolve(strict=True)
    manifest: dict[str, str] = {}

    def visit(directory: Path, relative: PurePosixPath) -> None:
        try:
            entries = sorted(os.scandir(directory), key=lambda entry: entry.name)
        except OSError as exc:
            raise IntegrationError(f"cannot inspect repository path {directory}: {exc}") from exc
        for entry in entries:
            if entry.name in TRANSIENT_FILE_NAMES:
                continue
            child_relative = relative / entry.name
            child = Path(entry.path)
            if entry.is_symlink():
                manifest[child_relative.as_posix()] = _fingerprint(child)
            elif entry.is_dir(follow_symlinks=False):
                if entry.name not in TRANSIENT_DIRECTORY_NAMES:
                    visit(child, child_relative)
            else:
                if not entry.name.endswith((".pyc", ".pyo")):
                    manifest[child_relative.as_posix()] = _fingerprint(child)

    visit(root, PurePosixPath())
    return manifest


def _tracked_paths(root: Path) -> set[str]:
    try:
        process = subprocess.run(
            ["git", "-C", str(root), "ls-files", "--cached", "-z"],
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            check=False,
        )
    except OSError:
        return set()
    if process.returncode != 0:
        return set()
    try:
        return {
            item.decode("utf-8")
            for item in process.stdout.split(b"\0")
            if item
        }
    except UnicodeDecodeError as exc:
        raise IntegrationError("Git returned a non-UTF-8 tracked path") from exc


def derive_changes(
    baseline: Mapping[str, str],
    current: Mapping[str, str],
    root: Path,
) -> dict[str, Any]:
    baseline_paths = set(baseline)
    current_paths = set(current)
    added_candidates = current_paths - baseline_paths
    deleted_candidates = baseline_paths - current_paths
    modified = sorted(
        path
        for path in baseline_paths & current_paths
        if baseline[path] != current[path]
    )

    deleted_by_fingerprint: dict[str, list[str]] = {}
    for path in deleted_candidates:
        deleted_by_fingerprint.setdefault(baseline[path], []).append(path)
    added_by_fingerprint: dict[str, list[str]] = {}
    for path in added_candidates:
        added_by_fingerprint.setdefault(current[path], []).append(path)

    renamed: list[dict[str, str]] = []
    renamed_from: set[str] = set()
    renamed_to: set[str] = set()
    for fingerprint in sorted(set(deleted_by_fingerprint) & set(added_by_fingerprint)):
        sources = sorted(deleted_by_fingerprint[fingerprint])
        destinations = sorted(added_by_fingerprint[fingerprint])
        for source, destination in zip(sources, destinations):
            renamed.append({"from": source, "to": destination})
            renamed_from.add(source)
            renamed_to.add(destination)

    added = sorted(added_candidates - renamed_to)
    deleted = sorted(deleted_candidates - renamed_from)
    tracked = _tracked_paths(root)
    untracked = sorted(path for path in added_candidates if path not in tracked)
    changed_paths = sorted(added_candidates | deleted_candidates | set(modified))
    return {
        "added": added,
        "modified": modified,
        "deleted": deleted,
        "renamed": renamed,
        "untracked": untracked,
        "changed_paths": changed_paths,
    }


def _is_within(path: Path, directory: Path) -> bool:
    try:
        path.relative_to(directory)
        return True
    except ValueError:
        return False


def begin(
    *,
    root: Path,
    contract_path: Path,
    state_path: Path,
    executable: Path = SCOPE_GATE,
) -> dict[str, Any]:
    root = root.resolve(strict=True)
    state_path = state_path.resolve(strict=False)
    if _is_within(state_path, root):
        raise IntegrationError("controller state must be outside the repository")
    contract_bytes = contract_path.read_bytes()
    contract = strict_json(contract_bytes, source=str(contract_path))
    if not isinstance(contract, dict):
        raise IntegrationError("contract must be a JSON object")
    verify_contract(contract, executable)
    state = {
        "schema_version": STATE_SCHEMA,
        "repository_root": str(root),
        "expected_scope_revision": contract["scope_revision"],
        "contract_b64": base64.b64encode(contract_bytes).decode("ascii"),
        "baseline_manifest": repository_manifest(root),
    }
    try:
        descriptor = os.open(state_path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o400)
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(canonical_bytes(state))
            handle.flush()
            os.fsync(handle.fileno())
    except FileExistsError as exc:
        raise IntegrationError(f"controller state already exists: {state_path}") from exc
    except OSError as exc:
        raise IntegrationError(f"cannot write controller state: {exc}") from exc
    return state


def load_state(state_path: Path, expected_root: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    state = strict_json(state_path.read_bytes(), source=str(state_path))
    if not isinstance(state, dict) or set(state) != EXPECTED_STATE_KEYS:
        raise IntegrationError("malformed controller state")
    if state.get("schema_version") != STATE_SCHEMA:
        raise IntegrationError("unexpected controller state schema")
    root = expected_root.resolve(strict=True)
    if state.get("repository_root") != str(root):
        raise IntegrationError("controller state repository mismatch")
    baseline = state.get("baseline_manifest")
    if not isinstance(baseline, dict) or not all(
        isinstance(path, str) and isinstance(value, str)
        for path, value in baseline.items()
    ):
        raise IntegrationError("malformed baseline manifest")
    try:
        contract_bytes = base64.b64decode(state["contract_b64"], validate=True)
    except (KeyError, TypeError, ValueError) as exc:
        raise IntegrationError("malformed frozen contract bytes") from exc
    contract = strict_json(contract_bytes, source="frozen contract")
    if not isinstance(contract, dict):
        raise IntegrationError("frozen contract must be a JSON object")
    if not isinstance(state.get("expected_scope_revision"), str):
        raise IntegrationError("malformed frozen scope revision")
    return state, contract


CheckRunner = Callable[[str], int]


def _real_check(check_id: str, root: Path) -> int:
    environment = os.environ.copy()
    environment["PYTHONDONTWRITEBYTECODE"] = "1"
    if check_id == "check-focused-tests":
        environment["PYTEST_ADDOPTS"] = "-p no:cacheprovider"
        command = [
            sys.executable,
            "-m",
            "pytest",
            "-q",
            "tests/test_oracle.py",
            "tests/test_verifier.py",
            "tests/test_worker_fake.py",
            "tests/test_smc.py",
        ]
    elif check_id == "check-offline-report":
        candidates = sorted(
            path
            for path in (root / "runs").glob("*")
            if path.is_dir() and (path / "summary.json").is_file()
        )
        if not candidates:
            return 1
        selected = candidates[-1].relative_to(root).as_posix()
        environment["PYTHONPATH"] = "src"
        environment["TLA_STEER_DISABLE_MODEL_CALLS"] = "1"
        command = [sys.executable, "-m", "tla_steer", "report", selected]
    else:
        raise IntegrationError(f"controller does not implement required check: {check_id}")
    try:
        return subprocess.run(
            command,
            cwd=root,
            env=environment,
            stdin=subprocess.DEVNULL,
            stdout=None,
            stderr=None,
            check=False,
        ).returncode
    except OSError as exc:
        raise IntegrationError(f"required check {check_id} could not run: {exc}") from exc


def run_checks(
    contract: Mapping[str, Any],
    root: Path,
    check_runner: CheckRunner | None = None,
) -> list[dict[str, Any]]:
    checks = contract.get("checks")
    if not isinstance(checks, list):
        raise IntegrationError("frozen contract has malformed checks")
    runner = check_runner or (lambda check_id: _real_check(check_id, root))
    results: list[dict[str, Any]] = []
    for check in checks:
        if not isinstance(check, dict) or not isinstance(check.get("id"), str):
            raise IntegrationError("frozen contract has malformed check")
        check_id = check["id"]
        returncode = runner(check_id)
        if isinstance(returncode, bool) or not isinstance(returncode, int):
            raise IntegrationError(f"check runner returned invalid status for {check_id}")
        results.append(
            {
                "check_id": check_id,
                "status": "passed" if returncode == 0 else "failed",
                "trusted": True,
            }
        )
    return results


def validate_findings(findings: Any) -> list[dict[str, Any]]:
    if not isinstance(findings, list):
        raise IntegrationError("auditor findings must be a JSON list")
    required = {"id", "subject_type", "subject_id", "check_ids"}
    for finding in findings:
        if not isinstance(finding, dict) or not required.issubset(finding):
            raise IntegrationError("auditor finding is not structured")
    return findings


def _validate_evaluation_output(output: Any, exit_code: int) -> dict[str, Any]:
    if not isinstance(output, dict):
        raise IntegrationError("Scope Gate evaluation output is not an object")
    if output.get("schema_version") != "scope-gate-evaluation-v1":
        raise IntegrationError("unexpected Scope Gate evaluation schema")
    disposition = output.get("disposition")
    if exit_code in {0, 2}:
        expected_keys = {
            "schema_version",
            "scope_revision",
            "disposition",
            "reason_codes",
            "finding_results",
            "path_results",
            "blocking_finding_ids",
        }
        if set(output) != expected_keys:
            raise IntegrationError("malformed Scope Gate evaluation output")
        if not isinstance(output["scope_revision"], str) or not all(
            isinstance(output[field], list)
            for field in (
                "reason_codes",
                "finding_results",
                "path_results",
                "blocking_finding_ids",
            )
        ):
            raise IntegrationError("malformed Scope Gate evaluation fields")
    elif exit_code == 3:
        if set(output) != {"schema_version", "disposition", "reason_codes"}:
            raise IntegrationError("malformed Scope Gate invalid-input output")
    if (exit_code, disposition) not in {
        (0, "advisory"),
        (2, "block"),
        (3, "invalid_input"),
    }:
        raise IntegrationError(
            "Scope Gate exit code contradicts its disposition",
            scope_gate_exit=exit_code,
        )
    return output


def invoke_evaluate(
    bundle: Mapping[str, Any], executable: Path = SCOPE_GATE
) -> tuple[int, dict[str, Any]]:
    process = _scope_gate_process(executable, "evaluate", bundle)
    if process.returncode not in {0, 2, 3}:
        raise IntegrationError(
            f"unexpected Scope Gate exit {process.returncode}",
            scope_gate_exit=process.returncode,
        )
    if process.stderr:
        raise IntegrationError(
            "Scope Gate evaluation wrote unexpected stderr",
            scope_gate_exit=process.returncode,
        )
    output = strict_json(process.stdout, source="scope-gate evaluate")
    output = _validate_evaluation_output(output, process.returncode)
    if process.returncode == 3:
        raise IntegrationError(
            "Scope Gate rejected the evaluation bundle",
            scope_gate_exit=3,
        )
    return process.returncode, output


def evaluate(
    *,
    root: Path,
    state_path: Path,
    findings: Any,
    executable: Path = SCOPE_GATE,
    check_runner: CheckRunner | None = None,
) -> tuple[int, dict[str, Any]]:
    state, contract = load_state(state_path, root)
    results = run_checks(contract, root, check_runner)
    changes = derive_changes(
        state["baseline_manifest"], repository_manifest(root), root
    )
    bundle = {
        "schema_version": "scope-gate-bundle-v1",
        "expected_scope_revision": state["expected_scope_revision"],
        "contract": contract,
        "results": results,
        "findings": validate_findings(findings),
        "changed_paths": changes["changed_paths"],
    }
    scope_gate_exit, evaluation = invoke_evaluate(bundle, executable)
    checks_passed = all(
        result["trusted"] and result["status"] == "passed" for result in results
    ) and len(results) == len(contract["checks"])
    completion_allowed = scope_gate_exit == 0 and checks_passed
    controller_exit = 0 if completion_allowed else 2
    report = {
        "schema_version": RESULT_SCHEMA,
        "completion_allowed": completion_allowed,
        "controller_exit": controller_exit,
        "scope_gate_exit": scope_gate_exit,
        "check_results": results,
        "changes": changes,
        "evaluation": evaluation,
    }
    return controller_exit, report


def _load_findings_file(path: Path | None) -> list[dict[str, Any]]:
    if path is None:
        return []
    return validate_findings(strict_json(path.read_bytes(), source=str(path)))


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    begin_parser = subparsers.add_parser("begin", help="freeze contract and baseline")
    begin_parser.add_argument("--state", required=True, type=Path)
    evaluate_parser = subparsers.add_parser("evaluate", help="run checks and Scope Gate")
    evaluate_parser.add_argument("--state", required=True, type=Path)
    evaluate_parser.add_argument("--findings", type=Path)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    arguments = _parser().parse_args(argv)
    try:
        if arguments.command == "begin":
            state = begin(
                root=REPOSITORY_ROOT,
                contract_path=CONTRACT_PATH,
                state_path=arguments.state,
                executable=SCOPE_GATE,
            )
            output = {
                "schema_version": RESULT_SCHEMA,
                "baseline_captured": True,
                "scope_revision": state["expected_scope_revision"],
                "state_path": str(arguments.state.resolve()),
            }
            sys.stdout.buffer.write(canonical_bytes(output))
            return 0
        exit_code, output = evaluate(
            root=REPOSITORY_ROOT,
            state_path=arguments.state,
            findings=_load_findings_file(arguments.findings),
            executable=SCOPE_GATE,
        )
        sys.stdout.buffer.write(canonical_bytes(output))
        return exit_code
    except (IntegrationError, OSError) as exc:
        output = {
            "schema_version": RESULT_SCHEMA,
            "completion_allowed": False,
            "controller_exit": 3,
            "scope_gate_exit": getattr(exc, "scope_gate_exit", None),
            "integration_error": str(exc),
        }
        sys.stderr.buffer.write(canonical_bytes(output))
        return 3


if __name__ == "__main__":
    raise SystemExit(main())
