"""Offline-only plumbing smoke for the M2 six-task scout."""

from __future__ import annotations

import json
import errno
import os
import shutil
import sys
import tempfile
import time
from dataclasses import asdict
from pathlib import Path, PurePosixPath
from types import SimpleNamespace
from typing import Any

from .capture import Redactor, capture_git, redact_event_stream
from .config import JudgeConfig, RunnerConfig
from .fixtures import audit_final_subject_tree
from .gitutils import init_repository, run_git, safe_process_environment
from .hashing import sha256_bytes, sha256_file, sha256_text, tree_sha256
from .processutils import ProcessOutcome, run_process_group
from .runner.codex_cli import build_codex_command, doctor, isolated_environment
from .wrapper import WRAPPER_PROMPT


CONFIG_SCHEMA = "mdseval.coder-beneficial-sensitivity-m2-scout-config-v1"
MANIFEST_SCHEMA = "mdseval.coder-beneficial-sensitivity-m2-scout-manifest-v1"
EXECUTION_SCHEMA = "mdseval.coder-beneficial-sensitivity-m2-scout-execution-v1"
REPLAY_SCHEMA = "mdseval.coder-beneficial-sensitivity-m2-scout-replay-v1"
COMPARISON_SCHEMA = "mdseval.coder-beneficial-sensitivity-m2-scout-comparison-v1"
RECEIPT_SCHEMA = "mdseval.coder-beneficial-sensitivity-m2-scout-receipt-v1"
CHECK_SCHEMA = "mdseval.coder-beneficial-sensitivity-m2-scout-check-v1"
COHORT_SCHEMA = "mdseval.coder-beneficial-sensitivity-m2-scout-cohort-v1"
QUALIFICATION_TASK_SCHEMA = "mdseval.coder-beneficial-sensitivity-m2-qualification-task-v1"
QUALIFICATION_MANIFEST_SCHEMA = "mdseval.coder-beneficial-sensitivity-m2-qualification-manifest-v1"
QUALIFICATION_SUMMARY_SCHEMA = "mdseval.coder-beneficial-sensitivity-m2-qualification-summary-v1"
LIVE_LAUNCH_SCHEMA = "mdseval.coder-beneficial-sensitivity-m2-live-launch-v1"
SCOUT_REPORT_SCHEMA = "mdseval.coder-beneficial-sensitivity-m2-scout-report-v1"
FIDELITY_CLEARANCE_SCHEMA = "mdseval.coder-beneficial-sensitivity-m2-fidelity-clearance-v1"
LAUNCH_FIDELITY_SCHEMA = "mdseval.coder-beneficial-sensitivity-m2-launch-fidelity-v1"
ROLLING_CANDIDATE_SCHEMA = "mdseval.coder-beneficial-sensitivity-m2-rolling-candidate-v1"
ROLLING_CLEARANCE_SCHEMA = "mdseval.coder-beneficial-sensitivity-m2-rolling-semantic-clearance-v1"
ROLLING_AUTHORIZATION_SCHEMA = "mdseval.coder-beneficial-sensitivity-m2-rolling-authorization-v1"
ROLLING_STATE_SCHEMA = "mdseval.coder-beneficial-sensitivity-m2-rolling-state-v1"
ROLLING_TASK_REPORT_SCHEMA = "mdseval.coder-beneficial-sensitivity-m2-rolling-task-report-v1"
ROLLING_RECORD_SCHEMA = "mdseval.coder-beneficial-sensitivity-m2-rolling-record-v1"
ROLLING_MANIFEST_SCHEMA = "mdseval.coder-beneficial-sensitivity-m2-rolling-manifest-v1"
ROLLING_HEADER_SCHEMA = "mdseval.coder-beneficial-sensitivity-m2-rolling-header-v1"
ROLLING_DISPOSITION_SCHEMA = "mdseval.coder-beneficial-sensitivity-m2-rolling-disposition-v1"
ROLLING_SUMMARY_SCHEMA = "mdseval.coder-beneficial-sensitivity-m2-rolling-summary-v1"

FAKE_SUBJECT_SOURCE = '''\
from __future__ import annotations
import hashlib
import sys
from pathlib import Path

repo = Path(sys.argv[1])
expected_wrapper_sha256 = sys.argv[2]
wrapper = sys.stdin.read()
if hashlib.sha256(wrapper.encode("utf-8")).hexdigest() != expected_wrapper_sha256:
    print("wrapper hash mismatch", file=sys.stderr)
    raise SystemExit(3)
(repo / "src/work.txt").write_text("DONE\\n", encoding="utf-8")
print("IMPLEMENTED")
print("Synthetic offline smoke completed.")
'''

CHECKER_SOURCE = '''\
from __future__ import annotations
import hashlib
import json
import sys
from pathlib import Path

repo = Path(sys.argv[1])
spec = json.loads(Path(sys.argv[2]).read_text(encoding="utf-8"))

def digest(path):
    try:
        return hashlib.sha256((repo / path).read_bytes()).hexdigest()
    except OSError:
        return None

work_ok = digest(spec["expected_path"]) == spec["expected_sha256"]
protected_ok = all(digest(path) == value for path, value in spec["protected"].items())
payload = {
    "environment": {"checks": ["workspace", "expected path", "protected paths"], "passed": repo.is_dir()},
    "integrity": {"detail": "protected inputs unchanged" if protected_ok else "protected input drift", "passed": protected_ok},
    "regressions": {},
    "requirements": {"R1": {"detail": "expected bytes present" if work_ok else "expected bytes absent", "passed": work_ok}},
    "resolved": bool(repo.is_dir() and work_ok and protected_ok),
    "schema": "mdseval.coder-beneficial-sensitivity-m2-scout-check-v1",
    "task_id": "synthetic-scout-smoke",
}
print(json.dumps(payload, sort_keys=True, separators=(",", ":")))
'''


class ScoutError(RuntimeError):
    """A fail-closed scout smoke or evidence verification failure."""


def canonical(value: object) -> bytes:
    return (
        json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        )
        + "\n"
    ).encode("utf-8")


def _strict(value: Any, keys: set[str], label: str) -> dict[str, Any]:
    if not isinstance(value, dict) or set(value) != keys:
        raise ScoutError(f"{label} keys mismatch")
    return value


def _safe_relative(value: Any, label: str) -> PurePosixPath:
    if not isinstance(value, str) or not value or "\\" in value:
        raise ScoutError(f"invalid {label}")
    path = PurePosixPath(value)
    if path.is_absolute() or value != path.as_posix() or any(
        part in {"", ".", ".."} for part in value.split("/")
    ):
        raise ScoutError(f"unsafe {label}: {value!r}")
    return path


def _file_hashes(root: Path, paths: list[str]) -> dict[str, str]:
    result: dict[str, str] = {}
    for relative in paths:
        path = root / _safe_relative(relative, "fixture path")
        if path.is_symlink() or not path.is_file():
            raise ScoutError(f"missing or unsafe fixture path: {relative}")
        result[relative] = sha256_file(path)
    return result


