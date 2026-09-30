"""One-run coordinator for the fixed TwoLights hackathon comparison.

This is intentionally glue, not a generalized experiment framework.  Every
hosted turn goes through the role-aware fresh-workspace worker; generated code
is executed only in trusted subprocess adapters; and the weighted SMC artifact
is selected and frozen before the independent verifier sees it.
"""

from __future__ import annotations

import hashlib
import itertools
import json
import math
import os
import shutil
import subprocess
import sys
import tempfile
import threading
import time
import uuid
from dataclasses import asdict, is_dataclass
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
from typing import Any, Mapping

from .contract import (
    ContractError,
    Controller,
    ControllerStep,
    Proposal,
    controller_from_json,
    initial_state_from_fragment,
    proposal_from_json,
    validate_guard_update_source,
)
from . import execution
from .evidence import sha256_file, write_json, write_run_report
from .oracle import ACTION_SYMBOLS, CONSTANTS
from .smc import (
    ActionObservation,
    IncrementalScore,
    FatalScoringError,
    Particle,
    SMCConfig,
    score_action_observations,
    score_initial_state,
    run_smc,
)
from .verifier import INVALID_CANDIDATE, verify_candidate
from .worker import PROTOTYPE_LOCAL, ROLE_POLICIES, WorkerRequest, WorkerResult, ReviewedFixtureWorker, run_worker


SCHEMA_VERSION = "tla-steer-run/0.1"
WORKER_TIMEOUT_SECONDS = 300
PROBE_TIMEOUT_SECONDS = 5
SOURCE_HASHES = {
    "TwoLights.tla": "7717242a40bcd6ed57380ca7a4f2e1e756d5432470c3162a3a31e15309f4b4aa",
    "TwoLights.cfg": "ae94c273187b35d55831f4b272c0b229437e82758c2be7f9a0921830b288ce40",
}


class PipelineError(RuntimeError):
    """The fixed comparison could not proceed; partial evidence is preserved."""


_PROBE_RUNNER = r'''
import json
import sys


def emit(value):
    sys.stdout.write(json.dumps(value, sort_keys=True, separators=(",", ":")))


def same_state(actual, expected):
    return type(actual) is dict and set(actual) == set(expected) and all(
        type(actual[key]) is type(value) and actual[key] == value for key, value in expected.items()
    )


request = json.loads(sys.stdin.read())
safe_builtins = {
    "abs": abs,
    "all": all,
    "any": any,
    "bool": bool,
    "dict": dict,
    "enumerate": enumerate,
    "float": float,
    "frozenset": frozenset,
    "int": int,
    "isinstance": isinstance,
    "len": len,
    "list": list,
    "max": max,
    "min": min,
    "object": object,
    "range": range,
    "set": set,
    "str": str,
    "sum": sum,
    "tuple": tuple,
    "type": type,
    "zip": zip,
    "Exception": Exception,
    "RuntimeError": RuntimeError,
    "TypeError": TypeError,
    "ValueError": ValueError,
}
namespace = {"__builtins__": safe_builtins, "__name__": "candidate"}
try:
    with open(sys.argv[1], encoding="utf-8") as handle:
        source = handle.read()
    exec(compile(source, "partial-candidate.py", "exec"), namespace, namespace)
    function = namespace[request["symbol"]]
    rows = []
    for state in request["states"]:
        first_input = dict(state)
        second_input = dict(state)
        first = function(first_input)
        first_mutated = not same_state(first_input, state)
        first = dict(first) if type(first) is dict else first
        second = function(second_input)
        second = dict(second) if type(second) is dict else second
        rows.append(
            {
                "first": first,
                "second": second,
                "input_mutated": first_mutated or not same_state(first_input, state) or not same_state(second_input, state),
                "deterministic": first == second,
            }
        )
except BaseException as exc:
    emit({"ok": False, "error": type(exc).__name__ + ": " + str(exc)[:500]})
else:
    emit({"ok": True, "rows": rows})
'''


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _write_once(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("xb") as stream:
        stream.write(data)


def _write_json_once(path: Path, value: Any) -> None:
    _write_once(
        path,
        (
            json.dumps(
                _json_safe(value),
                indent=2,
                sort_keys=True,
                ensure_ascii=False,
                allow_nan=False,
            )
            + "\n"
        ).encode("utf-8"),
    )


def _write_jsonl_once(path: Path, values: list[dict[str, Any]]) -> None:
    text = "".join(
        json.dumps(
            _json_safe(value),
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        )
        + "\n"
        for value in values
    )
    _write_once(path, text.encode("utf-8"))


def _json_safe(value: Any) -> Any:
    if is_dataclass(value) and not isinstance(value, type):
        return _json_safe(asdict(value))
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, Mapping):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, (tuple, list)):
        return [_json_safe(item) for item in value]
    if isinstance(value, float) and not math.isfinite(value):
        if math.isnan(value):
            return "nan"
        return "inf" if value > 0 else "-inf"
    return value


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _prompt_with_inputs(base_prompt: str, files: Mapping[str, str]) -> str:
    """Place approved inputs in-band for the capability-disabled model turn."""

    sections = [
        base_prompt.rstrip(),
        "",
        (
            "The fresh model turn cannot open workspace files. Treat the exact "
            "approved input contents below as the named files."
        ),
    ]
    for name, contents in files.items():
        sections.extend(
            [
                "",
                f"<BEGIN APPROVED FILE {name}>",
                contents.rstrip(),
                f"<END APPROVED FILE {name}>",
            ]
        )
    return "\n".join(sections) + "\n"


