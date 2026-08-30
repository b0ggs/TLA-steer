"""Thin role-aware adapter over the preserved MDs_EVAL Codex worker.

This module intentionally implements only the hackathon's local fallback.  It
uses Codex's workspace sandbox and the foundation's capability shutdown,
process cleanup, redaction, and JSONL audit, but it is *not* the sealed
MDs_EVAL container boundary.  Every result records that fact as
``prototype_local``.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import stat
import tempfile
import time
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any, Callable, Mapping, Protocol

from mdseval.capture import Redactor, audit_event_evidence, redact_event_stream
from mdseval.config import RunnerConfig
from mdseval.gitutils import init_repository
from mdseval.processutils import ProcessOutcome, run_process_group
from mdseval.runner.codex_cli import build_codex_command, isolated_environment


PROTOTYPE_LOCAL = "prototype_local"
PROTOTYPE_LOCAL_WARNING = (
    "Host-local Codex workspace sandbox; this does not reproduce the sealed "
    "MDs_EVAL anti-cheating boundary."
)
USAGE_FIELDS = (
    "input_tokens",
    "cached_input_tokens",
    "cache_write_input_tokens",
    "output_tokens",
    "reasoning_output_tokens",
)
_SAFE_ID = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]{0,127}\Z")
_RESERVED_SPOOL_PATHS = frozenset(
    {"intent.json", "events.jsonl", "stderr.txt", "final.txt", "result.json"}
)
_OUTPUT_SCHEMA_PATH = ".tla-steer-output-schema.json"
_MAX_ARTIFACT_BYTES = 2 * 1024 * 1024
_CODE_MODE_DISABLED_WARNING = (
    "Code Mode is unavailable because code-mode host is disabled. Code mode "
    "will fail closed; enable `features.code_mode_host` and install "
    "`codex-code-mode-host`."
)


@dataclass(frozen=True)
class RolePolicy:
    role: str
    model: str
    reasoning_effort: str


ROLE_POLICIES: Mapping[str, RolePolicy] = {
    "direct": RolePolicy("direct", "gpt-5.6-sol", "xhigh"),
    "planner": RolePolicy("planner", "gpt-5.6-sol", "xhigh"),
    "follower": RolePolicy("follower", "gpt-5.6-luna", "low"),
}


def _safe_relative_path(value: str, label: str) -> str:
    if not isinstance(value, str) or not value or "\\" in value or "\x00" in value:
        raise ValueError(f"{label} must be a nonempty POSIX relative path")
    path = PurePosixPath(value)
    if (
        path.is_absolute()
        or path.as_posix() != value
        or any(part in {"", ".", ".."} for part in path.parts)
        or path.parts[0] == ".git"
    ):
        raise ValueError(f"{label} must stay within the fresh workspace")
    return value


def _canonical_schema(value: Mapping[str, Any]) -> bytes:
    if not isinstance(value, Mapping):
        raise ValueError("output_schema must be a JSON object")
    try:
        return json.dumps(
            dict(value),
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        ).encode("utf-8")
    except (TypeError, ValueError, RecursionError) as exc:
        raise ValueError("output_schema must be a finite JSON object") from exc


@dataclass(frozen=True)
class WorkerRequest:
    """One fresh, stateless Codex turn and its isolated evidence spool."""

    call_id: str
    role: str
    prompt: str
    input_files: Mapping[str, str | bytes]
    artifact_path: str | None
    spool_dir: Path
    codex_home: Path
    timeout_seconds: int = 300
    containment_mode: str = PROTOTYPE_LOCAL
    output_schema: Mapping[str, Any] | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.call_id, str) or _SAFE_ID.fullmatch(self.call_id) is None:
            raise ValueError("call_id must be a safe nonempty identifier")
        if self.role not in ROLE_POLICIES:
            raise ValueError(f"unsupported worker role: {self.role!r}")
        if not isinstance(self.prompt, str) or not self.prompt.strip():
            raise ValueError("prompt must be nonempty")
        if not isinstance(self.input_files, Mapping):
            raise ValueError("input_files must be a path-to-content mapping")
        for path, content in self.input_files.items():
            _safe_relative_path(path, "input file path")
            if not isinstance(content, (str, bytes)):
                raise ValueError(f"input file {path!r} must contain str or bytes")
        if self.artifact_path is not None:
            artifact = _safe_relative_path(self.artifact_path, "artifact_path")
            if artifact in _RESERVED_SPOOL_PATHS:
                raise ValueError("artifact_path collides with worker evidence")
        if not isinstance(self.spool_dir, Path) or not isinstance(self.codex_home, Path):
            raise ValueError("spool_dir and codex_home must be pathlib.Path values")
        if (
            not isinstance(self.timeout_seconds, int)
            or isinstance(self.timeout_seconds, bool)
            or self.timeout_seconds <= 0
        ):
            raise ValueError("timeout_seconds must be a positive integer")
        if self.containment_mode != PROTOTYPE_LOCAL:
            raise ValueError(
                "this adapter supports only honestly labeled prototype_local containment"
            )
        if self.output_schema is not None:
            _canonical_schema(self.output_schema)


@dataclass(frozen=True)
class WorkerResult:
    call_id: str
    role: str
    requested_model: str
    returned_model: str | None
    reasoning_effort: str
    containment_mode: str
    containment_warning: str
    status: str
    exit_code: int | None
    duration_seconds: float
    queue_duration_seconds: float
    timed_out: bool
    interrupted: bool
    usage: dict[str, int | bool]
    error: str | None
    artifact_path: str | None
    artifact_sha256: str | None
    artifact_size_bytes: int | None
    event_fatal_defects: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "call_id": self.call_id,
            "role": self.role,
            "requested_model": self.requested_model,
            "returned_model": self.returned_model,
            "reasoning_effort": self.reasoning_effort,
            "containment_mode": self.containment_mode,
            "containment_warning": self.containment_warning,
            "status": self.status,
            "exit_code": self.exit_code,
            "duration_seconds": self.duration_seconds,
            "queue_duration_seconds": self.queue_duration_seconds,
            "timed_out": self.timed_out,
            "interrupted": self.interrupted,
            "usage": dict(self.usage),
            "error": self.error,
            "artifact_path": self.artifact_path,
            "artifact_sha256": self.artifact_sha256,
            "artifact_size_bytes": self.artifact_size_bytes,
            "event_fatal_defects": list(self.event_fatal_defects),
        }


class ProcessRunner(Protocol):
    def __call__(
        self,
        command: list[str],
        *,
        cwd: Path,
        input_text: str | None,
        timeout: int,
        environment: dict[str, str],
    ) -> ProcessOutcome: ...


def _write_once(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("xb") as stream:
        stream.write(data)


def _json_bytes(value: Any) -> bytes:
    return (
        json.dumps(
            value,
            sort_keys=True,
            indent=2,
            ensure_ascii=False,
            allow_nan=False,
        )
        + "\n"
    ).encode("utf-8")


def _sha256(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _write_inputs(workspace: Path, files: Mapping[str, str | bytes]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for relative in sorted(files):
        data = files[relative]
        raw = data.encode("utf-8") if isinstance(data, str) else data
        target = workspace.joinpath(*PurePosixPath(relative).parts)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(raw)
        rows.append({"path": relative, "sha256": _sha256(raw), "size_bytes": len(raw)})
    return rows


def _runner_config(policy: RolePolicy, timeout_seconds: int) -> RunnerConfig:
    return RunnerConfig(
        type="codex-cli",
        model=policy.model,
        reasoning_effort=policy.reasoning_effort,
        sandbox="workspace-write",
        approval_policy="never",
        subagents_enabled=False,
        ephemeral=True,
        network_for_agent_commands=False,
        timeout_seconds=timeout_seconds,
        max_parallel_runs=1,
    )


def _event_metadata(path: Path) -> tuple[str | None, bool]:
    """Read only narrow, documented metadata from already-redacted JSONL."""

    returned_model: str | None = None
    turn_failed = False
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except (OSError, UnicodeError):
        return None, False
    for line in lines:
        try:
            event = json.loads(line)
        except (json.JSONDecodeError, ValueError):
            continue
        if not isinstance(event, dict):
            continue
        if event.get("type") == "turn.failed":
            turn_failed = True
        candidate = event.get("model")
        if not isinstance(candidate, str):
            response = event.get("response")
            candidate = response.get("model") if isinstance(response, dict) else None
        if isinstance(candidate, str) and candidate.strip():
            returned_model = candidate
    return returned_model, turn_failed


def _compatible_event_defects(
    path: Path, fatal_defects: tuple[str, ...]
) -> tuple[str, ...]:
    """Ignore only Codex 0.151's exact fail-closed Code Mode warning.

    The event remains in the persisted JSONL. Generic ``error`` items, an
    altered warning, extra fields, or the warning at any other lifecycle point
    remain fatal under the foundation audit.
    """

    target_defect = 'line:2:unknown_item_type:"error"'
    if target_defect not in fatal_defects:
        return fatal_defects
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
        event = json.loads(lines[1])
    except (OSError, UnicodeError, IndexError, json.JSONDecodeError, ValueError):
        return fatal_defects
    expected = {
        "type": "item.completed",
        "item": {
            "id": "item_0",
            "type": "error",
            "message": _CODE_MODE_DISABLED_WARNING,
        },
    }
    if event != expected:
        return fatal_defects
    return tuple(defect for defect in fatal_defects if defect != target_defect)


def _capture_artifact(
    workspace: Path, spool_dir: Path, relative: str | None
) -> tuple[str | None, str | None, int | None, str | None]:
    if relative is None:
        return None, None, None, None
    source = workspace.joinpath(*PurePosixPath(relative).parts)
    try:
        info = source.lstat()
    except FileNotFoundError:
        return None, None, None, f"expected artifact was not created: {relative}"
    if stat.S_ISLNK(info.st_mode) or not stat.S_ISREG(info.st_mode):
        return None, None, None, f"artifact is not a regular non-symlink file: {relative}"
    if info.st_size > _MAX_ARTIFACT_BYTES:
        return None, None, None, f"artifact exceeds {_MAX_ARTIFACT_BYTES} bytes: {relative}"
    data = source.read_bytes()
    destination = spool_dir.joinpath(*PurePosixPath(relative).parts)
    _write_once(destination, data)
    return relative, _sha256(data), len(data), None


def _empty_usage() -> dict[str, int | bool]:
    return {**{field: 0 for field in USAGE_FIELDS}, "usage_reported": False}


def run_worker(
    request: WorkerRequest,
    *,
    process_runner: ProcessRunner = run_process_group,
    monotonic: Callable[[], float] = time.monotonic,
    redactor: Redactor | None = None,
) -> WorkerResult:
    """Run one role turn in a fresh workspace and persist its complete spool.

    Model/process failures are returned as data so the direct arm can report a
    failed attempt and SMC can assign a zero weight without losing evidence.
    Pre-launch request or spool collisions remain caller errors.
    """

    policy = ROLE_POLICIES[request.role]
    redactor = redactor or Redactor()
    request.spool_dir.mkdir(parents=True, exist_ok=False)

    with tempfile.TemporaryDirectory(prefix=f"tla-steer-{request.role}-") as temporary:
        root = Path(temporary)
        workspace = root / "workspace"
        workspace.mkdir()
        inputs = _write_inputs(workspace, request.input_files)
        schema_bytes: bytes | None = None
        if request.output_schema is not None:
            schema_bytes = _canonical_schema(request.output_schema)
            (workspace / _OUTPUT_SCHEMA_PATH).write_bytes(schema_bytes)
        init_repository(workspace)

        raw_final = root / "final.txt"
        command = build_codex_command(
            _runner_config(policy, request.timeout_seconds), workspace, raw_final
        )
        if schema_bytes is not None:
            schema_path = workspace / _OUTPUT_SCHEMA_PATH
            command[-1:-1] = ["--output-schema", str(schema_path)]

        intent = {
            "schema_version": "tla-steer-worker-intent/0.1",
            "call_id": request.call_id,
            "role": request.role,
            "requested_model": policy.model,
            "reasoning_effort": policy.reasoning_effort,
            "containment_mode": request.containment_mode,
            "containment_warning": PROTOTYPE_LOCAL_WARNING,
            "timeout_seconds": request.timeout_seconds,
            "prompt": redactor.text(request.prompt),
            "prompt_sha256": _sha256(request.prompt.encode("utf-8")),
            "input_files": inputs,
            "artifact_path": request.artifact_path,
            "output_schema": (
                None
                if schema_bytes is None
                else {
                    "path": _OUTPUT_SCHEMA_PATH,
                    "sha256": _sha256(schema_bytes),
                    "value": request.output_schema,
                }
            ),
        }
        _write_once(request.spool_dir / "intent.json", _json_bytes(intent))

        started = monotonic()
        spawn_error: str | None = None
        try:
            outcome = process_runner(
                command,
                cwd=workspace,
                input_text=request.prompt,
                timeout=request.timeout_seconds,
                environment=isolated_environment(str(request.codex_home)),
            )
        except Exception as exc:  # Preserve one failed call rather than losing its spool.
            spawn_error = redactor.text(f"{type(exc).__name__}: {exc}")
            outcome = ProcessOutcome(None, "", spawn_error, False, False)
        duration = max(0.0, monotonic() - started)

        safe_events = redact_event_stream(outcome.stdout, redactor)
        safe_stderr = redactor.text(outcome.stderr)
        safe_final = redactor.text(
            raw_final.read_text(encoding="utf-8", errors="replace")
            if raw_final.is_file()
            else ""
        )
        events_path = request.spool_dir / "events.jsonl"
        _write_once(events_path, safe_events.encode("utf-8"))
        _write_once(request.spool_dir / "stderr.txt", safe_stderr.encode("utf-8"))
        _write_once(request.spool_dir / "final.txt", safe_final.encode("utf-8"))

        audit = audit_event_evidence(events_path)
        event_fatal_defects = _compatible_event_defects(
            events_path, audit.fatal_defects
        )
        usage: dict[str, int | bool] = {
            field: int(audit.usage[field]) for field in USAGE_FIELDS
        }
        usage["usage_reported"] = bool(audit.usage["usage_reported"])
        returned_model, turn_failed = _event_metadata(events_path)

        artifact_path, artifact_sha, artifact_size, artifact_error = _capture_artifact(
            workspace, request.spool_dir, request.artifact_path
        )
        error: str | None
        if spawn_error is not None:
            status, error = "SPAWN_ERROR", spawn_error
        elif outcome.timed_out:
            status, error = "TIMEOUT", "worker process timed out"
        elif outcome.interrupted:
            status, error = "INTERRUPTED", "worker process was interrupted"
        elif outcome.returncode != 0:
            status, error = "FAILED", f"worker process exited with status {outcome.returncode}"
        elif turn_failed:
            status, error = "FAILED", "Codex JSONL reported turn.failed"
        elif event_fatal_defects:
            status = "INVALID_EVIDENCE"
            error = "fatal JSONL evidence defects: " + "; ".join(
                event_fatal_defects
            )
        elif artifact_error is not None:
            status, error = "INVALID_ARTIFACT", artifact_error
        else:
            status, error = "COMPLETED", None

        result = WorkerResult(
            call_id=request.call_id,
            role=request.role,
            requested_model=policy.model,
            returned_model=returned_model,
            reasoning_effort=policy.reasoning_effort,
            containment_mode=request.containment_mode,
            containment_warning=PROTOTYPE_LOCAL_WARNING,
            status=status,
            exit_code=outcome.returncode,
            duration_seconds=duration,
            queue_duration_seconds=0.0,
            timed_out=outcome.timed_out,
            interrupted=outcome.interrupted,
            usage=usage,
            error=error,
            artifact_path=artifact_path,
            artifact_sha256=artifact_sha,
            artifact_size_bytes=artifact_size,
            event_fatal_defects=event_fatal_defects,
        )
        _write_once(request.spool_dir / "result.json", _json_bytes(result.to_dict()))
        return result