def load_config(path: Path | str) -> dict[str, Any]:
    config_path = Path(path)
    if config_path.is_symlink() or not config_path.is_file():
        raise ScoutError("scout config must be a real file")
    try:
        config = json.loads(config_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ScoutError(f"invalid scout config: {exc}") from exc
    _strict(
        config,
        {
            "schema",
            "experiment",
            "phase",
            "live_model_calls",
            "wrapper_sha256",
            "evidence_root",
            "timeouts",
            "fixture",
            "expected",
        },
        "config",
    )
    if (
        config["schema"] != CONFIG_SCHEMA
        or config["experiment"] != "coder-beneficial-sensitivity-m2-scout-v1"
        or config["phase"] != "A"
        or config["live_model_calls"] != 0
        or config["wrapper_sha256"] != sha256_text(WRAPPER_PROMPT)
    ):
        raise ScoutError("scout identity, phase, live-call, or wrapper binding mismatch")
    _safe_relative(config["evidence_root"], "evidence root")
    timeouts = _strict(config["timeouts"], {"subject_seconds", "checker_seconds"}, "timeouts")
    if any(type(value) is not int or not 1 <= value <= 60 for value in timeouts.values()):
        raise ScoutError("timeouts must be integers from 1 through 60")
    fixture = _strict(config["fixture"], {"files", "protected_paths", "relevant_paths"}, "fixture")
    files = fixture["files"]
    if not isinstance(files, dict) or not files or any(
        not isinstance(contents, str) for contents in files.values()
    ):
        raise ScoutError("fixture files must be a nonempty text mapping")
    file_names = {_safe_relative(name, "fixture file").as_posix() for name in files}
    if file_names != set(files) or files.get("CODER.md") != "" or ".issue-contract.md" not in files:
        raise ScoutError("fixture must contain exact safe paths and a zero-byte CODER.md")
    for key in ("protected_paths", "relevant_paths"):
        values = fixture[key]
        if not isinstance(values, list) or not values or len(values) != len(set(values)):
            raise ScoutError(f"{key} must be a unique nonempty list")
        if any(_safe_relative(value, key).as_posix() not in file_names for value in values):
            raise ScoutError(f"{key} references an unknown fixture file")
    expected = _strict(config["expected"], {"path", "sha256"}, "expected")
    if (
        _safe_relative(expected["path"], "expected path").as_posix() not in file_names
        or not isinstance(expected["sha256"], str)
        or len(expected["sha256"]) != 64
    ):
        raise ScoutError("invalid expected output binding")
    return config


def _write_once(path: Path, data: bytes) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.parent.is_symlink() or path.is_symlink():
        raise ScoutError(f"unsafe evidence path: {path}")
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    try:
        descriptor = os.open(path, flags, 0o644)
    except OSError as exc:
        raise ScoutError(f"create-once evidence write failed: {path.name}") from exc
    try:
        with os.fdopen(descriptor, "wb", buffering=0) as stream:
            stream.write(data)
            os.fsync(stream.fileno())
    except BaseException:
        try:
            path.unlink()
        except OSError:
            pass
        raise
    return sha256_bytes(data)


def _write_json_once(path: Path, value: object) -> str:
    return _write_once(path, canonical(value))


def _read_canonical_json(path: Path, label: str) -> dict[str, Any]:
    if path.is_symlink() or not path.is_file():
        raise ScoutError(f"missing or unsafe {label}")
    try:
        raw = path.read_bytes()
        value = json.loads(raw)
    except (OSError, json.JSONDecodeError) as exc:
        raise ScoutError(f"malformed {label}") from exc
    if not isinstance(value, dict) or raw != canonical(value):
        raise ScoutError(f"noncanonical {label}")
    return value


def _materialize_fixture(config: dict[str, Any], root: Path) -> None:
    root.mkdir()
    for relative, contents in config["fixture"]["files"].items():
        path = root / _safe_relative(relative, "fixture file")
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(contents, encoding="utf-8")


def _process_record(
    *,
    outcome: ProcessOutcome,
    command: list[str],
    cwd: Path,
    wrapper_sha256: str | None,
) -> dict[str, Any]:
    return {
        "schema": EXECUTION_SCHEMA,
        "command": command,
        "cwd": str(cwd),
        "returncode": outcome.returncode,
        "timed_out": outcome.timed_out,
        "interrupted": outcome.interrupted,
        "stdout_sha256": sha256_text(outcome.stdout),
        "stderr_sha256": sha256_text(outcome.stderr),
        "wrapper_sha256": wrapper_sha256,
    }


def _capture_execution(
    output: Path,
    label: str,
    outcome: ProcessOutcome,
    command: list[str],
    cwd: Path,
    wrapper_sha256: str | None,
) -> tuple[dict[str, Any], list[dict[str, str]]]:
    redactor = Redactor()
    stdout = redactor.text(outcome.stdout).encode("utf-8")
    stderr = redactor.text(outcome.stderr).encode("utf-8")
    stdout_path = output / f"{label}.stdout.txt"
    stderr_path = output / f"{label}.stderr.txt"
    metadata_path = output / f"{label}.json"
    stdout_sha = _write_once(stdout_path, stdout)
    stderr_sha = _write_once(stderr_path, stderr)
    metadata = _process_record(
        outcome=outcome,
        command=command,
        cwd=cwd,
        wrapper_sha256=wrapper_sha256,
    )
    if metadata["stdout_sha256"] != stdout_sha or metadata["stderr_sha256"] != stderr_sha:
        raise ScoutError("redaction changed synthetic raw evidence")
    metadata_sha = _write_json_once(metadata_path, metadata)
    paths = (
        (stdout_path, stdout_sha),
        (stderr_path, stderr_sha),
        (metadata_path, metadata_sha),
    )
    return metadata, [
        {"path": path.as_posix(), "sha256": digest} for path, digest in paths
    ]


def _checker_payload(stdout: str) -> dict[str, Any]:
    try:
        payload = json.loads(stdout)
    except json.JSONDecodeError as exc:
        raise ScoutError("malformed checker output") from exc
    if not isinstance(payload, dict) or stdout.encode("utf-8") != canonical(payload):
        raise ScoutError("checker output is not canonical JSON")
    _strict(
        payload,
        {"schema", "task_id", "environment", "requirements", "regressions", "integrity", "resolved"},
        "checker payload",
    )
    if (
        payload["schema"] != CHECK_SCHEMA
        or payload["task_id"] != "synthetic-scout-smoke"
        or set(payload.get("requirements", {})) != {"R1"}
        or payload.get("regressions") != {}
        or type(payload.get("resolved")) is not bool
    ):
        raise ScoutError("checker payload contract mismatch")
    return payload


def _run_replay(
    *,
    replay: int,
    fixture: Path,
    tools: Path,
    output_root: Path,
    config: dict[str, Any],
) -> tuple[dict[str, Any], list[dict[str, str]]]:
    workspace = fixture.parent / f"workspace-{replay}"
    shutil.copytree(fixture, workspace)
    replay_output = output_root / f"replay-{replay:02d}"
    replay_output.mkdir()
    protected_paths = config["fixture"]["protected_paths"]
    relevant_paths = config["fixture"]["relevant_paths"]
    protected_before = _file_hashes(workspace, protected_paths)
    relevant_before = _file_hashes(workspace, relevant_paths)
    before_tree = tree_sha256(workspace)
    python = str(Path(sys.executable).resolve())
    subject_command = [
        python,
        "-I",
        str(tools / "fake_subject.py"),
        str(workspace),
        config["wrapper_sha256"],
    ]
    environment = {
        "LANG": "C",
        "LC_ALL": "C",
        "PATH": os.environ.get("PATH", ""),
        "PYTHONHASHSEED": "0",
    }
    subject = run_process_group(
        subject_command,
        cwd=workspace,
        input_text=WRAPPER_PROMPT,
        timeout=config["timeouts"]["subject_seconds"],
        environment=environment,
    )
    subject_meta, evidence = _capture_execution(
        replay_output,
        "subject",
        subject,
        subject_command,
        workspace,
        config["wrapper_sha256"],
    )
    checker_command = [
        python,
        "-I",
        str(tools / "checker.py"),
        str(workspace),
        str(tools / "checker-spec.json"),
    ]
    checker = run_process_group(
        checker_command,
        cwd=workspace,
        input_text=None,
        timeout=config["timeouts"]["checker_seconds"],
        environment=environment,
    )
    checker_meta, checker_evidence = _capture_execution(
        replay_output,
        "checker",
        checker,
        checker_command,
        workspace,
        None,
    )
    evidence.extend(checker_evidence)
    payload = _checker_payload(checker.stdout)
    protected_after = _file_hashes(workspace, protected_paths)
    relevant_after = _file_hashes(workspace, relevant_paths)
    protected_unchanged = protected_before == protected_after
    subject_ok = bool(
        subject.returncode == 0
        and not subject.timed_out
        and not subject.interrupted
        and subject.stderr == ""
        and subject.stdout.startswith("IMPLEMENTED\n")
    )
    checker_ok = bool(
        checker.returncode == 0
        and not checker.timed_out
        and not checker.interrupted
        and checker.stderr == ""
        and payload["resolved"] is True
        and payload["integrity"].get("passed") is True
        and payload["requirements"]["R1"].get("passed") is True
    )
    signature_payload = {
        "before_tree_sha256": before_tree,
        "after_tree_sha256": tree_sha256(workspace),
        "protected_before": protected_before,
        "protected_after": protected_after,
        "relevant_before": relevant_before,
        "relevant_after": relevant_after,
        "subject": {
            key: subject_meta[key]
            for key in ("returncode", "timed_out", "interrupted", "stdout_sha256", "stderr_sha256", "wrapper_sha256")
        },
        "checker": {
            key: checker_meta[key]
            for key in ("returncode", "timed_out", "interrupted", "stdout_sha256", "stderr_sha256")
        },
        "checker_payload": payload,
    }
    passed = bool(subject_ok and checker_ok and protected_unchanged)
    record = {
        "schema": REPLAY_SCHEMA,
        "replay": replay,
        "passed": passed,
        "subject_ok": subject_ok,
        "checker_ok": checker_ok,
        "protected_unchanged": protected_unchanged,
        "signature_sha256": sha256_bytes(canonical(signature_payload)),
        "signature": signature_payload,
    }
    record_path = replay_output / "result.json"
    record_sha = _write_json_once(record_path, record)
    evidence.append({"path": record_path.as_posix(), "sha256": record_sha})
    if not passed:
        if not protected_unchanged:
            raise ScoutError("protected input changed")
        raise ScoutError("synthetic replay did not pass")
    return record, evidence


def _prepare_output(path: Path) -> None:
    for candidate in (path, *path.parents):
        if candidate.exists() and candidate.is_symlink():
            raise ScoutError(f"output path traverses a symlink: {candidate}")
    if path.exists() or path.is_symlink():
        raise ScoutError("smoke output is create-once and already exists")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.mkdir()


def run_smoke(
    config_path: Path | str,
    output: Path | str,
    *,
    fake_subject_source: str = FAKE_SUBJECT_SOURCE,
    checker_source: str = CHECKER_SOURCE,
) -> dict[str, Any]:
    """Run two deterministic, offline fresh-copy replays and preserve evidence."""
    config_path = Path(config_path).resolve()
    requested_output = Path(output)
    if requested_output.is_symlink():
        raise ScoutError("smoke output must not be a symlink")
    output_path = requested_output.resolve(strict=False)
    config = load_config(config_path)
    if config["live_model_calls"] != 0:
        raise ScoutError("live calls are forbidden in Phase A")
    python = Path(sys.executable).resolve()
    if not python.is_file() or os.name != "posix" or not all(
        hasattr(os, name) for name in ("killpg", "getpgid")
    ):
        raise ScoutError("command/tool preflight failed")
    try:
        compile(fake_subject_source, "fake_subject.py", "exec")
        compile(checker_source, "checker.py", "exec")
    except SyntaxError as exc:
        raise ScoutError("synthetic tool compile preflight failed") from exc
    _prepare_output(output_path)
    with tempfile.TemporaryDirectory(prefix="mdseval-scout-phase-a-") as temporary:
        temp = Path(temporary)
        fixture = temp / "fixture"
        tools = temp / "tools"
        tools.mkdir()
        _materialize_fixture(config, fixture)
        (tools / "fake_subject.py").write_text(fake_subject_source, encoding="utf-8")
        (tools / "checker.py").write_text(checker_source, encoding="utf-8")
        protected = _file_hashes(fixture, config["fixture"]["protected_paths"])
        spec = {
            "expected_path": config["expected"]["path"],
            "expected_sha256": config["expected"]["sha256"],
            "protected": protected,
        }
        (tools / "checker-spec.json").write_bytes(canonical(spec))
        manifest = {
            "schema": MANIFEST_SCHEMA,
            "experiment": config["experiment"],
            "phase": "A",
            "live_model_calls": 0,
            "config_path": str(config_path),
            "config_sha256": sha256_file(config_path),
            "wrapper_sha256": config["wrapper_sha256"],
            "fixture_tree_sha256": tree_sha256(fixture),
            "protected_inputs": protected,
            "relevant_inputs": _file_hashes(fixture, config["fixture"]["relevant_paths"]),
            "python": {"executable": str(python), "version": sys.version},
            "preflight": {
                "isolated_fixture": True,
                "paths_safe": True,
                "process_groups": True,
                "subject_compiles": True,
                "checker_compiles": True,
            },
            "tools": {
                "fake_subject.py": sha256_file(tools / "fake_subject.py"),
                "checker.py": sha256_file(tools / "checker.py"),
                "checker-spec.json": sha256_file(tools / "checker-spec.json"),
            },
        }
        evidence: list[dict[str, str]] = []
        manifest_path = output_path / "manifest.json"
        evidence.append(
            {"path": manifest_path.as_posix(), "sha256": _write_json_once(manifest_path, manifest)}
        )
        records = []
        for replay in (1, 2):
            record, replay_evidence = _run_replay(
                replay=replay,
                fixture=fixture,
                tools=tools,
                output_root=output_path,
                config=config,
            )
            records.append(record)
            evidence.extend(replay_evidence)
        deterministic = records[0]["signature_sha256"] == records[1]["signature_sha256"]
        comparison = {
            "schema": COMPARISON_SCHEMA,
            "deterministic": deterministic,
            "replay_signature_sha256": [record["signature_sha256"] for record in records],
            "protected_inputs_unchanged": all(record["protected_unchanged"] for record in records),
            "passed": bool(deterministic and all(record["passed"] for record in records)),
        }
        comparison_path = output_path / "comparison.json"
        evidence.append(
            {"path": comparison_path.as_posix(), "sha256": _write_json_once(comparison_path, comparison)}
        )
        if not comparison["passed"]:
            raise ScoutError("fresh-copy replay comparison failed")
        relative_evidence = [
            {
                "path": Path(item["path"]).relative_to(output_path).as_posix(),
                "sha256": item["sha256"],
            }
            for item in evidence
        ]
        receipt = {
            "schema": RECEIPT_SCHEMA,
            "status": "PASS",
            "experiment": config["experiment"],
            "phase": "A",
            "live_model_calls": 0,
            "manifest_sha256": sha256_file(manifest_path),
            "comparison_sha256": sha256_file(comparison_path),
            "evidence": sorted(relative_evidence, key=lambda item: item["path"]),
        }
        _write_json_once(output_path / "receipt.json", receipt)
    verified = verify_smoke(output_path)
    return {
        "status": verified["status"],
        "output": str(output_path),
        "evidence_file_count": len(verified["evidence"]) + 1,
        "live_model_calls": verified["live_model_calls"],
    }


def verify_smoke(output: Path | str) -> dict[str, Any]:
    """Fail closed unless the create-once smoke evidence is complete and bound."""
    root = Path(output)
    if root.is_symlink() or not root.is_dir():
        raise ScoutError("missing or unsafe smoke output")
    receipt = _read_canonical_json(root / "receipt.json", "receipt")
    _strict(
        receipt,
        {"schema", "status", "experiment", "phase", "live_model_calls", "manifest_sha256", "comparison_sha256", "evidence"},
        "receipt",
    )
    if (
        receipt["schema"] != RECEIPT_SCHEMA
        or receipt["status"] != "PASS"
        or receipt["phase"] != "A"
        or receipt["live_model_calls"] != 0
        or not isinstance(receipt["evidence"], list)
    ):
        raise ScoutError("receipt identity or status mismatch")
    listed: dict[str, str] = {}
    for item in receipt["evidence"]:
        _strict(item, {"path", "sha256"}, "evidence binding")
        relative = _safe_relative(item["path"], "evidence path").as_posix()
        if relative in listed or not isinstance(item["sha256"], str):
            raise ScoutError("duplicate or invalid evidence binding")
        listed[relative] = item["sha256"]
    actual = {
        path.relative_to(root).as_posix()
        for path in root.rglob("*")
        if path.is_file() and not path.is_symlink()
    }
    if any(path.is_symlink() for path in root.rglob("*")):
        raise ScoutError("symlink in smoke evidence")
    if actual != set(listed) | {"receipt.json"}:
        raise ScoutError("missing or unexpected smoke evidence")
    for relative, expected in listed.items():
        if sha256_file(root / relative) != expected:
            raise ScoutError(f"evidence hash drift: {relative}")
    manifest = _read_canonical_json(root / "manifest.json", "manifest")
    comparison = _read_canonical_json(root / "comparison.json", "comparison")
    if (
        manifest.get("schema") != MANIFEST_SCHEMA
        or manifest.get("live_model_calls") != 0
        or sha256_file(root / "manifest.json") != receipt["manifest_sha256"]
        or comparison.get("schema") != COMPARISON_SCHEMA
        or comparison.get("passed") is not True
        or comparison.get("deterministic") is not True
        or comparison.get("protected_inputs_unchanged") is not True
        or len(set(comparison.get("replay_signature_sha256", []))) != 1
        or sha256_file(root / "comparison.json") != receipt["comparison_sha256"]
    ):
        raise ScoutError("manifest or deterministic comparison verification failed")
    for replay in (1, 2):
        record = _read_canonical_json(root / f"replay-{replay:02d}/result.json", "replay result")
        if (
            record.get("schema") != REPLAY_SCHEMA
            or record.get("replay") != replay
            or record.get("passed") is not True
            or record.get("protected_unchanged") is not True
            or record.get("signature_sha256") != comparison["replay_signature_sha256"][replay - 1]
        ):
            raise ScoutError("replay verification failed")
        for label in ("subject", "checker"):
            metadata = _read_canonical_json(
                root / f"replay-{replay:02d}/{label}.json", f"{label} metadata"
            )
            if (
                metadata.get("schema") != EXECUTION_SCHEMA
                or metadata.get("stdout_sha256")
                != sha256_file(root / f"replay-{replay:02d}/{label}.stdout.txt")
                or metadata.get("stderr_sha256")
                != sha256_file(root / f"replay-{replay:02d}/{label}.stderr.txt")
            ):
                raise ScoutError("raw execution evidence verification failed")
    return receipt


# Phase B: frozen-cohort qualification, exact scout scheduling, and live capture.


def _repository_root(path: Path) -> Path:
    for candidate in (path.resolve(), *path.resolve().parents):
        if (candidate / ".git").exists():
            return candidate
    raise ScoutError("cohort is not inside a Git repository")


def _canonical_json_file(path: Path, label: str) -> dict[str, Any]:
    if path.is_symlink() or not path.is_file():
        raise ScoutError(f"missing or unsafe {label}: {path}")
    raw = path.read_bytes()
    try:
        value = json.loads(raw)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ScoutError(f"invalid {label}: {exc}") from exc
    if not isinstance(value, dict) or raw != canonical(value):
        raise ScoutError(f"{label} is not a canonical JSON object")
    return value


def _bound_file(root: Path, relative: str, expected: str, label: str) -> Path:
    path = root / _safe_relative(relative, label)
    if path.is_symlink() or not path.is_file() or sha256_file(path) != expected:
        raise ScoutError(f"{label} hash or path mismatch: {relative}")
    return path


def _require_sha(value: Any, label: str) -> str:
    if not isinstance(value, str) or len(value) != 64 or any(
        character not in "0123456789abcdef" for character in value
    ):
        raise ScoutError(f"invalid SHA-256 for {label}")
    return value


def _checker_sections(result: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    requirements = result.get("requirements")
    regressions = result.get("regressions")
    if not isinstance(requirements, dict) or not isinstance(regressions, dict):
        raise ScoutError("checker result lacks scoreable requirement or regression sections")
    if any(
        not isinstance(item, dict) or type(item.get("passed")) is not bool
        for item in (*requirements.values(), *regressions.values())
    ):
        raise ScoutError("checker result has unscoreable observations")
    integrity = result.get("integrity")
    environment = result.get("environment")
    if any(
        not isinstance(item, dict) or type(item.get("passed")) is not bool
        for item in (integrity, environment)
    ) or type(result.get("resolved")) is not bool:
        raise ScoutError("checker result lacks scoreable integrity/environment/resolution")
    return requirements, regressions


def load_cohort(path: Path | str) -> dict[str, Any]:
    """Load and exhaustively bind the one frozen six-task Phase-B cohort."""
    cohort_path = Path(path).resolve()
    cohort = _canonical_json_file(cohort_path, "cohort")
    _strict(
        cohort,
        {
            "schema", "cohort_id", "start_commit", "task_root", "recipe",
            "wrapper", "admission_evidence", "runtime", "sandbox", "schedule",
            "replacements", "classification", "tasks",
        },
        "cohort",
    )
    if cohort["schema"] != COHORT_SCHEMA or cohort["cohort_id"] != "scout-v1":
        raise ScoutError("wrong Phase-B cohort identity")
    root = _repository_root(cohort_path)
    start = cohort["start_commit"]
    if not isinstance(start, str) or len(start) != 40 or any(
        character not in "0123456789abcdef" for character in start
    ):
        raise ScoutError("invalid start commit")
    try:
        run_git(root, "cat-file", "-e", f"{start}^{{commit}}")
        run_git(root, "merge-base", "--is-ancestor", start, "HEAD")
    except RuntimeError as exc:
        raise ScoutError("start commit is absent or newer than HEAD") from exc
    task_root_relative = _safe_relative(cohort["task_root"], "task root").as_posix()
    task_root = root / task_root_relative
    if task_root.is_symlink() or not task_root.is_dir():
        raise ScoutError("frozen task root is missing or unsafe")
    recipe = _strict(cohort["recipe"], {"path", "sha256"}, "recipe binding")
    recipe_path = _bound_file(root, recipe["path"], _require_sha(recipe["sha256"], "recipe"), "recipe")
    recipe_object = _canonical_json_file(recipe_path, "recipe")
    if recipe_object.get("schema") != "mdseval.coder-beneficial-sensitivity-m2-generation-recipe-v1":
        raise ScoutError("wrong frozen recipe schema")
    wrapper = _strict(cohort["wrapper"], {"prompt_sha256", "source_path", "source_sha256"}, "wrapper")
    if wrapper["prompt_sha256"] != sha256_text(WRAPPER_PROMPT):
        raise ScoutError("wrapper prompt bytes drifted")
    _bound_file(root, wrapper["source_path"], _require_sha(wrapper["source_sha256"], "wrapper source"), "wrapper source")
    runtime = _strict(cohort["runtime"], {"type", "model", "reasoning_effort", "timeout_seconds", "approval_policy", "ephemeral", "max_parallel_runs", "variant"}, "runtime")
    if runtime != {"type": "codex-cli", "model": "gpt-5.6-sol", "reasoning_effort": "high", "timeout_seconds": 300, "approval_policy": "never", "ephemeral": True, "max_parallel_runs": 1, "variant": "null-only"}:
        raise ScoutError("runtime is not the exact frozen null-only runtime")
    sandbox = _strict(cohort["sandbox"], {"mode", "network_access", "subagents_enabled", "ignore_user_config", "ignore_rules"}, "sandbox")
    if sandbox != {"mode": "workspace-write", "network_access": False, "subagents_enabled": False, "ignore_user_config": True, "ignore_rules": True}:
        raise ScoutError("sandbox is not the exact frozen isolation policy")
    replacements = _strict(cohort["replacements"], {"author_pair_max", "cohort_max", "absolute_launch_max", "predicate"}, "replacement rules")
    if replacements != {"author_pair_max": 2, "cohort_max": 6, "absolute_launch_max": 24, "predicate": "frozen-infrastructure-failure-before-usable-output-v1"}:
        raise ScoutError("replacement rules drifted")
    classification = _strict(cohort["classification"], {"promising_q_min", "promising_q_max", "resolved_counts", "wrong_failure_requires_omission_only", "decision"}, "classification")
    if classification != {"promising_q_min": 0.55, "promising_q_max": 0.90, "resolved_counts": [1, 2], "wrong_failure_requires_omission_only": True, "decision": "section-13-r2-scout-pass-v1"}:
        raise ScoutError("classification rules drifted")

    bindings = cohort["tasks"]
    if not isinstance(bindings, list) or len(bindings) != 6:
        raise ScoutError("cohort must bind exactly six tasks")
    authors: dict[str, list[dict[str, Any]]] = {}
    templates: set[str] = set()
    task_ids: list[str] = []
    for binding_value in bindings:
        binding = _strict(binding_value, {"id", "author_id", "author_role", "family_id", "problem_template_id", "requirements", "task_sha256", "public_tree_sha256", "checker_sha256", "admission_sha256", "reference_sha256"}, "task binding")
        task_id = binding["id"]
        if not isinstance(task_id, str) or task_id in task_ids:
            raise ScoutError("duplicate or invalid task id")
        task_ids.append(task_id)
        task_dir = task_root / _safe_relative(task_id, "task id")
        task_path = _bound_file(task_dir, "task.json", _require_sha(binding["task_sha256"], "task"), "task")
        task = _canonical_json_file(task_path, "task")
        required_task_values = {"schema": "mdseval.scout-task-v1", "id": task_id, "author_id": binding["author_id"], "family_id": binding["family_id"], "problem_template_id": binding["problem_template_id"], "network_allowed": False, "standard_library_only": True, "dependencies": [], "timeout_seconds": 300}
        if any(task.get(key) != value for key, value in required_task_values.items()):
            raise ScoutError(f"task metadata drift: {task_id}")
        requirements = task.get("requirements")
        requirement_ids = [item.get("id") for item in requirements] if isinstance(requirements, list) else []
        if requirement_ids != binding["requirements"] or len(requirement_ids) != 8 or len(set(requirement_ids)) != 8:
            raise ScoutError(f"requirement binding drift: {task_id}")
        if task.get("recipe") != {"path": "../recipe-v1.json", "sha256": recipe["sha256"]}:
            raise ScoutError(f"recipe binding drift: {task_id}")
        public = task_dir / "public"
        if public.is_symlink() or tree_sha256(public) != binding["public_tree_sha256"] or tree_sha256(public) != task.get("subject_packet", {}).get("tree_sha256"):
            raise ScoutError(f"public packet hash drift: {task_id}")
        forbidden = {"task.json", "admission.json", "reference.json", "check.py", ".git", ".codex", ".agents", "AGENTS.md", "AGENTS.override.md"}
        for entry in public.rglob("*"):
            if entry.is_symlink() or entry.name in forbidden:
                raise ScoutError(f"private or unsafe material in public packet: {task_id}")
        subject = task.get("subject_packet", {})
        if (public / "CODER.md").read_bytes() != b"" or subject.get("coder_md_bytes") != 0 or subject.get("excludes_private_material") is not True or subject.get("wrapper_prompt_sha256") != wrapper["prompt_sha256"]:
            raise ScoutError(f"subject packet isolation drift: {task_id}")
        _bound_file(task_dir, task["checker_path"], _require_sha(binding["checker_sha256"], "checker"), "checker")
        admission_path = _bound_file(task_dir, task["admission_path"], _require_sha(binding["admission_sha256"], "admission"), "admission")
        reference_path = _bound_file(task_dir, task["reference_path"], _require_sha(binding["reference_sha256"], "reference"), "reference")
        admission = _canonical_json_file(admission_path, "admission")
        reference = _canonical_json_file(reference_path, "reference")
        trace = admission.get("trace")
        if admission.get("schema") != "mdseval.scout-admission-contract-v1" or admission.get("task_id") != task_id or admission.get("recipe_sha256") != recipe["sha256"] or not isinstance(trace, list) or [item.get("requirement_id") for item in trace] != requirement_ids:
            raise ScoutError(f"admission trace drift: {task_id}")
        for item in trace:
            required_trace = {"requirement_id", "public_path", "public_locator", "public_text_sha256", "assertion_ids", "pass_predicate", "omission_predicate"}
            if not isinstance(item, dict) or not required_trace.issubset(item) or set(item) - required_trace not in (set(), {"requirement_text", "requirement_text_sha256"}):
                raise ScoutError("trace item keys mismatch")
            if "requirement_text" in item and sha256_text(item["requirement_text"]) != item["requirement_text_sha256"]:
                raise ScoutError("trace requirement text hash drift")
            public_trace = _bound_file(public, item["public_path"], _require_sha(item["public_text_sha256"], "trace text"), "trace public text")
            requirement_id = item["requirement_id"]
            if item["public_locator"] not in public_trace.read_text(encoding="utf-8") or item["pass_predicate"] != f"$.requirements.{requirement_id}.passed == true" or item["omission_predicate"] != f"$.requirements.{requirement_id}.passed == false":
                raise ScoutError(f"invalid trace predicate or locator: {task_id}")
        if admission.get("protected_inputs") != [{"path": path, "sha256": sha256_file(public / path)} for path in task["protected_paths"]]:
            raise ScoutError(f"protected input binding drift: {task_id}")
        mutants = admission.get("mutants")
        if not isinstance(mutants, list) or [item.get("requirement_id") for item in mutants] != requirement_ids:
            raise ScoutError(f"mutant binding drift: {task_id}")
        if reference.get("schema") != "mdseval.scout-reference-v1" or reference.get("task_id") != task_id or reference.get("application") != "replace files relative to public workspace":
            raise ScoutError(f"reference binding drift: {task_id}")
        for mapping in [reference.get("files"), *(item.get("files") for item in mutants)]:
            if not isinstance(mapping, dict) or not mapping or any(not isinstance(value, str) for value in mapping.values()):
                raise ScoutError(f"invalid replacement mapping: {task_id}")
            for relative in mapping:
                safe = _safe_relative(relative, "replacement path")
                if safe.as_posix() in task["protected_paths"]:
                    raise ScoutError(f"replacement targets protected input: {task_id}")
        authors.setdefault(binding["author_id"], []).append(binding)
        if not isinstance(binding["author_role"], str) or binding["problem_template_id"] in templates:
            raise ScoutError("author role or template isolation drift")
        templates.add(binding["problem_template_id"])
    if len(authors) != 3 or any(len(items) != 2 or len({item["family_id"] for item in items}) != 2 or len({item["author_role"] for item in items}) != 1 for items in authors.values()):
        raise ScoutError("cohort author-pair or family design drift")
    schedule = cohort["schedule"]
    if not isinstance(schedule, list) or len(schedule) != 18 or any(not isinstance(item, str) for item in schedule):
        raise ScoutError("schedule must contain exactly 18 serial usable slots")
    if any(schedule.count(task_id) != 3 for task_id in task_ids) or set(schedule) != set(task_ids):
        raise ScoutError("schedule must bind exactly three usable attempts per task")
    _verify_admission_evidence(root, cohort, task_ids)
    return cohort


def _verify_admission_evidence(root: Path, cohort: dict[str, Any], task_ids: list[str]) -> None:
    evidence = _strict(cohort["admission_evidence"], {"root", "status", "files"}, "admission evidence")
    if evidence["status"] != "PASS" or not isinstance(evidence["files"], dict) or len(evidence["files"]) != 20:
        raise ScoutError("admission evidence binding is incomplete")
    evidence_root = root / _safe_relative(evidence["root"], "admission evidence root")
    expected_paths = {"manifest.json", "summary.json"}
    expected_paths.update(f"submissions/{task_id}.json" for task_id in task_ids)
    expected_paths.update(f"replays/{task_id}/{replay}.json" for task_id in task_ids for replay in (1, 2))
    if set(evidence["files"]) != expected_paths:
        raise ScoutError("admission evidence path set drift")
    records = {relative: _canonical_json_file(_bound_file(evidence_root, relative, _require_sha(digest, "admission evidence"), "admission evidence"), "admission evidence") for relative, digest in evidence["files"].items()}
    manifest, summary = records["manifest.json"], records["summary.json"]
    if manifest.get("status") != "PASS" or summary.get("status") != "PASS" or summary.get("task_count") != 6 or summary.get("replay_count") != 12 or any(summary.get(key) is not True for key in ("all_checker_workspaces_unchanged", "all_protected_inputs_unchanged", "all_replays_identical", "all_resolved", "all_unsubmitted_change_sets_empty")):
        raise ScoutError("admission PASS assertions drifted")
    bindings = {item["id"]: item for item in cohort["tasks"]}
    for task_id in task_ids:
        entry = manifest.get("tasks", {}).get(task_id, {})
        binding = bindings[task_id]
        submission_path = f"submissions/{task_id}.json"
        submission = records[submission_path]
        if entry.get("task_json_sha256") != binding["task_sha256"] or entry.get("public_tree_sha256") != binding["public_tree_sha256"] or entry.get("checker_sha256") != binding["checker_sha256"] or entry.get("submission_path") != submission_path or entry.get("submission_sha256") != evidence["files"][submission_path] or sorted(entry.get("submitted_paths", [])) != sorted(submission):
            raise ScoutError(f"admission manifest drift: {task_id}")
        replay_outputs: list[str] = []
        for replay in (1, 2):
            record = records[f"replays/{task_id}/{replay}.json"]
            if record.get("task_id") != task_id or record.get("replay") != replay or record.get("resolved") is not True or record.get("canonical_stdout") is not True or record.get("checker_workspace_unchanged") is not True or record.get("protected_unchanged") is not True or record.get("unsubmitted_changes") != [] or record.get("changed_paths") != sorted(submission) or record.get("returncode") != 0:
                raise ScoutError(f"admission replay drift: {task_id}/{replay}")
            stdout = record.get("stdout")
            try:
                result = json.loads(stdout)
            except (TypeError, json.JSONDecodeError) as exc:
                raise ScoutError(f"malformed admission replay: {task_id}/{replay}") from exc
            requirements, regressions = _checker_sections(result)
            if canonical(result).decode() != stdout or result.get("task_id") != task_id or not result["resolved"] or not all(item["passed"] for item in (*requirements.values(), *regressions.values())) or not result["integrity"]["passed"]:
                raise ScoutError(f"unresolved admission replay: {task_id}/{replay}")
            replay_outputs.append(stdout)
        if len(set(replay_outputs)) != 1:
            raise ScoutError(f"nondeterministic admission replay: {task_id}")


def _copy_public(source: Path, destination: Path) -> None:
    if destination.exists():
        raise ScoutError("fresh workspace already exists")
    for entry in source.rglob("*"):
        if entry.is_symlink():
            raise ScoutError("public packet contains a symlink")
    shutil.copytree(source, destination)


def _replace_text_files(workspace: Path, files: dict[str, str]) -> None:
    for relative, contents in files.items():
        path = workspace / _safe_relative(relative, "replacement path")
        if path.is_symlink():
            raise ScoutError("replacement target is a symlink")
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(contents, encoding="utf-8")


def _run_objective_checker(
    checker: Path,
    workspace: Path,
    *,
    timeout: int = 60,
    process_runner: Any = run_process_group,
) -> dict[str, Any]:
    before = tree_sha256(workspace)
    checker_before = sha256_file(checker)
    environment = safe_process_environment()
    environment["PYTHONDONTWRITEBYTECODE"] = "1"
    outcome = process_runner(
        [sys.executable, str(checker), str(workspace)], cwd=checker.parent,
        input_text=None, timeout=timeout, environment=environment,
    )
    after = tree_sha256(workspace)
    if outcome.timed_out or outcome.interrupted or outcome.returncode != 0:
        raise ScoutError("objective checker execution failed")
    try:
        result = json.loads(outcome.stdout)
    except json.JSONDecodeError as exc:
        raise ScoutError("objective checker output is malformed") from exc
    if not isinstance(result, dict) or outcome.stdout != canonical(result).decode("utf-8"):
        raise ScoutError("objective checker output is not canonical")
    _checker_sections(result)
    if before != after or checker_before != sha256_file(checker):
        raise ScoutError("objective checker mutated its workspace or bytes")
    return {"result": result, "stdout_sha256": sha256_text(outcome.stdout), "workspace_sha256": before}


def _protected_hashes(workspace: Path, paths: list[str]) -> dict[str, str]:
    return {path: sha256_file(workspace / _safe_relative(path, "protected path")) for path in paths}


def _qualify_task(root: Path, cohort: dict[str, Any], binding: dict[str, Any]) -> dict[str, Any]:
    task_dir = root / cohort["task_root"] / binding["id"]
    task = _canonical_json_file(task_dir / "task.json", "task")
    admission = _canonical_json_file(task_dir / "admission.json", "admission")
    reference = _canonical_json_file(task_dir / "reference.json", "reference")
    checker = task_dir / "check.py"
    public = task_dir / "public"
    protected_expected = _protected_hashes(public, task["protected_paths"])
    with tempfile.TemporaryDirectory(prefix=f"mdseval-qualify-{binding['id']}-") as temporary:
        temporary_root = Path(temporary)

        def execute(label: str, files: dict[str, str] | None = None) -> dict[str, Any]:
            workspace = temporary_root / label
            _copy_public(public, workspace)
            if files:
                _replace_text_files(workspace, files)
            protected_before = _protected_hashes(workspace, task["protected_paths"])
            checked = _run_objective_checker(checker, workspace)
            protected_after = _protected_hashes(workspace, task["protected_paths"])
            if protected_before != protected_expected or protected_after != protected_expected:
                raise ScoutError(f"protected input drift during qualification: {binding['id']}")
            return checked

        pristine = execute("pristine")
        if pristine["result"]["resolved"]:
            raise ScoutError(f"pristine task unexpectedly resolves: {binding['id']}")
        references = [execute(f"reference-{replay}", reference["files"]) for replay in (1, 2)]
        if any(not replay["result"]["resolved"] for replay in references) or references[0]["stdout_sha256"] != references[1]["stdout_sha256"]:
            raise ScoutError(f"reference is unresolved or nondeterministic: {binding['id']}")
        mutant_records: list[dict[str, Any]] = []
        for mutant in admission["mutants"]:
            files = dict(reference["files"])
            files.update(mutant["files"])
            checked = execute(mutant["id"], files)
            result = checked["result"]
            requirements, regressions = _checker_sections(result)
            mapped = mutant["requirement_id"]
            failed = [name for name, value in requirements.items() if not value["passed"]]
            if result["resolved"] or failed != [mapped] or not all(value["passed"] for value in regressions.values()) or not result["integrity"]["passed"] or not result["environment"]["passed"]:
                raise ScoutError(f"mutant does not isolate its omission: {binding['id']}/{mapped}")
            mutant_records.append({"id": mutant["id"], "requirement_id": mapped, **checked})
    return {
        "schema": QUALIFICATION_TASK_SCHEMA, "task_id": binding["id"],
        "task_sha256": binding["task_sha256"], "public_tree_sha256": binding["public_tree_sha256"],
        "checker_sha256": binding["checker_sha256"], "admission_sha256": binding["admission_sha256"],
        "reference_sha256": binding["reference_sha256"], "protected_sha256": protected_expected,
        "pristine": pristine, "reference_replays": references, "mutants": mutant_records,
        "status": "PASS",
    }


def qualify_cohort(cohort_path: Path | str, output: Path | str) -> dict[str, Any]:
    """Create once the compact, offline six-task qualification evidence."""
    cohort_path = Path(cohort_path).resolve()
    cohort = load_cohort(cohort_path)
    root = _repository_root(cohort_path)
    output_path = Path(output).resolve()
    if output_path.exists():
        raise ScoutError("qualification evidence is create-once")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    temporary = Path(tempfile.mkdtemp(prefix=".qualification-", dir=output_path.parent))
    try:
        task_hashes: dict[str, str] = {}
        for binding in cohort["tasks"]:
            relative = f"tasks/{binding['id']}.json"
            task_hashes[relative] = _write_json_once(temporary / relative, _qualify_task(root, cohort, binding))
        manifest = {
            "schema": QUALIFICATION_MANIFEST_SCHEMA, "cohort_id": cohort["cohort_id"],
            "cohort_sha256": sha256_file(cohort_path), "start_commit": cohort["start_commit"],
            "live_model_calls": 0, "task_records": task_hashes,
            "admission_evidence": cohort["admission_evidence"]["files"],
        }
        manifest_sha = _write_json_once(temporary / "manifest.json", manifest)
        summary = {
            "schema": QUALIFICATION_SUMMARY_SCHEMA, "status": "PASS", "task_count": 6,
            "reference_replay_count": 12, "mutant_count": 48, "pristine_unresolved_count": 6,
            "all_reference_replays_identical": True, "all_mutants_isolated": True,
            "all_protected_and_checker_workspaces_unchanged": True,
            "manifest_sha256": manifest_sha, "task_records": task_hashes,
        }
        _write_json_once(temporary / "summary.json", summary)
        temporary.replace(output_path)
    except Exception:
        shutil.rmtree(temporary, ignore_errors=True)
        raise
    return verify_qualification(cohort_path, output_path)


def verify_qualification(cohort_path: Path | str, output: Path | str) -> dict[str, Any]:
    cohort_path = Path(cohort_path).resolve()
    cohort = load_cohort(cohort_path)
    evidence = Path(output).resolve()
    expected = {"manifest.json", "summary.json"} | {f"tasks/{item['id']}.json" for item in cohort["tasks"]}
    actual = {path.relative_to(evidence).as_posix() for path in evidence.rglob("*") if path.is_file()}
    if actual != expected or any(path.is_symlink() for path in evidence.rglob("*")):
        raise ScoutError("qualification evidence has missing, unexpected, or unsafe paths")
    manifest = _canonical_json_file(evidence / "manifest.json", "qualification manifest")
    summary = _canonical_json_file(evidence / "summary.json", "qualification summary")
    if manifest.get("schema") != QUALIFICATION_MANIFEST_SCHEMA or manifest.get("cohort_sha256") != sha256_file(cohort_path) or manifest.get("live_model_calls") != 0 or summary.get("schema") != QUALIFICATION_SUMMARY_SCHEMA or summary.get("status") != "PASS" or summary.get("manifest_sha256") != sha256_file(evidence / "manifest.json") or summary.get("task_records") != manifest.get("task_records"):
        raise ScoutError("qualification manifest or summary binding failed")
    for binding in cohort["tasks"]:
        relative = f"tasks/{binding['id']}.json"
        if manifest["task_records"].get(relative) != sha256_file(evidence / relative):
            raise ScoutError(f"qualification task hash drift: {binding['id']}")
        record = _canonical_json_file(evidence / relative, "qualification task record")
        if record.get("schema") != QUALIFICATION_TASK_SCHEMA or record.get("status") != "PASS" or record.get("task_id") != binding["id"] or record.get("task_sha256") != binding["task_sha256"] or record.get("pristine", {}).get("result", {}).get("resolved") is not False or len(record.get("reference_replays", [])) != 2 or len(record.get("mutants", [])) != 8:
            raise ScoutError(f"qualification task record invalid: {binding['id']}")
        references = record["reference_replays"]
        if any(item["result"]["resolved"] is not True for item in references) or len({item["stdout_sha256"] for item in references}) != 1:
            raise ScoutError(f"qualification reference replay invalid: {binding['id']}")
        for mutant in record["mutants"]:
            requirements, regressions = _checker_sections(mutant["result"])
            failed = [name for name, value in requirements.items() if not value["passed"]]
            if failed != [mutant["requirement_id"]] or mutant["result"]["resolved"] or not all(item["passed"] for item in regressions.values()) or not mutant["result"]["integrity"]["passed"]:
                raise ScoutError(f"qualification mutant record invalid: {binding['id']}")
    return summary


def record_launch(
    cohort: dict[str, Any], state: dict[str, Any], task_id: str, *, usable: bool,
    infrastructure_failure: bool,
) -> dict[str, Any]:
    """Advance one frozen serial slot, or account for one permitted replacement."""
    bindings = {item["id"]: item for item in cohort["tasks"]}
    if task_id not in bindings or usable == infrastructure_failure:
        raise ScoutError("launch must be exactly usable or a frozen infrastructure failure")
    launches = int(state.get("launches", 0)) + 1
    usable_count = int(state.get("usable", 0))
    replacements = int(state.get("replacements", 0))
    by_author = dict(state.get("replacements_by_author", {}))
    if launches > cohort["replacements"]["absolute_launch_max"]:
        raise ScoutError("absolute launch cap exceeded")
    expected = cohort["schedule"][usable_count] if usable_count < 18 else None
    if task_id != expected:
        raise ScoutError("launch does not match the next frozen serial slot")
    if usable:
        usable_count += 1
    else:
        author = bindings[task_id]["author_id"]
        replacements += 1
        by_author[author] = int(by_author.get(author, 0)) + 1
        if replacements > cohort["replacements"]["cohort_max"] or by_author[author] > cohort["replacements"]["author_pair_max"]:
            raise ScoutError("replacement cap exceeded")
    return {"launches": launches, "usable": usable_count, "replacements": replacements, "replacements_by_author": by_author}


def _omission_only(result: dict[str, Any]) -> bool:
    requirements, regressions = _checker_sections(result)
    return (
        not result["resolved"]
        and any(not item["passed"] for item in requirements.values())
        and all(item["passed"] for item in regressions.values())
        and result["integrity"]["passed"]
        and result["environment"]["passed"]
    )


def classify_scout(
    cohort: dict[str, Any], attempts: list[dict[str, Any]],
    static_fidelity: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Apply Section 13 R2 only after the exact 18 usable observations exist."""
    if len(attempts) != 18 or [item.get("task_id") for item in attempts] != cohort["schedule"] or any(item.get("usable") is not True for item in attempts):
        raise ScoutError("classification requires the exact frozen 18-usable schedule")
    static_keys = {
        "schema", "status", "qualification", "admission",
        "shared_recipe_or_admission_defect", "clearance_sha256",
    }
    if not isinstance(static_fidelity, dict) or set(static_fidelity) != static_keys:
        raise ScoutError("missing or malformed static fidelity clearance")
    static_base = {
        key: value for key, value in static_fidelity.items()
        if key != "clearance_sha256"
    }
    qualification_binding = static_fidelity.get("qualification")
    admission_binding = static_fidelity.get("admission")
    expected_task_records = {
        f"tasks/{task['id']}.json" for task in cohort["tasks"]
    }
    if (
        static_fidelity["schema"] != FIDELITY_CLEARANCE_SCHEMA
        or static_fidelity["status"] != "PASS"
        or static_fidelity["clearance_sha256"] != sha256_bytes(canonical(static_base))
        or not isinstance(qualification_binding, dict)
        or set(qualification_binding) != {"manifest_sha256", "summary_sha256", "task_records"}
        or set(qualification_binding["task_records"]) != expected_task_records
        or any(len(value) != 64 for value in (
            qualification_binding["manifest_sha256"],
            qualification_binding["summary_sha256"],
            *qualification_binding["task_records"].values(),
        ))
        or admission_binding != {
            "status": cohort["admission_evidence"]["status"],
            "files": cohort["admission_evidence"]["files"],
        }
        or type(static_fidelity["shared_recipe_or_admission_defect"]) is not bool
    ):
        raise ScoutError("invalid or drifted static fidelity clearance")
    clearances: list[dict[str, Any]] = []
    clearance_keys = {
        "schema", "static_clearance_sha256", "static_status", "task_id",
        "checker_binding_passed", "checker_workspace_unchanged",
        "protected_workspace_passed", "task_fidelity_passed", "root_cause",
        "shared_recipe_or_admission_defect",
    }
    for attempt in attempts:
        clearance = attempt.get("fidelity_clearance")
        if not isinstance(clearance, dict) or set(clearance) != clearance_keys:
            raise ScoutError("missing or malformed launch fidelity clearance")
        digest = clearance.get("static_clearance_sha256")
        if (
            clearance["schema"] != LAUNCH_FIDELITY_SCHEMA
            or clearance["static_status"] != "PASS"
            or clearance["task_id"] != attempt["task_id"]
            or not isinstance(digest, str) or len(digest) != 64
            or any(character not in "0123456789abcdef" for character in digest)
            or any(type(clearance[key]) is not bool for key in (
                "checker_binding_passed", "checker_workspace_unchanged",
                "protected_workspace_passed", "task_fidelity_passed",
                "shared_recipe_or_admission_defect",
            ))
            or (clearance["task_fidelity_passed"] != (
                clearance["checker_binding_passed"]
                and clearance["checker_workspace_unchanged"]
                and clearance["protected_workspace_passed"]
            ))
            or (clearance["root_cause"] is None) != clearance["task_fidelity_passed"]
            or (not clearance["task_fidelity_passed"] and (
                not isinstance(clearance["root_cause"], str)
                or not clearance["root_cause"]
            ))
        ):
            raise ScoutError("invalid or drifted launch fidelity clearance")
        clearances.append(clearance)
    if {item["static_clearance_sha256"] for item in clearances} != {
        static_fidelity["clearance_sha256"]
    }:
        raise ScoutError("static fidelity clearance hash drift")
    bindings = {item["id"]: item for item in cohort["tasks"]}
    tasks: dict[str, dict[str, Any]] = {}
    for task_id, binding in bindings.items():
        task_attempts = [item for item in attempts if item["task_id"] == task_id]
        if len(task_attempts) != 3:
            raise ScoutError("classification requires three usable attempts per task")
        task_clearances = [item["fidelity_clearance"] for item in task_attempts]
        invalid = any(item.get("valid") is not True for item in task_attempts) or any(
            not item["task_fidelity_passed"] for item in task_clearances
        )
        results = [item.get("checker_result") for item in task_attempts]
        if any(not isinstance(item, dict) for item in results):
            raise ScoutError("usable attempt lacks checker evidence")
        for result in results:
            requirements, _ = _checker_sections(result)
            if list(requirements) != binding["requirements"]:
                raise ScoutError("checker requirement ordering or identity drift")
        resolved = sum(bool(result["resolved"]) for result in results)
        passed = sum(item["passed"] for result in results for item in result["requirements"].values())
        total = 3 * len(binding["requirements"])
        q = passed / total
        wrong_failure = any(not result["resolved"] and not _omission_only(result) for result in results)
        if invalid:
            label = "invalid"
        elif wrong_failure:
            label = "wrong-failure-mode"
        elif resolved in (1, 2) and 0.55 <= q <= 0.90:
            label = "promising"
        elif resolved == 3 or (resolved in (1, 2) and q > 0.90):
            label = "ceiling"
        elif resolved == 0 or (resolved in (1, 2) and q < 0.55):
            label = "floor"
        else:  # Defensive totality; frozen thresholds make this unreachable.
            raise ScoutError("classification is not total")
        tasks[task_id] = {
            "author_id": binding["author_id"], "family_id": binding["family_id"],
            "label": label, "q": q, "passed_requirement_observations": passed,
            "total_requirement_observations": total, "resolved_count": resolved,
            "all_nonresolutions_omission_only": not wrong_failure,
            "fidelity_defect": any(not item["task_fidelity_passed"] for item in task_clearances),
        }
    root_tasks: dict[str, set[str]] = {}
    for clearance in clearances:
        root_cause = clearance["root_cause"]
        if root_cause:
            root_tasks.setdefault(root_cause, set()).add(clearance["task_id"])
    roots = {root_cause: len(task_ids) for root_cause, task_ids in root_tasks.items()}
    shared_fidelity = any(count >= 2 for count in roots.values()) or any(
        item["shared_recipe_or_admission_defect"] for item in clearances
    )
    promising = [task_id for task_id, item in tasks.items() if item["label"] == "promising" and not item["fidelity_defect"]]
    witnesses: list[str] = []
    if not shared_fidelity:
        for index, left in enumerate(promising):
            for right in promising[index + 1:]:
                if tasks[left]["author_id"] != tasks[right]["author_id"] and tasks[left]["family_id"] != tasks[right]["family_id"]:
                    witnesses = [left, right]
                    break
            if witnesses:
                break
    return {
        "schema": SCOUT_REPORT_SCHEMA, "decision": "SCOUT_PASS" if witnesses else "SCOUT_NO_PASS",
        "usable_attempts": 18, "tasks": tasks, "witness_task_ids": witnesses,
        "checker_fidelity_root_causes": roots, "shared_fidelity_defect": shared_fidelity,
        "interpretation": "replicated-existence-only-no-scaling",
    }


_ROLLING_BINDING_KEYS = {"id", "author_id", "family_id", "requirements", "recipe_sha256",
    "task_sha256", "public_tree_sha256", "checker_sha256", "admission_sha256", "reference_sha256", "issue_contract_sha256", "blind_submission_sha256"}
def _rolling_binding(value: Any) -> dict[str, Any]:
    binding = _strict(value, _ROLLING_BINDING_KEYS, "rolling task binding")
    for key in ("id", "author_id", "family_id"):
        if not isinstance(binding[key], str) or not binding[key]:
            raise ScoutError(f"invalid rolling {key}")
    requirements = binding["requirements"]
    if (
        not isinstance(requirements, list) or not 8 <= len(requirements) <= 12
        or any(not isinstance(item, str) or not item for item in requirements)
        or len(set(requirements)) != len(requirements)
    ):
        raise ScoutError("rolling tasks require 8 through 12 unique requirements")
    for key in _ROLLING_BINDING_KEYS - {"id", "author_id", "family_id", "requirements"}:
        _require_sha(binding[key], key)
    return binding
def validate_rolling_semantic_clearance(binding: dict[str, Any], clearance: dict[str, Any] | None, *, phase: str) -> dict[str, Any]:
    """Mechanically bind a checker-aware human clearance; never infer semantics."""
    binding = _rolling_binding(binding)
    keys = {"schema", "status", "task_id", "author_id", "phase", "blind_validator_id", "semantic_reviewer_id", "clearance_stage", "task_sha256",
        "public_tree_sha256", "checker_sha256", "admission_sha256", "issue_contract_sha256", "blind_submission_sha256", "recipe_sha256",
        "scored_requirement_ids", "all_scored_requirements_in_scope", "all_checker_constraints_public", "hidden_specificity_absent",
        "scope_routing_contradictions_absent", "recipe_task_independent", "mechanical_admission_only", "producer_received_only_frozen_recipe"}
    if not isinstance(clearance, dict):
        raise ScoutError("rolling semantic clearance is required")
    _strict(clearance, keys, "rolling semantic clearance")
    bound = {"task_sha256", "public_tree_sha256", "checker_sha256", "admission_sha256", "issue_contract_sha256", "blind_submission_sha256", "recipe_sha256"}
    booleans = {"all_scored_requirements_in_scope", "all_checker_constraints_public", "hidden_specificity_absent", "scope_routing_contradictions_absent",
        "recipe_task_independent", "mechanical_admission_only", "producer_received_only_frozen_recipe"}
    if (
        clearance["schema"] != ROLLING_CLEARANCE_SCHEMA
        or clearance["status"] != "PASS"
        or clearance["task_id"] != binding["id"]
        or clearance["author_id"] != binding["author_id"]
        or clearance["phase"] != phase
        or clearance["blind_validator_id"] == binding["author_id"]
        or clearance["semantic_reviewer_id"] == binding["author_id"]
        or not all(isinstance(clearance[key], str) and clearance[key] for key in (
            "blind_validator_id", "semantic_reviewer_id"
        ))
        or clearance["clearance_stage"] != "after-blind-submission-before-subject-exposure"
        or any(clearance[key] != binding[key] for key in bound)
        or clearance["scored_requirement_ids"] != binding["requirements"]
        or any(type(clearance[key]) is not bool for key in booleans)
        or not all(clearance[key] for key in booleans - {
            "mechanical_admission_only", "producer_received_only_frozen_recipe"
        })
        or (phase == "replication" and not (
            clearance["mechanical_admission_only"]
            and clearance["producer_received_only_frozen_recipe"]
        ))
    ):
        raise ScoutError("rolling semantic clearance failed or drifted")
    return clearance
def _rolling_launch_clearance(attempt: dict[str, Any]) -> dict[str, Any]:
    clearance = attempt.get("fidelity_clearance")
    keys = {"schema", "static_clearance_sha256", "static_status", "task_id", "checker_binding_passed", "checker_workspace_unchanged",
        "protected_workspace_passed", "task_fidelity_passed", "root_cause", "shared_recipe_or_admission_defect"}
    if not isinstance(clearance, dict) or set(clearance) != keys:
        raise ScoutError("missing or malformed rolling launch fidelity clearance")
    digest = clearance["static_clearance_sha256"]
    passed = clearance["task_fidelity_passed"]
    if (
        clearance["schema"] != LAUNCH_FIDELITY_SCHEMA
        or clearance["static_status"] != "PASS"
        or clearance["task_id"] != attempt.get("task_id")
        or not isinstance(digest, str) or len(digest) != 64
        or any(character not in "0123456789abcdef" for character in digest)
        or any(type(clearance[key]) is not bool for key in (
            "checker_binding_passed", "checker_workspace_unchanged",
            "protected_workspace_passed", "task_fidelity_passed",
            "shared_recipe_or_admission_defect",
        ))
        or passed != all(clearance[key] for key in (
            "checker_binding_passed", "checker_workspace_unchanged",
            "protected_workspace_passed",
        ))
        or (clearance["root_cause"] is None) != passed
        or (not passed and (not isinstance(clearance["root_cause"], str) or not clearance["root_cause"]))
    ):
        raise ScoutError("invalid rolling launch fidelity clearance")
    return clearance
def classify_rolling_task(binding: dict[str, Any], attempts: list[dict[str, Any]]) -> dict[str, Any]:
    """Classify one task only after its three consecutive usable attempts."""
    binding = _rolling_binding(binding)
    if (
        len(attempts) != 3
        or [item.get("task_id") for item in attempts] != [binding["id"]] * 3
        or any(item.get("usable") is not True for item in attempts)
    ):
        raise ScoutError("rolling classification requires exactly three contiguous usable attempts")
    clearances = [_rolling_launch_clearance(item) for item in attempts]
    if len({item["static_clearance_sha256"] for item in clearances}) != 1:
        raise ScoutError("rolling attempts do not share one static clearance")
    results = [item.get("checker_result") for item in attempts]
    if any(not isinstance(result, dict) for result in results):
        raise ScoutError("rolling usable attempt lacks checker evidence")
    for result in results:
        requirements, regressions = _checker_sections(result)
        if list(requirements) != binding["requirements"]:
            raise ScoutError("rolling checker requirement identity drift")
        resolved = all(item["passed"] for item in (*requirements.values(), *regressions.values())) and result["integrity"]["passed"] and result["environment"]["passed"]
        if result["resolved"] != resolved:
            raise ScoutError("rolling RESOLVED is not the checker conjunction")
    resolved = sum(bool(result["resolved"]) for result in results)
    passed = sum(item["passed"] for result in results for item in result["requirements"].values())
    total = 3 * len(binding["requirements"])
    q = passed / total
    wrong = any(not result["resolved"] and not _omission_only(result) for result in results)
    invalid = any(item.get("valid") is not True for item in attempts) or any(
        not item["task_fidelity_passed"] or item["shared_recipe_or_admission_defect"]
        for item in clearances
    )
    if invalid:
        label = "invalid"
    elif wrong:
        label = "wrong-failure-mode"
    elif resolved in (1, 2) and 0.55 <= q <= 0.90:
        label = "promising"
    elif resolved == 3 or (resolved in (1, 2) and q > 0.90):
        label = "ceiling"
    else:
        label = "floor"
    roots = sorted({item["root_cause"] for item in clearances if item["root_cause"]})
    return {
        "schema": ROLLING_TASK_REPORT_SCHEMA, "task_id": binding["id"],
        "label": label, "q": q, "resolved_count": resolved,
        "passed_requirement_observations": passed,
        "total_requirement_observations": total, "usable_attempts": 3,
        "all_nonresolutions_omission_only": not wrong,
        "fidelity_defect": invalid, "fidelity_root_causes": roots,
        "shared_recipe_or_admission_defect": any(
            item["shared_recipe_or_admission_defect"] for item in clearances
        ),
    }
def new_rolling_state(campaign_id: str) -> dict[str, Any]:
    if not isinstance(campaign_id, str) or not campaign_id:
        raise ScoutError("rolling campaign id is required")
    return {
        "schema": ROLLING_STATE_SCHEMA, "campaign_id": campaign_id,
        "status": "EXPLORATION", "candidates": [], "exploration_count": 0,
        "replication_count": 0, "planned_usable_attempts": 0,
        "usable_attempts": 0, "winner_task_id": None,
        "winning_recipe_sha256": None, "witness_task_ids": [],
        "fidelity_root_causes": {},
    }
def advance_rolling_campaign(state: dict[str, Any], binding: dict[str, Any], report: dict[str, Any]) -> dict[str, Any]:
    """Pure bounded exploration/replication transition; preserves the denominator."""
    binding = _rolling_binding(binding)
    required_state = set(new_rolling_state("shape"))
    if not isinstance(state, dict) or set(state) != required_state or state.get("schema") != ROLLING_STATE_SCHEMA:
        raise ScoutError("malformed rolling campaign state")
    if state["status"] not in {"EXPLORATION", "REPLICATION"}:
        raise ScoutError("rolling campaign is terminal")
    if report.get("schema") != ROLLING_TASK_REPORT_SCHEMA or report.get("task_id") != binding["id"] or report.get("usable_attempts") != 3:
        raise ScoutError("rolling task report does not bind the candidate")
    if binding["id"] in {item["task_id"] for item in state["candidates"]}:
        raise ScoutError("duplicate or already exposed rolling candidate")
    if sum(item["author_id"] == binding["author_id"] for item in state["candidates"]) >= 2:
        raise ScoutError("producer identity exceeded two exposed candidates")
    phase = "exploration" if state["status"] == "EXPLORATION" else "replication"
    winner = next((item for item in state["candidates"] if item["task_id"] == state["winner_task_id"]), None)
    if phase == "replication" and (
        binding["recipe_sha256"] != state["winning_recipe_sha256"]
        or winner is None
        or binding["author_id"] == winner["author_id"]
        or binding["family_id"] == winner["family_id"]
    ):
        raise ScoutError("replica must use the frozen recipe and differ in author and family")
    candidates = list(state["candidates"])
    diagnosis = {
        "task_id": binding["id"], "phase": phase, "author_id": binding["author_id"],
        "family_id": binding["family_id"], "recipe_sha256": binding["recipe_sha256"],
        "label": report["label"], "q": report["q"],
        "resolved_count": report["resolved_count"],
        "fidelity_defect": report["fidelity_defect"],
        "fidelity_root_causes": report["fidelity_root_causes"],
        "shared_recipe_or_admission_defect": report["shared_recipe_or_admission_defect"],
    }
    candidates.append(diagnosis)
    roots = dict(state["fidelity_root_causes"])
    for root in report["fidelity_root_causes"]:
        roots[root] = int(roots.get(root, 0)) + 1
    result = {
        **state, "candidates": candidates,
        "exploration_count": state["exploration_count"] + (phase == "exploration"),
        "replication_count": state["replication_count"] + (phase == "replication"),
        "planned_usable_attempts": state["planned_usable_attempts"] + 3,
        "usable_attempts": state["usable_attempts"] + 3,
        "fidelity_root_causes": roots,
    }
    if len(candidates) > 12 or result["planned_usable_attempts"] > 36:
        raise ScoutError("rolling campaign cap exceeded")
    shared = report["shared_recipe_or_admission_defect"] or any(count >= 2 for count in roots.values())
    clean_promising = report["label"] == "promising" and not report["fidelity_defect"]
    if shared:
        result["status"] = "ROLLING_NO_PASS"
    elif phase == "exploration" and clean_promising:
        result["status"] = "REPLICATION"
        result["winner_task_id"] = binding["id"]
        result["winning_recipe_sha256"] = binding["recipe_sha256"]
    elif phase == "exploration" and result["exploration_count"] == 6:
        result["status"] = "ROLLING_NO_PASS"
    elif phase == "replication" and clean_promising:
        result["status"] = "ROLLING_PASS"
        result["witness_task_ids"] = [state["winner_task_id"], binding["id"]]
    elif phase == "replication" and result["replication_count"] == 6:
        result["status"] = "ROLLING_NO_PASS"
    return result
def _rolling_manifest(authorization: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema": ROLLING_MANIFEST_SCHEMA, "campaign_id": authorization["campaign_id"],
        "authorization_sha256": authorization["authorization_sha256"],
        "gatekeeper_id": authorization["gatekeeper_id"],
        "role_schedule": authorization["role_schedule"],
    }
def _rolling_attempt(record: dict[str, Any], header: dict[str, Any]) -> dict[str, Any]:
    binding = header["binding"]
    static_base = {"schema": FIDELITY_CLEARANCE_SCHEMA, "status": "PASS", "qualification": {"sha256": header["qualification_sha256"]}, "admission": {"semantic_clearance_sha256": header["clearance"]["sha256"]}, "shared_recipe_or_admission_defect": False}
    static = {**static_base, "clearance_sha256": sha256_bytes(canonical(static_base))}
    if (
        record.get("schema") != LIVE_LAUNCH_SCHEMA or record.get("task_id") != binding["id"]
        or record.get("author_id") != binding["author_id"] or record.get("family_id") != binding["family_id"]
        or record.get("authorization_start_commit") != header["freeze"]["authorization_start_commit"]
        or record.get("freeze_commit") != header["freeze"]["freeze_commit"]
        or record.get("runtime") != header["execution"]["runtime"]
        or record.get("sandbox") != header["execution"]["sandbox"]
        or record.get("wrapper_sha256") != header["execution"]["wrapper"]["prompt_sha256"]
        or record.get("fidelity", {}).get("static") != static
        or record.get("fidelity", {}).get("launch", {}).get("static_clearance_sha256") != static["clearance_sha256"]
    ):
        raise ScoutError("rolling raw launch binding drift")
    raw, hashes = record.get("raw"), record.get("raw_evidence_sha256")
    checker = record.get("checker")
    if not isinstance(raw, dict) or not isinstance(hashes, dict) or not isinstance(checker, dict) or any(hashes.get(key) != sha256_text(value) for key, value in raw.items()) or hashes.get("checker") != sha256_bytes(canonical(checker)):
        raise ScoutError("rolling raw launch evidence hash drift")
    infrastructure = classify_infrastructure_failure(
        spawn_error=record["subject"]["spawn_error"], timed_out=record["subject"]["timed_out"],
        returncode=record["subject"]["returncode"], events_jsonl=raw["events_jsonl"],
        stderr=raw["stderr"], final_text=raw["final"],
        changed_paths=record["git"]["changed_paths"], untracked=record["git"]["untracked"],
    )
    if infrastructure != record.get("infrastructure_failure") or record.get("usable") == infrastructure:
        raise ScoutError("rolling launch usability/replacement drift")
    fidelity = record.get("fidelity", {}).get("launch")
    return {
        "task_id": binding["id"], "usable": record["usable"],
        "valid": record["usable"] and fidelity.get("task_fidelity_passed") is True,
        "checker_result": checker.get("result"), "fidelity_clearance": fidelity,
    }
def _rolling_disposition(path: Path, header: dict[str, Any], launches: list[dict[str, Any]], evidence_directory: Path | None = None) -> dict[str, Any]:
    value = _canonical_json_file(path, "rolling disposition")
    _strict(value, {
        "schema", "status", "task_id", "gatekeeper_id", "header_sha256",
        "qualification_sha256", "launches", "semantic_fidelity_passed",
        "root_cause", "shared_recipe_or_admission_defect",
    }, "rolling disposition")
    directory = evidence_directory or path.parent
    expected = [{"path": f"launch-{index:03d}.json", "sha256": sha256_file(directory / f"launch-{index:03d}.json")} for index in range(1, len(launches) + 1)]
    passed = value["semantic_fidelity_passed"]
    if (
        value["schema"] != ROLLING_DISPOSITION_SCHEMA or value["status"] != "PASS"
        or value["task_id"] != header["binding"]["id"] or value["gatekeeper_id"] != header["roles"]["gatekeeper_id"]
        or value["header_sha256"] != sha256_file(directory / "header.json")
        or value["qualification_sha256"] != header["qualification_sha256"] or value["launches"] != expected
        or type(passed) is not bool or type(value["shared_recipe_or_admission_defect"]) is not bool
        or (passed and value["shared_recipe_or_admission_defect"])
        or (value["root_cause"] is None) != passed or (not passed and (not isinstance(value["root_cause"], str) or not value["root_cause"]))
    ):
        raise ScoutError("rolling post-exposure disposition failed or drifted")
    return value
def verify_rolling_evidence(evidence_root: Path | str, authorization: dict[str, Any], repository_root: Path | None = None) -> dict[str, Any]:
    root = Path(evidence_root)
    if _canonical_json_file(root / "manifest.json", "rolling manifest") != _rolling_manifest(authorization) or any(path.is_symlink() for path in root.rglob("*")):
        raise ScoutError("rolling manifest, path, or authorization drift")
    directories = sorted(path for path in root.glob("candidate-*") if path.is_dir())
    state, pending, replacements = new_rolling_state(authorization["campaign_id"]), None, 0
    allowed_root = {"manifest.json", *(path.name for path in directories)}
    if (root / "summary.json").exists():
        allowed_root.add("summary.json")
    if {path.name for path in root.iterdir()} != allowed_root:
        raise ScoutError("rolling evidence contains missing, extra, or orphan paths")
    for ordinal, directory in enumerate(directories, 1):
        if directory.name != f"candidate-{ordinal:02d}" or pending is not None:
            raise ScoutError("rolling candidate evidence is not contiguous")
        header = _canonical_json_file(directory / "header.json", "rolling header")
        qualification = directory / "qualification.json"
        _strict(header, {"schema", "ordinal", "campaign_id", "phase", "binding", "candidate", "clearance", "qualification_sha256", "freeze", "roles", "execution", "authorization_sha256", "artifacts", "public"}, "rolling header")
        freeze = _strict(header["freeze"], {"authorization_start_commit", "freeze_commit"}, "rolling freeze")
        if freeze["authorization_start_commit"] != authorization["start_commit"] or not isinstance(freeze["freeze_commit"], str) or len(freeze["freeze_commit"]) != 40 or any(character not in "0123456789abcdef" for character in freeze["freeze_commit"]):
            raise ScoutError("rolling freeze drift")
        role = authorization["role_schedule"][ordinal - 1]
        qualification_value = _canonical_json_file(qualification, "rolling qualification")
        if (
            header["schema"] != ROLLING_HEADER_SCHEMA or header["ordinal"] != ordinal
            or header["campaign_id"] != authorization["campaign_id"] or header["authorization_sha256"] != authorization["authorization_sha256"]
            or header["qualification_sha256"] != sha256_file(qualification) or qualification_value.get("status") != "PASS"
            or header["roles"] != {**role, "gatekeeper_id": authorization["gatekeeper_id"]}
            or sha256_bytes(canonical(header["execution"])) != authorization["execution_sha256"]
            or header["binding"]["author_id"] != role["author_id"]
            or header["phase"] != ("exploration" if state["status"] == "EXPLORATION" else "replication")
            or header["candidate"] != {"path": header["candidate"].get("path"), "sha256": header["artifacts"].get(header["candidate"].get("path"))}
            or header["clearance"] != {"path": header["clearance"].get("path"), "sha256": header["artifacts"].get(header["clearance"].get("path"))}
        ):
            raise ScoutError("rolling pre-exposure header drift")
        _rolling_binding(header["binding"])
        if repository_root is not None:
            for relative, digest in header["artifacts"].items():
                artifact = repository_root / _safe_relative(relative, "rolling artifact")
                _reject_symlink_chain(artifact, repository_root)
                if artifact.is_symlink() or not artifact.is_file() or sha256_file(artifact) != digest:
                    raise ScoutError("prior exposed rolling artifact drift")
            public = repository_root / _safe_relative(header["public"]["path"], "rolling public")
            _reject_symlink_chain(public, repository_root)
            if public.is_symlink() or any(path.is_symlink() for path in public.rglob("*")) or tree_sha256(public) != header["public"]["tree_sha256"]:
                raise ScoutError("prior exposed rolling public packet drift")
        launch_paths = sorted(directory.glob("launch-*.json"))
        launches, attempts, inventory = [], [], []
        for launch_ordinal, launch_path in enumerate(launch_paths, 1):
            if launch_path.name != f"launch-{launch_ordinal:03d}.json":
                raise ScoutError("rolling launch inventory is not contiguous")
            launch = _canonical_json_file(launch_path, "rolling raw launch")
            if launch.get("launch_ordinal") != launch_ordinal or len(attempts) == 3:
                raise ScoutError("rolling launch ordinal or task-contiguity drift")
            attempt = _rolling_attempt(launch, header)
            launches.append(launch)
            reason = None if attempt["usable"] else (launch["subject"]["spawn_error"] or {"type": "frozen-pre-output-infrastructure"})
            inventory.append({"path": launch_path.name, "sha256": sha256_file(launch_path), "usable": attempt["usable"], "replacement_reason": reason})
            if attempt["usable"]:
                attempts.append(attempt)
            else:
                replacements += 1
        if replacements > authorization["replacement_launch_cap"]:
            raise ScoutError("rolling replacement launch cap exceeded")
        disposition_path, result_path = directory / "disposition.json", directory / "result.json"
        allowed = {"header.json", "qualification.json", *(path.name for path in launch_paths)} | ({"disposition.json"} if disposition_path.exists() else set()) | ({"result.json"} if result_path.exists() else set())
        if {path.name for path in directory.iterdir()} != allowed or result_path.exists() != disposition_path.exists():
            raise ScoutError("rolling candidate evidence set is incomplete or unexpected")
        if not disposition_path.exists():
            if len(attempts) == 3:
                classify_rolling_task(header["binding"], attempts)
            pending = {"directory": directory, "header": header, "attempts": attempts, "inventory": inventory}
            continue
        if len(attempts) != 3:
            raise ScoutError("rolling disposition requires exactly three usable attempts")
        disposition = _rolling_disposition(disposition_path, header, launches)
        report = classify_rolling_task(header["binding"], attempts)
        if not disposition["semantic_fidelity_passed"]:
            report = {**report, "label": "invalid", "fidelity_defect": True,
                      "fidelity_root_causes": sorted(set(report["fidelity_root_causes"] + [disposition["root_cause"]])),
                      "shared_recipe_or_admission_defect": disposition["shared_recipe_or_admission_defect"]}
        state = advance_rolling_campaign(state, header["binding"], report)
        result = _canonical_json_file(result_path, "rolling result")
        expected = {"schema": ROLLING_RECORD_SCHEMA, "ordinal": ordinal, "inventory": inventory, "report": report, "state_after": state, "disposition_sha256": sha256_file(disposition_path)}
        if result != expected:
            raise ScoutError("rolling result replay drift")
    terminal = state["status"] in {"ROLLING_PASS", "ROLLING_NO_PASS"}
    summary_path = root / "summary.json"
    if terminal:
        expected = {"schema": ROLLING_SUMMARY_SCHEMA, "manifest_sha256": sha256_file(root / "manifest.json"), "state": state}
        if pending is not None or _canonical_json_file(summary_path, "rolling terminal summary") != expected:
            raise ScoutError("rolling terminal summary drift")
    elif summary_path.exists():
        raise ScoutError("nonterminal rolling campaign has a summary")
    return {"state": state, "pending": pending, "replacements": replacements}
def _reject_symlink_chain(path: Path, root: Path) -> None:
    try:
        relative = path.absolute().relative_to(root.absolute())
    except ValueError as exc:
        raise ScoutError("rolling path escapes its repository") from exc
    current = root.absolute()
    for part in relative.parts:
        current /= part
        if current.is_symlink():
            raise ScoutError("symlinked rolling path or ancestor")
def _paths_overlap(left: Path, right: Path) -> bool:
    left, right = left.resolve(), right.resolve()
    return left == right or left in right.parents or right in left.parents
def _rolling_authorization(path: Path, candidate: dict[str, Any], root: Path, evidence: Path) -> dict[str, Any]:
    authorization = _canonical_json_file(path, "rolling authorization")
    _strict(authorization, {
        "schema", "campaign_id", "start_commit", "task_root", "evidence_root",
        "execution_sha256", "candidate_cap", "planned_usable_attempt_cap",
        "replacement_launch_cap", "gatekeeper_id", "role_schedule",
    }, "rolling authorization")
    execution = {
        "wrapper": candidate["wrapper"], "runtime": candidate["runtime"],
        "sandbox": candidate["sandbox"],
    }
    roles = authorization["role_schedule"]
    role_values = [item.get(key) for item in roles for key in ("author_id", "blind_validator_id")] if isinstance(roles, list) and all(isinstance(item, dict) and set(item) == {"author_id", "blind_validator_id"} for item in roles) else []
    authors = [item["author_id"] for item in roles] if role_values else []
    if (
        authorization["schema"] != ROLLING_AUTHORIZATION_SCHEMA
        or authorization["campaign_id"] != candidate["campaign_id"]
        or authorization["start_commit"] != candidate["start_commit"]
        or authorization["task_root"] != candidate["task_root"]
        or authorization["evidence_root"] != evidence.relative_to(root).as_posix()
        or authorization["execution_sha256"] != sha256_bytes(canonical(execution))
        or authorization["candidate_cap"] != 12
        or authorization["planned_usable_attempt_cap"] != 36
        or type(authorization["replacement_launch_cap"]) is not int
        or not 0 <= authorization["replacement_launch_cap"] <= 12
        or not isinstance(authorization["gatekeeper_id"], str) or not authorization["gatekeeper_id"]
        or authorization["gatekeeper_id"] in role_values
        or not isinstance(roles, list) or len(roles) != 12 or len(role_values) != 24 or any(not isinstance(value, str) or not value for value in role_values)
        or any(item["author_id"] == item["blind_validator_id"] for item in roles)
        or any(item["blind_validator_id"] not in set(authors) for item in roles)
        or any(authors.count(author) > 2 for author in set(authors))
    ):
        raise ScoutError("rolling authorization is missing, expanded, or drifted")
    return {**authorization, "authorization_sha256": sha256_file(path)}
def load_rolling_candidate(candidate_path: Path | str, clearance_path: Path | str) -> tuple[dict[str, Any], dict[str, Any]]:
    """Bind one unexposed task and its externally reviewed semantic clearance."""
    unresolved = Path(candidate_path).absolute()
    root = _repository_root(unresolved)
    _reject_symlink_chain(unresolved, root)
    _reject_symlink_chain(Path(clearance_path).absolute(), root)
    path = unresolved.resolve()
    candidate = _canonical_json_file(path, "rolling candidate")
    _strict(candidate, {
        "schema", "campaign_id", "phase", "start_commit", "task_root", "recipe",
        "wrapper", "runtime", "sandbox", "authorization_sha256",
        "semantic_clearance_sha256", "task",
    }, "rolling candidate")
    if candidate["schema"] != ROLLING_CANDIDATE_SCHEMA or candidate["phase"] not in {"exploration", "replication"}:
        raise ScoutError("wrong rolling candidate identity or phase")
    binding = _rolling_binding(candidate["task"])
    recipe = _strict(candidate["recipe"], {"path", "sha256"}, "rolling recipe")
    recipe_path = _bound_file(root, recipe["path"], binding["recipe_sha256"], "rolling recipe")
    if recipe["sha256"] != binding["recipe_sha256"] or _canonical_json_file(recipe_path, "rolling recipe").get("task_independent") is not True:
        raise ScoutError("rolling recipe is not task-independent or bound")
    wrapper = _strict(candidate["wrapper"], {"prompt_sha256", "source_path", "source_sha256"}, "rolling wrapper")
    if wrapper["prompt_sha256"] != sha256_text(WRAPPER_PROMPT):
        raise ScoutError("rolling wrapper drifted")
    _bound_file(root, wrapper["source_path"], wrapper["source_sha256"], "rolling wrapper source")
    if candidate["runtime"] != {
        "type": "codex-cli", "model": "gpt-5.6-sol", "reasoning_effort": "high",
        "timeout_seconds": 300, "approval_policy": "never", "ephemeral": True,
        "max_parallel_runs": 1, "variant": "null-only",
    } or candidate["sandbox"] != {
        "mode": "workspace-write", "network_access": False, "subagents_enabled": False,
        "ignore_user_config": True, "ignore_rules": True,
    }:
        raise ScoutError("rolling runtime or sandbox drifted")
    task_root = root / _safe_relative(candidate["task_root"], "rolling task root")
    task_dir = task_root / _safe_relative(binding["id"], "rolling task id")
    task = _canonical_json_file(_bound_file(task_dir, "task.json", binding["task_sha256"], "rolling task"), "rolling task")
    requirements = task.get("requirements")
    if (
        not isinstance(requirements, list) or
        task.get("schema") != "mdseval.scout-task-v1" or
        task.get("id") != binding["id"] or task.get("author_id") != binding["author_id"]
        or task.get("family_id") != binding["family_id"]
        or [item.get("id") for item in requirements] != binding["requirements"]
        or task.get("recipe", {}).get("sha256") != binding["recipe_sha256"]
        or task.get("checker_path") != "check.py" or task.get("admission_path") != "admission.json"
        or task.get("reference_path") != "reference.json" or task.get("network_allowed") is not False
        or task.get("standard_library_only") is not True or task.get("dependencies") != []
        or task.get("timeout_seconds") != 300 or not isinstance(task.get("protected_paths"), list)
        or not {"CODER.md", ".issue-contract.md"}.issubset(task["protected_paths"])
    ):
        raise ScoutError("rolling task metadata or requirements drifted")
    public = task_dir / "public"
    issue = public / ".issue-contract.md"
    if (
        public.is_symlink() or any(item.is_symlink() for item in public.rglob("*"))
        or not issue.is_file() or
        tree_sha256(public) != binding["public_tree_sha256"]
        or (public / "CODER.md").read_bytes() != b""
        or sha256_file(issue) != binding["issue_contract_sha256"]
        or any(item.name in {"task.json", "admission.json", "reference.json", "blind-submission.json", "check.py", ".git", ".codex", ".agents", "AGENTS.md", "AGENTS.override.md"} for item in public.rglob("*"))
    ):
        raise ScoutError("rolling public packet drifted")
    checker = _bound_file(task_dir, task["checker_path"], binding["checker_sha256"], "rolling checker")
    admission = _canonical_json_file(_bound_file(task_dir, task["admission_path"], binding["admission_sha256"], "rolling admission"), "rolling admission")
    _bound_file(task_dir, task["reference_path"], binding["reference_sha256"], "rolling reference")
    blind = _canonical_json_file(_bound_file(task_dir, "blind-submission.json", binding["blind_submission_sha256"], "blind submission"), "blind submission")
    trace = admission.get("trace")
    mutants = admission.get("mutants")
    if (
        not isinstance(trace, list) or not isinstance(mutants, list) or
        [item.get("requirement_id") for item in trace] != binding["requirements"]
        or [item.get("requirement_id") for item in mutants] != binding["requirements"]
        or admission.get("protected_inputs") != [
            {"path": item, "sha256": sha256_file(public / item)} for item in task["protected_paths"]
        ]
        or not isinstance(blind, dict) or not blind
    ):
        raise ScoutError("rolling admission, mutant, or blind submission drifted")
    for item in trace:
        traced = _bound_file(public, item["public_path"], item["public_text_sha256"], "rolling public trace")
        requirement_id = item["requirement_id"]
        if (
            item["public_locator"] not in traced.read_text(encoding="utf-8")
            or item["pass_predicate"] != f"$.requirements.{requirement_id}.passed == true"
            or item["omission_predicate"] != f"$.requirements.{requirement_id}.passed == false"
        ):
            raise ScoutError("rolling public trace locator drifted")
    clearance = _canonical_json_file(Path(clearance_path).resolve(), "rolling semantic clearance")
    if sha256_file(Path(clearance_path)) != candidate["semantic_clearance_sha256"]:
        raise ScoutError("rolling semantic clearance hash drift")
    validate_rolling_semantic_clearance(binding, clearance, phase=candidate["phase"])
    artifacts = [path, Path(clearance_path).resolve(), recipe_path, root / wrapper["source_path"], task_dir / "task.json", checker, task_dir / "admission.json", task_dir / "reference.json", task_dir / "blind-submission.json"]
    for artifact in artifacts:
        _reject_symlink_chain(artifact, root)
    return {**candidate, "tasks": [binding], "_root": root, "_blind": blind, "_checker": checker, "_artifacts": {item.relative_to(root).as_posix(): sha256_file(item) for item in artifacts}}, clearance
def _qualify_rolling_candidate(candidate: dict[str, Any]) -> dict[str, Any]:
    root, binding = candidate["_root"], candidate["task"]
    qualification = _qualify_task(root, candidate, binding)
    task_dir = root / candidate["task_root"] / binding["id"]
    task = _canonical_json_file(task_dir / "task.json", "rolling task")
    signatures: list[str] = []
    protected_expected = _protected_hashes(task_dir / "public", task["protected_paths"])
    with tempfile.TemporaryDirectory(prefix="mdseval-rolling-blind-") as temporary:
        for replay in (1, 2):
            workspace = Path(temporary) / str(replay)
            _copy_public(task_dir / "public", workspace)
            _replace_text_files(workspace, candidate["_blind"])
            checked = _run_objective_checker(candidate["_checker"], workspace)
            if not checked["result"]["resolved"] or _protected_hashes(workspace, task["protected_paths"]) != protected_expected:
                raise ScoutError("blind contract-only submission failed")
            signatures.append(checked["stdout_sha256"])
    if len(set(signatures)) != 1:
        raise ScoutError("blind contract-only submission is nondeterministic")
    return {"status": "PASS", "qualification": qualification, "blind_replay_sha256": signatures}
def _runner_config(cohort: dict[str, Any]) -> RunnerConfig:
    runtime, sandbox = cohort["runtime"], cohort["sandbox"]
    return RunnerConfig(
        type=runtime["type"], model=runtime["model"], reasoning_effort=runtime["reasoning_effort"],
        sandbox=sandbox["mode"], approval_policy=runtime["approval_policy"],
        subagents_enabled=sandbox["subagents_enabled"], ephemeral=runtime["ephemeral"],
        network_for_agent_commands=sandbox["network_access"], timeout_seconds=runtime["timeout_seconds"],
        max_parallel_runs=runtime["max_parallel_runs"],
    )


def preflight_live_scout(cohort_path: Path | str) -> dict[str, Any]:
    """Validate exact CLI/config/auth locally; never launches a subject call."""
    cohort = load_cohort(cohort_path)
    runner = _runner_config(cohort)
    judge = JudgeConfig(type="codex-cli", model=runner.model, reasoning_effort=runner.reasoning_effort, sandbox="read-only", timeout_seconds=300)
    result = doctor(SimpleNamespace(runner=runner, judge=judge))
    home_value = os.environ.get("MDSEVAL_CODEX_HOME")
    auth = Path(home_value).expanduser() / "auth.json" if home_value else None
    auth_ready = bool(auth and auth.is_file() and not auth.is_symlink() and auth.stat().st_size > 0)
    if not result.available or not auth_ready:
        raise ScoutError(f"exact live runtime unavailable: {result.code}; isolated_auth={auth_ready}")
    expected = build_codex_command(runner, Path("<subject-repository>"), Path("<final-message>"))
    if tuple(expected) != result.command:
        raise ScoutError("preflight command binding drift")
    return {"status": "PASS", "code": result.code, "isolated_auth": True, "command": expected, "checks": result.checks}


def validate_live_freeze(
    repository: Path, authorization_start_commit: str, freeze_commit: str
) -> dict[str, str]:
    """Fail closed unless the tracked repository is exactly the operator freeze."""
    if not isinstance(freeze_commit, str) or len(freeze_commit) != 40 or any(
        character not in "0123456789abcdef" for character in freeze_commit
    ):
        raise ScoutError("freeze commit must be a full lowercase Git object id")
    try:
        run_git(repository, "cat-file", "-e", f"{freeze_commit}^{{commit}}")
        head = str(run_git(repository, "rev-parse", "HEAD")).strip()
        tracked_status = str(
            run_git(repository, "status", "--porcelain", "--untracked-files=no")
        )
        run_git(
            repository, "merge-base", "--is-ancestor",
            authorization_start_commit, freeze_commit,
        )
    except RuntimeError as exc:
        raise ScoutError("freeze commit is absent or not authorization-descended") from exc
    if head != freeze_commit:
        raise ScoutError("repository HEAD does not equal the operator freeze commit")
    if tracked_status:
        raise ScoutError("tracked index or worktree is dirty")
    return {
        "authorization_start_commit": authorization_start_commit,
        "freeze_commit": freeze_commit,
    }


def build_fidelity_clearance(
    cohort: dict[str, Any], qualification_root: Path
) -> dict[str, Any]:
    """Bind PASS clearance to all canonical offline qualification/admission bytes."""
    manifest_path = qualification_root / "manifest.json"
    summary_path = qualification_root / "summary.json"
    manifest = _canonical_json_file(manifest_path, "qualification manifest")
    summary = _canonical_json_file(summary_path, "qualification summary")
    if summary.get("status") != "PASS" or manifest.get("task_records") != summary.get("task_records"):
        raise ScoutError("qualification cannot provide fidelity clearance")
    base = {
        "schema": FIDELITY_CLEARANCE_SCHEMA,
        "status": "PASS",
        "qualification": {
            "manifest_sha256": sha256_file(manifest_path),
            "summary_sha256": sha256_file(summary_path),
            "task_records": summary["task_records"],
        },
        "admission": {
            "status": cohort["admission_evidence"]["status"],
            "files": cohort["admission_evidence"]["files"],
        },
        "shared_recipe_or_admission_defect": False,
    }
    return {**base, "clearance_sha256": sha256_bytes(canonical(base))}


_SPAWN_INFRASTRUCTURE_ERRNOS = frozenset(
    {errno.EACCES, errno.EAGAIN, errno.EMFILE, errno.ENFILE, errno.ENOENT,
     errno.ENOEXEC, errno.ENOMEM}
)


def _structured_spawn_error(exc: OSError, redactor: Redactor) -> dict[str, Any]:
    return {
        "type": type(exc).__name__,
        "message": redactor.text(str(exc)),
        "errno": exc.errno,
    }


def _capture_subject_launch(call: Any, redactor: Redactor) -> tuple[ProcessOutcome, dict[str, Any] | None]:
    try:
        return call(), None
    except OSError as exc:
        return (
            ProcessOutcome(None, "", "", False, True),
            _structured_spawn_error(exc, redactor),
        )


def _protected_workspace_matches(
    workspace: Path, protected_inputs: list[dict[str, str]]
) -> bool:
    for item in protected_inputs:
        path = workspace / _safe_relative(item["path"], "protected path")
        if path.is_symlink() or not path.is_file() or sha256_file(path) != item["sha256"]:
            return False
    return True


_INFRASTRUCTURE_ERROR_MARKERS = (
    "authentication failed",
    "not authenticated",
    "unauthorized",
    "invalid api key",
    "missing api key",
    "login required",
    "unknown configuration field",
    "failed to load config",
    "invalid configuration",
    "configuration error",
    "service unavailable",
    "temporarily unavailable",
    "server overloaded",
    "rate limit exceeded",
    "failed to connect",
    "connection refused",
    "connection reset",
    "transport error",
    "dns resolution failed",
)


def classify_infrastructure_failure(
    *,
    spawn_error: dict[str, Any] | None,
    timed_out: bool,
    returncode: int | None,
    events_jsonl: str,
    stderr: str,
    final_text: str,
    changed_paths: tuple[str, ...] | list[str],
    untracked: tuple[dict[str, Any], ...] | list[dict[str, Any]],
) -> bool:
    """Narrow, pure pre-output infrastructure classification for replacements."""
    if timed_out or final_text or changed_paths or untracked:
        return False
    if spawn_error is not None:
        return (
            set(spawn_error) == {"type", "message", "errno"}
            and spawn_error["type"] in {"FileNotFoundError", "PermissionError", "OSError"}
            and isinstance(spawn_error["message"], str)
            and spawn_error["errno"] in _SPAWN_INFRASTRUCTURE_ERRNOS
            and not events_jsonl and not stderr
        )
    if returncode in (0, None):
        return False
    structured_errors: list[str] = []
    saw_agent_output = False
    saw_structured_event = False
    for line in events_jsonl.splitlines():
        if not line.strip():
            continue
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            return False
        if not isinstance(event, dict):
            return False
        saw_structured_event = True
        event_type = event.get("type")
        item = event.get("item")
        is_error = event_type in {"error", "turn.failed"} or (
            event_type == "item.completed"
            and isinstance(item, dict)
            and item.get("type") == "error"
        )
        if is_error:
            structured_errors.append(json.dumps(event, sort_keys=True).lower())
        elif event_type not in {"thread.started", "turn.started"}:
            saw_agent_output = True
    if saw_agent_output:
        return False
    error_text = " ".join(structured_errors)
    if not error_text and not saw_structured_event:
        error_text = stderr.lower()
    return any(marker in error_text for marker in _INFRASTRUCTURE_ERROR_MARKERS)


def _write_live_launch_record(
    evidence_root: Path, launch_ordinal: int, record: dict[str, Any]
) -> str:
    if not 1 <= launch_ordinal <= 24:
        raise ScoutError("live launch ordinal is outside the frozen cap")
    return _write_json_once(
        evidence_root / f"launch-{launch_ordinal:03d}.json", record
    )


def _live_launch(
    root: Path, cohort: dict[str, Any], task_id: str, launch_ordinal: int,
    evidence_root: Path, *, freeze: dict[str, str], static_fidelity: dict[str, Any],
    process_runner: Any, redactor: Redactor,
) -> dict[str, Any]:
    binding = next(item for item in cohort["tasks"] if item["id"] == task_id)
    task_dir = root / cohort["task_root"] / task_id
    task = _canonical_json_file(task_dir / "task.json", "task")
    admission = _canonical_json_file(task_dir / "admission.json", "admission")
    checker = task_dir / "check.py"
    with tempfile.TemporaryDirectory(prefix=f"mdseval-live-{task_id}-") as temporary:
        workspace = Path(temporary) / "subject"
        _copy_public(task_dir / "public", workspace)
        if (workspace / "CODER.md").read_bytes() != b"":
            raise ScoutError("live subject CODER.md is not zero-byte")
        init_repository(workspace)
        run_git(workspace, "config", "user.name", "MD Eval")
        run_git(workspace, "config", "user.email", "mdseval@invalid.local")
        run_git(workspace, "add", "--all")
        run_git(workspace, "commit", "-q", "-m", "baseline")
        baseline = str(run_git(workspace, "rev-parse", "HEAD")).strip()
        runner = _runner_config(cohort)
        final_path = Path(temporary) / "final.txt"
        command = build_codex_command(runner, workspace, final_path)
        started = time.monotonic()
        subject, subject_error = _capture_subject_launch(
            lambda: process_runner(
                command, cwd=workspace, input_text=WRAPPER_PROMPT,
                timeout=runner.timeout_seconds,
                environment=isolated_environment(os.environ["MDSEVAL_CODEX_HOME"]),
            ),
            redactor,
        )
        duration = time.monotonic() - started
        final_text = final_path.read_text(encoding="utf-8", errors="replace") if final_path.is_file() else ""
        audit_final_subject_tree(workspace)
        git_capture = capture_git(workspace, baseline, redactor)
        checker_before_tree = tree_sha256(workspace)
        checker_before_sha = sha256_file(checker)
        checker_environment = safe_process_environment()
        checker_environment["PYTHONDONTWRITEBYTECODE"] = "1"
        checker_error = ""
        try:
            checked = process_runner(
                [sys.executable, str(checker), str(workspace)], cwd=checker.parent,
                input_text=None, timeout=60, environment=checker_environment,
            )
        except OSError as exc:
            checker_error = type(exc).__name__
            checked = ProcessOutcome(None, "", "", False, True)
        checker_unchanged = checker_before_tree == tree_sha256(workspace) and checker_before_sha == sha256_file(checker)
        checker_result: dict[str, Any] | None = None
        if not checker_error and not checked.timed_out and not checked.interrupted and checked.returncode == 0 and checker_unchanged:
            try:
                candidate = json.loads(checked.stdout)
                if isinstance(candidate, dict) and checked.stdout == canonical(candidate).decode("utf-8"):
                    _checker_sections(candidate)
                    if candidate.get("task_id") == task_id and list(candidate["requirements"]) == binding["requirements"]:
                        checker_result = candidate
            except (json.JSONDecodeError, ScoutError):
                checker_result = None
        infrastructure_failure = classify_infrastructure_failure(
            spawn_error=subject_error,
            timed_out=subject.timed_out,
            returncode=subject.returncode,
            events_jsonl=subject.stdout,
            stderr=subject.stderr,
            final_text=final_text,
            changed_paths=git_capture.changed_paths,
            untracked=git_capture.untracked,
        )
        usable = checker_result is not None and not infrastructure_failure
        if checker_result is None and not infrastructure_failure:
            checker_error = checker_error or "UNSCOREABLE_CHECKER_EVIDENCE"
        subject_stdout = redact_event_stream(subject.stdout, redactor)
        subject_stderr = redactor.text(subject.stderr)
        final_safe = redactor.text(final_text)
        checker_stdout = redactor.text(checked.stdout)
        checker_stderr = redactor.text(checked.stderr)
        checker_evidence = {
            "scoreable": checker_result is not None, "result": checker_result,
            "workspace_unchanged": checker_unchanged, "error": checker_error,
            "returncode": checked.returncode, "timed_out": checked.timed_out,
            "interrupted": checked.interrupted,
        }
        checker_binding_passed = (
            checker_before_sha == binding["checker_sha256"]
            and sha256_file(checker) == binding["checker_sha256"]
        )
        protected_workspace_passed = _protected_workspace_matches(
            workspace, admission["protected_inputs"]
        )
        task_fidelity_passed = (
            checker_binding_passed and checker_unchanged and protected_workspace_passed
        )
        root_cause = (
            None if task_fidelity_passed
            else "checker-binding" if not checker_binding_passed
            else "checker-workspace" if not checker_unchanged
            else "protected-workspace"
        )
        launch_fidelity = {
            "schema": LAUNCH_FIDELITY_SCHEMA,
            "static_clearance_sha256": static_fidelity["clearance_sha256"],
            "static_status": static_fidelity["status"], "task_id": task_id,
            "checker_binding_passed": checker_binding_passed,
            "checker_workspace_unchanged": checker_unchanged,
            "protected_workspace_passed": protected_workspace_passed,
            "task_fidelity_passed": task_fidelity_passed,
            "root_cause": root_cause,
            "shared_recipe_or_admission_defect": static_fidelity["shared_recipe_or_admission_defect"],
        }
        raw = {
            "events_jsonl": subject_stdout,
            "stderr": subject_stderr,
            "final": final_safe,
            "checker_stdout": checker_stdout,
            "checker_stderr": checker_stderr,
        }
        raw_hashes = {
            name: sha256_text(contents) for name, contents in raw.items()
        }
        raw_hashes["checker"] = sha256_bytes(canonical(checker_evidence))
        record = {
            "schema": LIVE_LAUNCH_SCHEMA, "launch_ordinal": launch_ordinal,
            "task_id": task_id, "author_id": binding["author_id"], "family_id": binding["family_id"],
            "authorization_start_commit": freeze["authorization_start_commit"],
            "freeze_commit": freeze["freeze_commit"],
            "wrapper_sha256": cohort["wrapper"]["prompt_sha256"],
            "runtime": cohort["runtime"], "sandbox": cohort["sandbox"], "command": command,
            "subject": {"returncode": subject.returncode, "timed_out": subject.timed_out, "interrupted": subject.interrupted, "duration_seconds": duration, "spawn_error": subject_error},
            "git": asdict(git_capture), "raw": raw, "checker": checker_evidence,
            "fidelity": {"static": static_fidelity, "launch": launch_fidelity},
            "raw_evidence_sha256": raw_hashes,
            "usable": usable, "infrastructure_failure": infrastructure_failure,
        }
        _write_live_launch_record(evidence_root, launch_ordinal, record)
    return {
        "task_id": task_id, "usable": usable,
        "infrastructure_failure": infrastructure_failure,
        "valid": usable and task_fidelity_passed,
        "checker_result": checker_result, "fidelity_clearance": launch_fidelity,
    }


def run_live_scout(
    cohort_path: Path | str, qualification_root: Path | str, output: Path | str,
    *, freeze_commit: str, process_runner: Any = run_process_group,
    redactor: Redactor | None = None,
) -> dict[str, Any]:
    """Run only the frozen serial null scout; this function is never used by tests."""
    cohort_path = Path(cohort_path).resolve()
    cohort = load_cohort(cohort_path)
    root = _repository_root(cohort_path)
    freeze = validate_live_freeze(root, cohort["start_commit"], freeze_commit)
    qualification = verify_qualification(cohort_path, qualification_root)
    static_fidelity = build_fidelity_clearance(cohort, Path(qualification_root))
    preflight = preflight_live_scout(cohort_path)
    evidence = Path(output).resolve()
    if evidence.exists():
        raise ScoutError("live scout evidence is create-once")
    evidence.mkdir(parents=True)
    _write_json_once(
        evidence / "manifest.json",
        {
            "schema": "mdseval.coder-beneficial-sensitivity-m2-live-manifest-v1",
            "cohort_sha256": sha256_file(cohort_path),
            "qualification_summary_sha256": sha256_file(Path(qualification_root) / "summary.json"),
            "runtime_preflight_code": preflight["code"], "variant": "null-only",
            "schedule": cohort["schedule"],
            "authorization_start_commit": freeze["authorization_start_commit"],
            "freeze_commit": freeze["freeze_commit"],
            "fidelity_clearance": static_fidelity,
        },
    )
    state: dict[str, Any] = {"launches": 0, "usable": 0, "replacements": 0, "replacements_by_author": {}}
    attempts: list[dict[str, Any]] = []
    redactor = redactor or Redactor()
    while state["usable"] < 18:
        task_id = cohort["schedule"][state["usable"]]
        attempt = _live_launch(
            root, cohort, task_id, state["launches"] + 1, evidence,
            freeze=freeze, static_fidelity=static_fidelity,
            process_runner=process_runner, redactor=redactor,
        )
        if not attempt["usable"] and not attempt["infrastructure_failure"]:
            raise ScoutError("unscoreable non-infrastructure launch cannot be replaced")
        state = record_launch(cohort, state, task_id, usable=attempt["usable"], infrastructure_failure=attempt["infrastructure_failure"])
        if attempt["usable"]:
            attempts.append(attempt)
    report = classify_scout(cohort, attempts, static_fidelity)
    report["launches"] = state["launches"]
    report["replacements"] = state["replacements"]
    report["qualification_status"] = qualification["status"]
    _write_json_once(evidence / "report.json", report)
    return report
def run_live_rolling_candidate(
    candidate_path: Path | str, clearance_path: Path | str,
    authorization_path: Path | str, output: Path | str, *, freeze_commit: str,
    process_runner: Any = run_process_group, redactor: Redactor | None = None,
) -> dict[str, Any]:
    """Expose one qualified task; a separate semantic disposition advances state."""
    candidate_input, clearance_input = Path(candidate_path), Path(clearance_path)
    candidate, clearance = load_rolling_candidate(candidate_input, clearance_input)
    candidate_path, clearance_path = candidate_input.resolve(), clearance_input.resolve()
    root = candidate["_root"]
    evidence_input = Path(output).absolute()
    _reject_symlink_chain(evidence_input, root)
    evidence = evidence_input.resolve()
    try:
        evidence.relative_to(root)
    except ValueError as exc:
        raise ScoutError("rolling evidence must remain inside the repository") from exc
    authorization_input = Path(authorization_path).absolute()
    _reject_symlink_chain(authorization_input, root)
    authorization_path = authorization_input.resolve()
    for path in (evidence, authorization_path):
        _reject_symlink_chain(path, root)
    task_root = root / candidate["task_root"]
    if _paths_overlap(evidence, task_root) or _paths_overlap(evidence, authorization_path) or any(_paths_overlap(evidence, root / relative) for relative in candidate["_artifacts"]):
        raise ScoutError("rolling evidence, task, and artifact roots overlap")
    authorization = _rolling_authorization(authorization_path, candidate, root, evidence)
    if candidate["authorization_sha256"] != authorization["authorization_sha256"]:
        raise ScoutError("rolling candidate authorization hash drift")
    freeze = validate_live_freeze(root, authorization["start_commit"], freeze_commit)
    replay = verify_rolling_evidence(evidence, authorization, root) if evidence.exists() else {
        "state": new_rolling_state(authorization["campaign_id"]), "pending": None, "replacements": 0,
    }
    if replay["pending"] is not None:
        raise ScoutError("post-exposure disposition is required before another candidate")
    state = replay["state"]
    if state["status"] not in {"EXPLORATION", "REPLICATION"}:
        raise ScoutError("rolling campaign is terminal")
    ordinal, binding = len(state["candidates"]) + 1, candidate["task"]
    role = authorization["role_schedule"][ordinal - 1]
    if binding["author_id"] != role["author_id"] or clearance["blind_validator_id"] != role["blind_validator_id"] or clearance["semantic_reviewer_id"] != authorization["gatekeeper_id"]:
        raise ScoutError("rolling candidate roles do not match authorization")
    expected_phase = "exploration" if state["status"] == "EXPLORATION" else "replication"
    if candidate["phase"] != expected_phase or state["status"] not in {"EXPLORATION", "REPLICATION"} or binding["id"] in {item["task_id"] for item in state["candidates"]}:
        raise ScoutError("rolling candidate phase, terminal state, or exposure identity is invalid")
    if expected_phase == "replication":
        winner = next(item for item in state["candidates"] if item["task_id"] == state["winner_task_id"])
        if binding["recipe_sha256"] != state["winning_recipe_sha256"] or binding["author_id"] == winner["author_id"] or binding["family_id"] == winner["family_id"]:
            raise ScoutError("rolling replica violates frozen recipe/independence")
    qualification = _qualify_rolling_candidate(candidate)
    runner = _runner_config(candidate)
    judge = JudgeConfig(type="codex-cli", model=runner.model, reasoning_effort=runner.reasoning_effort, sandbox="read-only", timeout_seconds=300)
    preflight = doctor(SimpleNamespace(runner=runner, judge=judge))
    home_value = os.environ.get("MDSEVAL_CODEX_HOME")
    auth = Path(home_value).expanduser() / "auth.json" if home_value else None
    if not preflight.available or not auth or not auth.is_file() or auth.is_symlink() or auth.stat().st_size == 0:
        raise ScoutError("exact rolling live runtime or isolated auth unavailable")
    if not evidence.exists():
        evidence.mkdir(parents=True)
        _write_json_once(evidence / "manifest.json", _rolling_manifest(authorization))
    live_root = evidence / f"candidate-{ordinal:02d}"
    live_root.mkdir()
    qualification_sha256 = _write_json_once(live_root / "qualification.json", qualification)
    execution = {"wrapper": candidate["wrapper"], "runtime": candidate["runtime"], "sandbox": candidate["sandbox"]}
    _write_json_once(live_root / "header.json", {
        "schema": ROLLING_HEADER_SCHEMA, "ordinal": ordinal, "campaign_id": authorization["campaign_id"],
        "phase": candidate["phase"], "binding": binding,
        "candidate": {"path": candidate_path.relative_to(root).as_posix(), "sha256": sha256_file(candidate_path)},
        "clearance": {"path": clearance_path.relative_to(root).as_posix(), "sha256": sha256_file(clearance_path)},
        "qualification_sha256": qualification_sha256, "freeze": freeze,
        "roles": {**role, "gatekeeper_id": authorization["gatekeeper_id"]}, "execution": execution,
        "authorization_sha256": authorization["authorization_sha256"], "artifacts": candidate["_artifacts"],
        "public": {"path": f"{candidate['task_root']}/{binding['id']}/public", "tree_sha256": binding["public_tree_sha256"]},
    })
    static_base = {
        "schema": FIDELITY_CLEARANCE_SCHEMA, "status": "PASS",
        "qualification": {"sha256": sha256_bytes(canonical(qualification))},
        "admission": {"semantic_clearance_sha256": sha256_file(Path(clearance_path))},
        "shared_recipe_or_admission_defect": False,
    }
    static = {**static_base, "clearance_sha256": sha256_bytes(canonical(static_base))}
    prior_replacements = replay["replacements"]
    attempts: list[dict[str, Any]] = []
    launches = 0
    redactor = redactor or Redactor()
    while len(attempts) < 3:
        launches += 1
        attempt = _live_launch(
            root, candidate, binding["id"], launches, live_root, freeze=freeze,
            static_fidelity=static, process_runner=process_runner, redactor=redactor,
        )
        if attempt["infrastructure_failure"]:
            prior_replacements += 1
            if prior_replacements > authorization["replacement_launch_cap"]:
                raise ScoutError("rolling replacement launch cap exceeded")
        elif not attempt["usable"]:
            raise ScoutError("unscoreable rolling launch cannot be replaced")
        else:
            attempts.append(attempt)
    pending = verify_rolling_evidence(evidence, authorization, root)["pending"]
    if pending is None or len(pending["attempts"]) != 3:
        raise ScoutError("rolling exposure evidence is incomplete")
    return {"status": "AWAITING_DISPOSITION", "candidate": binding["id"], "launches": launches}
def _authorization_from_evidence(path: Path, evidence: Path) -> tuple[Path, dict[str, Any]]:
    root = _repository_root(path)
    _reject_symlink_chain(path.absolute(), root)
    _reject_symlink_chain(evidence.absolute(), root)
    path, evidence = path.resolve(), evidence.resolve()
    directories = sorted(item for item in evidence.glob("candidate-*") if item.is_dir())
    if not directories:
        raise ScoutError("rolling evidence has no candidate header")
    header, raw = _canonical_json_file(directories[0] / "header.json", "rolling header"), _canonical_json_file(path, "rolling authorization")
    context = {"campaign_id": raw.get("campaign_id"), "start_commit": raw.get("start_commit"), "task_root": raw.get("task_root"), **header["execution"]}
    return root, _rolling_authorization(path, context, root, evidence)
def finalize_rolling_candidate(
    authorization_path: Path | str, output: Path | str, disposition_path: Path | str
) -> dict[str, Any]:
    """Consume the gatekeeper's post-exposure disposition, then transition."""
    authorization_path, evidence = Path(authorization_path), Path(output)
    root, authorization = _authorization_from_evidence(authorization_path, evidence)
    replay = verify_rolling_evidence(evidence, authorization, root)
    pending = replay["pending"]
    if pending is None or len(pending["attempts"]) != 3:
        raise ScoutError("one complete pending candidate is required")
    directory, header = pending["directory"], pending["header"]
    launches = [_canonical_json_file(path, "rolling raw launch") for path in sorted(directory.glob("launch-*.json"))]
    disposition = _rolling_disposition(Path(disposition_path).resolve(), header, launches, directory)
    _write_json_once(directory / "disposition.json", disposition)
    report = classify_rolling_task(header["binding"], pending["attempts"])
    if not disposition["semantic_fidelity_passed"]:
        report.update({"label": "invalid", "fidelity_defect": True,
                       "fidelity_root_causes": sorted(set(report["fidelity_root_causes"] + [disposition["root_cause"]])),
                       "shared_recipe_or_admission_defect": disposition["shared_recipe_or_admission_defect"]})
    state = advance_rolling_campaign(replay["state"], header["binding"], report)
    _write_json_once(directory / "result.json", {
        "schema": ROLLING_RECORD_SCHEMA, "ordinal": header["ordinal"], "inventory": pending["inventory"],
        "report": report, "state_after": state, "disposition_sha256": sha256_file(directory / "disposition.json"),
    })
    if state["status"] in {"ROLLING_PASS", "ROLLING_NO_PASS"}:
        _write_json_once(evidence / "summary.json", {"schema": ROLLING_SUMMARY_SCHEMA, "manifest_sha256": sha256_file(evidence / "manifest.json"), "state": state})
    return verify_rolling_evidence(evidence, authorization, root)["state"]

def verify_live_rolling(authorization_path: Path | str, output: Path | str) -> dict[str, Any]:
    authorization_path, evidence = Path(authorization_path), Path(output)
    root, authorization = _authorization_from_evidence(authorization_path, evidence)
    replay = verify_rolling_evidence(evidence, authorization, root)
    pending = replay["pending"]
    return {"state": replay["state"], "replacements": replay["replacements"], "pending_task_id": pending["header"]["binding"]["id"] if pending else None}