def _relative_file(root: Path, raw: object, label: str) -> Path:
    if not isinstance(raw, str) or not raw:
        raise PipelineError(f"config path {label} must be a nonempty string")
    relative = PurePosixPath(raw)
    if relative.is_absolute() or any(part in {"", ".", ".."} for part in relative.parts):
        raise PipelineError(f"config path {label} must be repository-relative")
    path = root.joinpath(*relative.parts).resolve()
    try:
        path.relative_to(root.resolve())
    except ValueError as exc:
        raise PipelineError(f"config path {label} escapes the repository") from exc
    if not path.is_file() or path.is_symlink():
        raise PipelineError(f"configured file is missing or a symlink: {raw}")
    return path


def _run_root(root: Path, raw: object) -> Path:
    if not isinstance(raw, str) or not raw:
        raise PipelineError("paths.runs_root must be a repository-relative path")
    relative = PurePosixPath(raw)
    if relative.is_absolute() or any(part in {"", ".", ".."} for part in relative.parts):
        raise PipelineError("paths.runs_root must be a repository-relative path")
    path = root.joinpath(*relative.parts).resolve()
    try:
        path.relative_to(root.resolve())
    except ValueError as exc:
        raise PipelineError("paths.runs_root escapes the repository") from exc
    return path


def _object(value: object, label: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise PipelineError(f"{label} must be an object")
    return value


def _validate_fixed_configuration(
    config: Mapping[str, Any], *, particle_count: int, max_concurrency: int, smoke: bool
) -> None:
    models = _object(config.get("models"), "models")
    for role, policy in ROLE_POLICIES.items():
        selected = _object(models.get(role), f"models.{role}")
        if (
            selected.get("model") != policy.model
            or selected.get("reasoning_effort") != policy.reasoning_effort
            or selected.get("internal_subagents") is not False
        ):
            raise PipelineError(f"models.{role} differs from the frozen role policy")
    smc = _object(config.get("smc"), "smc")
    expected = (2, 2) if smoke else (8, 4)
    if (particle_count, max_concurrency) != expected:
        raise PipelineError(
            f"{'smoke' if smoke else 'comparison'} requires N={expected[0]}, C={expected[1]}"
        )
    if (
        smc.get("logical_particles") != 8
        or smc.get("max_active_follower_calls") != 4
        or smc.get("semantic_steps") != 8
        or smc.get("resampling") != "multinomial"
        or smc.get("seed") != 20260830
    ):
        raise PipelineError("SMC config differs from the frozen prototype")
    if config.get("containment_mode") != PROTOTYPE_LOCAL:
        raise PipelineError("this pipeline supports only honestly labeled prototype_local")


def _codex_home() -> tuple[Path, str]:
    for variable in ("TLA_STEER_CODEX_HOME", "MDSEVAL_CODEX_HOME"):
        value = os.environ.get(variable)
        if value:
            path = Path(value).expanduser().resolve()
            if not path.is_dir():
                raise PipelineError(f"{variable} does not name a directory: {path}")
            return path, variable
    raise PipelineError(
        "set TLA_STEER_CODEX_HOME or MDSEVAL_CODEX_HOME to the dedicated Codex OAuth profile"
    )


def _call_issue(result: WorkerResult) -> str | None:
    if result.status != "COMPLETED":
        return f"{result.role} call {result.call_id}: {result.status}: {result.error}"
    if result.returned_model is not None and result.returned_model != result.requested_model:
        return (
            f"{result.role} call {result.call_id}: returned model "
            f"{result.returned_model!r}, requested {result.requested_model!r}"
        )
    return None


def _failed_verification(reason: str) -> dict[str, Any]:
    return {
        "schema_version": "tla-steer-verification/0.1",
        "outcome": INVALID_CANDIDATE,
        "exact": False,
        "verification_not_run": True,
        "contract_failures": [reason],
        "verifier_duration_seconds": 0.0,
        "containment_mode": PROTOTYPE_LOCAL,
    }


def _constant_source() -> str:
    return "\n".join(f"{name} = {value!r}" for name, value in CONSTANTS.items()) + "\n"


def _partial_source(particle: Particle) -> str:
    return _constant_source() + ("\n" + particle.partial_artifact if particle.fragments else "")


def _candidate_source(particle: Particle) -> str:
    actions = ["ACTIONS = {"]
    actions.extend(
        f"    {label!r}: {symbol}," for label, symbol in ACTION_SYMBOLS.items()
    )
    actions.append("}")
    source = _partial_source(particle).rstrip() + "\n\n" + "\n".join(actions) + "\n"
    compile(source, "candidate.py", "exec")
    return source


def _score_action(particle: Particle, step: ControllerStep) -> IncrementalScore:
    source = _partial_source(particle)
    try:
        validate_guard_update_source(source, complete=False)
    except ContractError as exc:
        return IncrementalScore(0.0, error=f"guard_update_contract: {exc}")
    request = {"symbol": step.python_symbol, "states": [probe.state.as_dict() for probe in step.probes]}
    try:
        process = execution.run_observations(source, _PROBE_RUNNER, request, timeout_seconds=PROBE_TIMEOUT_SECONDS)
    except execution.ContainmentUnavailable as exc:
        raise FatalScoringError(f"candidate containment unavailable: {exc}") from exc
    if process.timed_out:
        return IncrementalScore(0.0, error="incremental probe timeout")
    if process.output_exceeded:
        return IncrementalScore(0.0, error="incremental probe output limit")
    if process.returncode != 0:
        return IncrementalScore(
            0.0,
            error=f"probe process exit {process.returncode}: {process.stderr.strip()[:300]}",
        )
    try:
        payload = json.loads(process.stdout)
    except json.JSONDecodeError as exc:
        return IncrementalScore(0.0, error=f"invalid probe response: {exc}")
    if not isinstance(payload, dict) or payload.get("ok") is not True:
        error = payload.get("error") if isinstance(payload, dict) else "non-object response"
        return IncrementalScore(0.0, error=f"proposal execution failed: {error}")
    rows = payload.get("rows")
    if not isinstance(rows, list) or len(rows) != len(step.probes):
        return IncrementalScore(0.0, error="probe response has wrong row count")
    observations: list[ActionObservation] = []
    for probe, row in zip(step.probes, rows):
        if not isinstance(row, dict):
            return IncrementalScore(0.0, error="probe response row is not an object")
        observations.append(
            ActionObservation(
                expected_successor=probe.expected_successor,
                actual_successor=row.get("first"),
                input_mutated=bool(row.get("input_mutated")),
                deterministic=bool(row.get("deterministic")),
            )
        )
    return score_action_observations(observations)


def _incremental_score(
    particle: Particle, step: ControllerStep, proposal: Proposal
) -> IncrementalScore:
    if step.kind == "initial":
        assert step.expected_initial is not None
        return score_initial_state(
            initial_state_from_fragment(proposal, step), step.expected_initial
        )
    return _score_action(particle, step)


def _context(
    spool: Path,
    *,
    arm: str,
    result: WorkerResult,
    particle: Particle | None = None,
    step: ControllerStep | None = None,
    attempt: int = 1,
) -> None:
    _write_json_once(
        spool / "context.json",
        {
            "schema_version": "tla-steer-call-context/0.1",
            "arm": arm,
            "role": result.role,
            "call_id": result.call_id,
            "attempt": attempt,
            "particle_id": None if particle is None else particle.particle_id,
            "parent_id": None if particle is None else particle.parent_id,
            "step_id": None if step is None else step.id,
            "step_target": None if step is None else step.target,
            "requested_model": result.requested_model,
            "returned_model": result.returned_model,
            "model_conforming": result.returned_model
            in (None, result.requested_model),
        },
    )


def _planner(
    *,
    run_dir: Path,
    codex_home: Path,
    base_prompt: str,
    common_inputs: dict[str, str],
    invoke: Any,
) -> tuple[Controller | None, int, str | None]:
    invalid_document: str | None = None
    validation_error: str | None = None
    for attempt in (1, 2):
        call_id = "planner-01" if attempt == 1 else "planner-02-schema-repair"
        spool = run_dir / "discipl" / "planner" / "calls" / call_id
        prompt = _prompt_with_inputs(base_prompt, common_inputs)
        inputs = dict(common_inputs)
        if attempt == 2:
            assert invalid_document is not None and validation_error is not None
            prompt = (
                prompt
                + "\nYour first controller failed host validation. Return one "
                "complete replacement controller using the exact failed document "
                "and host error below. Do not discuss the error or add any other "
                "fields. Before returning, re-audit all eight unique targets and "
                "every action's two distinct probes: first enabled with a non-null "
                "exact successor, second disabled with a null successor.\n\n"
                "<BEGIN FAILED CONTROLLER>\n"
                + invalid_document.rstrip()
                + "\n<END FAILED CONTROLLER>\n\n<BEGIN HOST VALIDATION ERROR>\n"
                + validation_error
                + "\n<END HOST VALIDATION ERROR>\n"
            )
            inputs["invalid-controller.json"] = invalid_document
            inputs["validation-error.txt"] = validation_error
        result = invoke(
            WorkerRequest(
                call_id=call_id,
                role="planner",
                prompt=prompt,
                input_files=inputs,
                artifact_path=None,
                spool_dir=spool,
                codex_home=codex_home,
                timeout_seconds=WORKER_TIMEOUT_SECONDS,
            )
        )
        _context(spool, arm="discipl", result=result, attempt=attempt)
        issue = _call_issue(result)
        if issue is not None:
            return None, attempt - 1, issue
        document = (spool / "final.txt").read_text(encoding="utf-8")
        try:
            return controller_from_json(document), attempt - 1, None
        except ContractError as exc:
            invalid_document = document
            validation_error = str(exc)
            if attempt == 2:
                return None, 1, f"Planner controller remained invalid: {exc}"
    raise AssertionError("unreachable Planner attempt loop")


def run_comparison(
    config: Mapping[str, Any],
    config_path: Path,
    repository_root: Path,
    particle_count: int,
    max_concurrency: int,
    smoke: bool,
    offline_screen: bool = False,
) -> Path:
    """Run the frozen comparison, optionally with the fixture-only cheap control.

    Model failures and semantic mismatches are experiment results.  Harness
    failures raise ``PipelineError`` after the partial run manifest and report
    have been updated.
    """

    root = repository_root.resolve()
    config_path = config_path.resolve()
    _validate_fixed_configuration(
        config,
        particle_count=particle_count,
        max_concurrency=max_concurrency,
        smoke=smoke,
    )
    paths = _object(config.get("paths"), "paths")
    input_config = _object(config.get("input"), "input")
    tla_path = _relative_file(root, input_config.get("tla_path"), "input.tla_path")
    cfg_path = _relative_file(root, input_config.get("cfg_path"), "input.cfg_path")
    source_bytes = {"TwoLights.tla": tla_path.read_bytes(), "TwoLights.cfg": cfg_path.read_bytes()}
    if input_config.get("sha256") != SOURCE_HASHES:
        raise PipelineError("configured TwoLights hashes differ from the approved source pins")
    for name, data in source_bytes.items():
        if _sha256_bytes(data) != SOURCE_HASHES[name]:
            raise PipelineError(f"TwoLights source hash mismatch: {name}; no worker launched")
    if offline_screen and (not smoke or (particle_count, max_concurrency) != (2, 2)):
        raise PipelineError("offline screen requires N=2, C=2")
    fixture = ReviewedFixtureWorker(root) if offline_screen else None
    if fixture is None:
        # No provider spend before a real isolated launch succeeds.
        execution.preflight()
        codex_home, codex_home_variable = _codex_home()
    else:
        codex_home_variable = "offline_empty_profile_no_credentials"
    rate_card_path = _relative_file(root, paths.get("rate_card"), "paths.rate_card")
    controller_schema_path = _relative_file(
        root, paths.get("controller_schema"), "paths.controller_schema"
    )
    proposal_schema_path = _relative_file(
        root, paths.get("proposal_schema"), "paths.proposal_schema"
    )
    prompt_paths = {
        role: _relative_file(root, paths.get(f"{role}_prompt"), f"paths.{role}_prompt")
        for role in ("direct", "planner", "follower")
    }
    controller_schema = json.loads(controller_schema_path.read_text(encoding="utf-8"))
    proposal_schema = json.loads(proposal_schema_path.read_text(encoding="utf-8"))
    if not isinstance(controller_schema, dict) or not isinstance(proposal_schema, dict):
        raise PipelineError("controller and proposal schemas must be JSON objects")

    runs_root = _run_root(root, "runs/offline-cost-screen-r2" if offline_screen else paths.get("runs_root"))
    runs_root.mkdir(parents=True, exist_ok=True)
    run_id = (
        datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        + "-"
        + uuid.uuid4().hex[:8]
        + ("-smoke" if smoke else "")
    )
    run_dir = runs_root / run_id
    run_dir.mkdir(exist_ok=False)
    if offline_screen:
        codex_home = run_dir / ".offline-profile"
        codex_home.mkdir()
    started = time.monotonic()
    start_timestamp = _utc_now()
    shutil.copyfile(rate_card_path, run_dir / "rate-card.json")

    seed = int(_object(config.get("smc"), "smc")["seed"])
    manifest: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "run_id": run_id,
        "experiment_id": config.get("experiment_id", "twolights-prototype"),
        "status": "running",
        "start_timestamp": start_timestamp,
        "containment_mode": PROTOTYPE_LOCAL,
        "containment_warning": (
            "Host-local Codex workspace sandbox; not the sealed MDs_EVAL anti-cheating boundary."
        ),
        "codex_home_source": codex_home_variable,
        "smoke": smoke,
        "offline_fixture": offline_screen,
        "measurement_note": (
            "Reviewed local fixtures and synthetic token counters only. No provider calls, "
            "live model performance, actual charges, or research savings are measured."
            if offline_screen else None
        ),
        "arms": ["direct", "cheap_alone", "discipl"] if offline_screen else ["direct", "discipl"],
        "attempted_calls_by_role": {role: 0 for role in ROLE_POLICIES
                                    if offline_screen or role != "cheap_alone"},
        "configuration": {
            "logical_particles": particle_count,
            "max_active_follower_calls": max_concurrency,
            "semantic_steps": 8,
            "ess_threshold": particle_count / 2.0,
            "resampling": "multinomial",
            "seed": seed,
            "models": config["models"],
        },
        "inputs": {
            "config": {"path": str(config_path.relative_to(root)), "sha256": sha256_file(config_path)},
            "tla": {"path": str(tla_path.relative_to(root)), "sha256": _sha256_bytes(source_bytes["TwoLights.tla"])},
            "cfg": {"path": str(cfg_path.relative_to(root)), "sha256": _sha256_bytes(source_bytes["TwoLights.cfg"])},
            "rate_card_sha256": sha256_file(run_dir / "rate-card.json"),
            "controller_schema_sha256": sha256_file(controller_schema_path),
            "proposal_schema_sha256": sha256_file(proposal_schema_path),
            "prompt_sha256": {
                role: sha256_file(path) for role, path in prompt_paths.items()
            },
        },
        "selection_policy": "sample one official particle from final normalized weights before verification",
        "selection_complete": False,
        "official_direct_candidate_sha256": None,
        "official_discipl_candidate_sha256": None,
        "arm_timing_note": (
            "Per-arm times sum generation and verification phases; deliberate "
            "waiting at the selection barrier is excluded. Run wall time includes all phases."
        ),
        "nonconformities": [],
    }
    write_json(run_dir / "manifest.json", manifest)

    tla_source = source_bytes["TwoLights.tla"].decode("utf-8")
    cfg_source = source_bytes["TwoLights.cfg"].decode("utf-8")
    for name, data in source_bytes.items():
        _write_once(run_dir / "inputs" / name, data)
    direct_prompt = prompt_paths["direct"].read_text(encoding="utf-8")
    planner_prompt = prompt_paths["planner"].read_text(encoding="utf-8")
    follower_prompt = prompt_paths["follower"].read_text(encoding="utf-8")
    common_inputs = {
        "TwoLights.tla": tla_source,
        "TwoLights.cfg": cfg_source,
        "artifact-contract.md": direct_prompt,
    }

    attempt_lock = threading.Lock()

    def invoke(request: WorkerRequest) -> WorkerResult:
        # Count before entering the worker, including setup/spawn exceptions.
        # Reconcile this existing manifest with intent/result spools on replay.
        with attempt_lock:
            manifest["attempted_calls_by_role"][request.role] += 1
            write_json(run_dir / "manifest.json", manifest)
        return fixture(request) if fixture is not None else run_worker(request)

    def score(particle: Particle, step: ControllerStep, proposal: Proposal) -> IncrementalScore:
        if fixture is not None:
            fixture.validate_particle(particle)
        return _incremental_score(particle, step, proposal)

    nonconformities: list[str] = manifest["nonconformities"]
    nonconformity_lock = threading.Lock()
    active_followers = 0
    maximum_followers = 0
    concurrency_lock = threading.Lock()
    follower_counter = itertools.count(1)
    follower_count_lock = threading.Lock()
    planner_repair_count = 0
    discipl_makespan = 0.0
    official_hash: str | None = None
    discipl_verification: dict[str, Any] | None = None
    selected_path: Path | None = None
    selected_metadata: dict[str, Any] = {}

    try:
        direct_arms = ["direct", "cheap_alone"] if offline_screen else ["direct"]
        direct_records = {}
        for arm in direct_arms:
            arm_started = time.monotonic()
            spool = run_dir / arm / "calls" / f"{arm}-0001"
            result = invoke(WorkerRequest(
                call_id=f"{arm}-0001", role=arm,
                prompt=_prompt_with_inputs(direct_prompt, {
                    "TwoLights.tla": tla_source, "TwoLights.cfg": cfg_source}),
                input_files={"TwoLights.tla": tla_source, "TwoLights.cfg": cfg_source},
                artifact_path=None, spool_dir=spool, codex_home=codex_home,
                timeout_seconds=WORKER_TIMEOUT_SECONDS,
            ))
            _context(spool, arm=arm, result=result)
            issue = _call_issue(result)
            candidate = run_dir / arm / "candidate.py"
            digest = None
            verification = None
            if issue is None:
                data = (spool / "final.txt").read_bytes()
                if fixture is not None and data != fixture.golden.encode("utf-8"):
                    raise PipelineError("offline screen refused unreviewed direct candidate")
                _write_once(candidate, data)
                digest = sha256_file(candidate)
            else:
                nonconformities.append(issue)
                verification = _failed_verification(issue)
            manifest[f"official_{arm}_candidate_sha256"] = digest
            write_json(run_dir / "manifest.json", manifest)
            direct_records[arm] = {
                "path": candidate, "hash": digest, "verification": verification,
                "seconds": time.monotonic() - arm_started,
            }

        discipl_started = time.monotonic()
        controller, planner_repair_count, planner_error = _planner(
            run_dir=run_dir,
            codex_home=codex_home,
            base_prompt=planner_prompt,
            invoke=invoke,
            common_inputs={
                **common_inputs,
                "controller.schema.json": controller_schema_path.read_text(encoding="utf-8"),
            },
        )
        if planner_error is not None:
            nonconformities.append(planner_error)
        if controller is None:
            discipl_verification = _failed_verification(
                planner_error or "Planner produced no controller"
            )
        else:
            _write_json_once(
                run_dir / "discipl" / "planner" / "controller.json",
                controller.as_dict(),
            )

            def follower(particle: Particle, step: ControllerStep) -> Proposal:
                nonlocal active_followers, maximum_followers
                with follower_count_lock:
                    ordinal = next(follower_counter)
                call_id = f"follower-{ordinal:04d}-{step.id}-{particle.particle_id}"
                spool = run_dir / "discipl" / "calls" / call_id
                step_document = json.dumps(
                    step.follower_view(), indent=2, sort_keys=True, ensure_ascii=False
                )
                follower_inputs = {
                    **common_inputs,
                    "partial-candidate.py": _partial_source(particle),
                    "controller-step.json": step_document,
                    "proposal.schema.json": proposal_schema_path.read_text(encoding="utf-8"),
                }
                prompt = _prompt_with_inputs(
                    follower_prompt
                    + "\n\nReturn exactly the requested fragment for this step.\n",
                    follower_inputs,
                )
                with concurrency_lock:
                    active_followers += 1
                    maximum_followers = max(maximum_followers, active_followers)
                try:
                    result = invoke(
                        WorkerRequest(
                            call_id=call_id,
                            role="follower",
                            prompt=prompt,
                            input_files=follower_inputs,
                            artifact_path=None,
                            spool_dir=spool,
                            codex_home=codex_home,
                            timeout_seconds=WORKER_TIMEOUT_SECONDS,
                            output_schema=proposal_schema,
                        )
                    )
                finally:
                    with concurrency_lock:
                        active_followers -= 1
                _context(
                    spool,
                    arm="discipl",
                    result=result,
                    particle=particle,
                    step=step,
                )
                issue = _call_issue(result)
                if issue is not None:
                    with nonconformity_lock:
                        nonconformities.append(issue)
                    raise PipelineError(issue)
                return proposal_from_json(
                    (spool / "final.txt").read_text(encoding="utf-8"), step=step
                )

            result = run_smc(
                controller,
                follower,
                score,
                config=SMCConfig(
                    population_size=particle_count,
                    concurrency=max_concurrency,
                    seed=seed,
                ),
            )
            trace_rows = []
            for trace in result.traces:
                row = asdict(trace)
                row.update(
                    {
                        "schema_version": "tla-steer-smc-trace/0.1",
                        "stopping_reason": result.stopping_reason,
                    }
                )
                trace_rows.append(row)
            _write_jsonl_once(run_dir / "discipl" / "trace.jsonl", trace_rows)
            _write_json_once(
                run_dir / "discipl" / "particles.json",
                {
                    "schema_version": "tla-steer-particles/0.1",
                    "stopping_reason": result.stopping_reason,
                    "official_particle_index": result.official_particle_index,
                    "selection_weights": result.selection_weights,
                    "particles": result.particles,
                },
            )
            if result.official_particle is None:
                discipl_verification = _failed_verification(result.stopping_reason)
                nonconformities.append(result.stopping_reason)
            else:
                if fixture is not None:
                    fixture.validate_particle(result.official_particle)
                selected = _candidate_source(result.official_particle).encode("utf-8")
                official_hash = _sha256_bytes(selected)
                selected_path = run_dir / "discipl" / "selected-candidate.py"
                _write_once(selected_path, selected)
                selected_metadata = {
                    "frozen_candidate_sha256": official_hash,
                    "official_particle_id": result.official_particle.particle_id,
                    "official_particle_index": result.official_particle_index,
                }
        discipl_makespan = time.monotonic() - discipl_started

        # Resolve both arms and persist their official bytes/digests before any
        # final grading. A failed arm has a null hash and a recorded reason;
        # it must not prevent the independently selected other arm being graded.
        manifest.update(
            {
                "selection_complete": True,
                "official_discipl_candidate_sha256": official_hash,
            }
        )
        write_json(run_dir / "manifest.json", manifest)

        for arm, record in direct_records.items():
            verification_started = time.monotonic()
            verification = record["verification"]
            if verification is None:
                if sha256_file(record["path"]) != record["hash"]:
                    raise PipelineError("official candidate changed after selection")
                if fixture is not None and record["path"].read_bytes() != fixture.golden.encode("utf-8"):
                    raise PipelineError("offline screen refused unreviewed direct candidate")
                verification = verify_candidate(record["path"])
                verification["frozen_candidate_sha256"] = record["hash"]
            _write_json_once(run_dir / arm / "verification.json", verification)
            if verification.get("outcome") == "EVALUATOR_ERROR":
                raise PipelineError(f"{arm} verifier infrastructure failure: {verification.get('contract_failures')}")
            record["seconds"] += time.monotonic() - verification_started

        verification_started = time.monotonic()
        if discipl_verification is None:
            assert selected_path is not None
            if sha256_file(selected_path) != official_hash:
                raise PipelineError("official candidate changed after selection")
            discipl_verification = verify_candidate(selected_path)
            discipl_verification.update(selected_metadata)
        _write_json_once(run_dir / "discipl" / "verification.json", discipl_verification)
        if discipl_verification.get("outcome") == "EVALUATOR_ERROR":
            raise PipelineError(f"discipl verifier infrastructure failure: {discipl_verification.get('contract_failures')}")
        discipl_makespan += time.monotonic() - verification_started

        manifest.update(
            {
                "status": "completed" if not nonconformities else "completed_with_failures",
                "end_timestamp": _utc_now(),
                "run_wall_time_seconds": time.monotonic() - started,
                "maximum_observed_concurrency": max(1, maximum_followers),
                "arm_makespan_seconds": {
                    **{arm: record["seconds"] for arm, record in direct_records.items()},
                    "discipl": discipl_makespan,
                },
                "planner_schema_repair_count": planner_repair_count,
                "follower_call_count": next(follower_counter) - 1,
                "official_discipl_candidate_sha256": official_hash,
            }
        )
        write_json(run_dir / "manifest.json", manifest)
        write_run_report(run_dir)
        return run_dir
    except Exception as exc:
        manifest.update(
            {
                "status": "pipeline_error",
                "end_timestamp": _utc_now(),
                "run_wall_time_seconds": time.monotonic() - started,
                "maximum_observed_concurrency": max(1, maximum_followers),
                "pipeline_error": f"{type(exc).__name__}: {exc}",
            }
        )
        write_json(run_dir / "manifest.json", manifest)
        try:
            write_run_report(run_dir)
        except Exception:
            pass
        raise PipelineError(f"run failed; evidence retained at {run_dir}: {exc}") from exc


__all__ = ["PipelineError", "run_comparison"]
