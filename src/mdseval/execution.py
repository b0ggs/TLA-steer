"""Experiment orchestration and immutable raw-artifact writing."""

from __future__ import annotations

import hashlib
import json
import os
import platform
import re
import shutil
import subprocess
import tempfile
import uuid
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .capture import (
    GitCapture,
    ParsedEvents,
    Redactor,
    capture_git,
    parse_event_stream,
    run_hidden_checks,
    write_json,
    is_ignored_generated_path,
    is_secret_name,
)
from .compare import deterministic_pair_order, invariant_mismatches
from .config import CaseConfig, ExperimentConfig
from .fixtures import audit_final_subject_tree, prepare_fixture
from .hashing import sha256_bytes, sha256_file, sha256_text, tree_sha256
from .gitutils import init_repository, run_git
from .processutils import run_process_group
from .report import build_report, write_report
from .runner.base import RunResult, SubjectRunner
from .runner.codex_cli import build_judge_command, doctor, isolated_environment
from .scoring.mechanical import score_run
from .scoring.mechanical import HARD_FIELDS
from .scoring.qualitative import (
    build_blinded_packet,
    parse_judge_output,
    restore_winner,
)
from .wrapper import WRAPPER_PROMPT
from .variants import validate_locked_variants

def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def environment_secret_values() -> tuple[str, ...]:
    """Collect only values for redaction; names and values are never persisted."""
    return tuple(
        value
        for name, value in os.environ.items()
        if value and is_secret_name(name)
    )


def create_run_directory(root: Path, run_id: str | None = None) -> Path:
    if run_id is None:
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        run_id = f"{stamp}-{uuid.uuid4().hex[:8]}"
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]*", run_id):
        raise ValueError("run id must be one safe path component")
    runs_root = root / "runs"
    if runs_root.is_symlink() or not runs_root.is_dir():
        raise ValueError("runs must be a real directory inside the evaluator root")
    try:
        runs_root.resolve().relative_to(root.resolve())
    except ValueError as exc:
        raise ValueError("runs directory escapes evaluator root") from exc
    run_dir = runs_root / run_id
    if run_dir.is_symlink():
        raise ValueError("run directory must not be a symlink")
    try:
        run_dir.resolve().relative_to(runs_root.resolve())
    except ValueError as exc:
        raise ValueError("run directory escapes runs root") from exc
    if run_dir.exists() and any(run_dir.iterdir()):
        raise FileExistsError(f"refusing to reuse nonempty run directory: {run_dir}")
    run_dir.mkdir(parents=True, exist_ok=True)
    return run_dir


def _git(root: Path, *args: str) -> str:
    return str(run_git(root, *args))


def evaluator_identity(root: Path, *, require_clean: bool) -> dict[str, str]:
    commit = _git(root, "rev-parse", "HEAD").strip()
    status = _git(root, "status", "--porcelain", "--untracked-files=all")
    if require_clean and status.strip():
        raise RuntimeError(
            "live comparisons require a clean evaluator checkout; commit or remove changes first"
        )
    state_material = status.encode("utf-8") + _git(
        root, "diff", "--no-ext-diff", "--no-textconv", "HEAD"
    ).encode("utf-8")
    for line in status.splitlines():
        relative = line[3:]
        if " -> " in relative:
            relative = relative.split(" -> ", 1)[1]
        path = root / relative
        if path.is_file() and not path.is_symlink():
            state_material += relative.encode("utf-8") + hashlib.sha256(
                path.read_bytes()
            ).digest()
    return {
        "evaluator_commit": commit,
        "evaluator_state_sha256": sha256_bytes(state_material)
        if status.strip()
        else sha256_text(f"clean:{commit}"),
        "evaluator_clean": str(not status.strip()).lower(),
    }


def _codex_version(fake: bool) -> str:
    if fake:
        return "FAKE"
    executable = shutil.which("codex")
    if not executable:
        return "UNAVAILABLE"
    process = subprocess.run(
        [executable, "--version"],
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
    )
    return process.stdout.strip() if process.returncode == 0 else "INCOMPATIBLE"


def current_control_context(
    experiment: ExperimentConfig, *, fake: bool = False
) -> tuple[dict[str, str], str]:
    evaluator = evaluator_identity(experiment.root, require_clean=not fake)
    values = {
        "experiment_sha256": sha256_file(experiment.path),
        "wrapper_prompt_sha256": sha256_text(WRAPPER_PROMPT),
        "judge_schema_sha256": sha256_file(
            experiment.root / "schemas/judge-output.schema.json"
        ),
        "evaluator_commit": evaluator["evaluator_commit"],
        "evaluator_state_sha256": evaluator["evaluator_state_sha256"],
        "codex_cli_version": _codex_version(fake),
        "python_version": platform.python_version(),
        "os": platform.system(),
        "architecture": platform.machine(),
        "model": experiment.runner.model,
        "reasoning_effort": experiment.runner.reasoning_effort,
        "sandbox": experiment.runner.sandbox,
        "approval_policy": experiment.runner.approval_policy,
        "run_order_seed": experiment.run_order_seed,
    }
    return evaluator, sha256_text(json.dumps(values, sort_keys=True))


def manifest_matches_authoritative(
    experiment: ExperimentConfig, manifest: dict[str, Any], *, fake: bool
) -> bool:
    try:
        if sha256_file(experiment.path) != manifest["experiment_sha256"]:
            return False
        if sha256_text(WRAPPER_PROMPT) != manifest["wrapper_prompt_sha256"]:
            return False
        if (
            sha256_file(experiment.root / "schemas/judge-output.schema.json")
            != manifest["judge_schema_sha256"]
        ):
            return False
        if _codex_version(fake) != manifest["codex_cli_version"]:
            return False
        if evaluator_identity(experiment.root, require_clean=not fake)[
            "evaluator_state_sha256"
        ] != manifest["evaluator_state_sha256"]:
            return False
        for variant_id, expected_hash in manifest.get("variant_hashes", {}).items():
            if (
                variant_id not in experiment.variants
                or sha256_file(experiment.variants[variant_id]) != expected_hash
            ):
                return False
        for case_id, expected_hash in manifest.get("case_hashes", {}).items():
            if (
                case_id not in experiment.cases
                or tree_sha256(experiment.cases[case_id].directory) != expected_hash
                or tree_sha256(experiment.cases[case_id].fixture_dir)
                != manifest["fixture_hashes"][case_id]
            ):
                return False
    except (KeyError, OSError, ValueError, RuntimeError):
        return False
    return True


def frozen_fields(
    experiment: ExperimentConfig,
    case: CaseConfig,
    evaluator: dict[str, str],
    *,
    fake: bool,
    authoritative: dict[str, str] | None = None,
) -> dict[str, Any]:
    authoritative = authoritative or {}
    return {
        "experiment_sha256": authoritative.get(
            "experiment_sha256", sha256_file(experiment.path)
        ),
        "case_definition_sha256": authoritative.get(
            "case_definition_sha256", case.definition_hash
        ),
        "fixture_tree_sha256": authoritative.get(
            "fixture_tree_sha256", case.fixture_hash
        ),
        "wrapper_prompt_sha256": authoritative.get(
            "wrapper_prompt_sha256", sha256_text(WRAPPER_PROMPT)
        ),
        "judge_schema_sha256": authoritative.get(
            "judge_schema_sha256",
            sha256_file(experiment.root / "schemas/judge-output.schema.json"),
        ),
        "evaluator_commit": evaluator["evaluator_commit"],
        "evaluator_state_sha256": evaluator["evaluator_state_sha256"],
        "codex_cli_version": authoritative.get(
            "codex_cli_version", _codex_version(fake)
        ),
        "python_version": platform.python_version(),
        "os": platform.system(),
        "architecture": platform.machine(),
        "model": experiment.runner.model,
        "reasoning_effort": experiment.runner.reasoning_effort,
        "sandbox": experiment.runner.sandbox,
        "approval_policy": experiment.runner.approval_policy,
        "run_order_seed": experiment.run_order_seed,
    }


def authoritative_inputs(case: CaseConfig, variant_path: Path) -> dict[str, str]:
    return {
        "case_definition_sha256": tree_sha256(case.directory),
        "fixture_tree_sha256": tree_sha256(case.fixture_dir),
        "variant_sha256": sha256_file(variant_path),
        "contract_sha256": sha256_file(case.contract_path),
        "rubric_sha256": sha256_file(case.rubric_path),
        "wrapper_prompt_sha256": sha256_text(WRAPPER_PROMPT),
    }


def _verified_instruction_text(path: Path, expected_hash: str) -> str:
    raw = path.read_bytes()
    if sha256_bytes(raw) != expected_hash:
        raise RuntimeError("instruction bytes changed")
    return raw.decode("utf-8")


def freeze_inputs(
    experiment: ExperimentConfig,
    case: CaseConfig,
    variant_path: Path,
    *,
    fake: bool,
) -> dict[str, str]:
    validate_locked_variants(experiment.variants)
    current = authoritative_inputs(case, variant_path)
    current["experiment_sha256"] = sha256_file(experiment.path)
    current["judge_schema_sha256"] = sha256_file(
        experiment.root / "schemas/judge-output.schema.json"
    )
    current["codex_cli_version"] = _codex_version(fake)
    if current["experiment_sha256"] != experiment.definition_hash:
        raise RuntimeError("experiment file changed after validation")
    if current["case_definition_sha256"] != case.definition_hash:
        raise RuntimeError(f"case definition changed after validation: {case.id}")
    if current["fixture_tree_sha256"] != case.fixture_hash:
        raise RuntimeError(f"fixture changed after validation: {case.id}")
    return current


def _verify_prepared_inputs(
    case: CaseConfig, variant_path: Path, subject_repo: Path
) -> None:
    if sha256_file(subject_repo / "CODER.md") != sha256_file(variant_path):
        raise RuntimeError("copied CODER.md does not match the frozen variant")
    if sha256_file(subject_repo / ".issue-contract.md") != sha256_file(
        case.contract_path
    ):
        raise RuntimeError("copied contract does not match the frozen contract")
    expected_paths = {
        path.relative_to(case.fixture_dir).as_posix()
        for path in case.fixture_dir.rglob("*")
        if path.is_file()
        and not is_ignored_generated_path(
            path.relative_to(case.fixture_dir).as_posix()
        )
    } | {"CODER.md", ".issue-contract.md"}
    actual_paths = {
        path.relative_to(subject_repo).as_posix()
        for path in subject_repo.rglob("*")
        if path.is_file() and ".git" not in path.relative_to(subject_repo).parts
    }
    if expected_paths != actual_paths:
        raise RuntimeError("prepared subject input set differs from frozen fixture inputs")
    expected_directories = {
        path.relative_to(case.fixture_dir).as_posix()
        for path in case.fixture_dir.rglob("*")
        if path.is_dir()
        and not is_ignored_generated_path(
            path.relative_to(case.fixture_dir).as_posix()
        )
    }
    actual_directories = {
        path.relative_to(subject_repo).as_posix()
        for path in subject_repo.rglob("*")
        if path.is_dir() and ".git" not in path.relative_to(subject_repo).parts
    }
    if expected_directories != actual_directories:
        raise RuntimeError("prepared subject directory set differs from frozen fixture inputs")
    for relative in expected_directories:
        source_mode = (case.fixture_dir / relative).stat().st_mode & 0o7777
        copied_mode = (subject_repo / relative).stat().st_mode & 0o7777
        if source_mode != copied_mode:
            raise RuntimeError(f"prepared fixture directory mode differs: {relative}")
    for relative in expected_paths - {"CODER.md", ".issue-contract.md"}:
        source = case.fixture_dir / relative
        copied = subject_repo / relative
        if sha256_file(source) != sha256_file(copied):
            raise RuntimeError(f"prepared fixture file differs: {relative}")
        if source.stat().st_mode & 0o7777 != copied.stat().st_mode & 0o7777:
            raise RuntimeError(f"prepared fixture file mode differs: {relative}")


def invariant_hash(fields: dict[str, Any]) -> str:
    return sha256_text(json.dumps(fields, sort_keys=True, separators=(",", ":")))


def _ensure_runner_files(artifact_dir: Path) -> None:
    for name in ("events.jsonl", "stderr.txt", "final.txt"):
        path = artifact_dir / name
        if not path.exists():
            path.write_text("", encoding="utf-8")


def execute_one(
    *,
    experiment: ExperimentConfig,
    case: CaseConfig,
    variant_id: str,
    variant_path: Path,
    replicate: int,
    artifact_dir: Path,
    runner: SubjectRunner,
    evaluator: dict[str, str],
    fake: bool,
    redactor: Redactor,
    expected_inputs: dict[str, str],
) -> dict[str, Any]:
    if artifact_dir.exists() and any(artifact_dir.iterdir()):
        raise FileExistsError(f"artifact directory is not empty: {artifact_dir}")
    artifact_dir.mkdir(parents=True, exist_ok=True)
    started = utc_now()
    fixture = None
    errors: list[str] = []
    run_result = RunResult(
        status="INTERRUPTED",
        exit_code=None,
        duration_seconds=0.0,
        interrupted=True,
    )
    events = ParsedEvents(
        valid=False,
        events=(),
        commands=(),
        file_changes=(),
        usage={
            "input_tokens": 0,
            "cached_input_tokens": 0,
            "output_tokens": 0,
            "reasoning_output_tokens": 0,
            "usage_reported": False,
            "total_tokens": 0,
        },
    )
    git = GitCapture(
        final_head="",
        status="",
        diff="",
        changed_paths=(),
        untracked=(),
        unauthorized_commit=False,
        historical_diff="",
    )
    checks = ()
    final_text = ""
    mechanical = {
        "schema_version": 1,
        "disposition": None,
        "fields": {field: False for field in HARD_FIELDS},
        "failed_fields": list(HARD_FIELDS),
        "hard_pass": False,
        "mechanical_score": 0,
    }
    input_before: dict[str, str] = {}
    input_after: dict[str, str] = {}
    capture_ok = False
    try:
        try:
            input_before = authoritative_inputs(case, variant_path)
            input_before["experiment_sha256"] = sha256_file(experiment.path)
            input_before["judge_schema_sha256"] = sha256_file(
                experiment.root / "schemas/judge-output.schema.json"
            )
            input_before["codex_cli_version"] = _codex_version(fake)
            if input_before != expected_inputs:
                raise RuntimeError("frozen evaluator input changed before subject execution")
            variant_hash = input_before["variant_sha256"]
            fixture = prepare_fixture(case, variant_path, variant_hash)
            _verify_prepared_inputs(case, variant_path, fixture.repo)
            run_result = runner.run(
                fixture,
                artifact_dir,
                min(case.timeout_seconds, experiment.runner.timeout_seconds),
                redactor,
            )
        except Exception as exc:
            errors.append(redactor.text(f"runner/preflight: {type(exc).__name__}: {exc}"))
        _ensure_runner_files(artifact_dir)
        try:
            events = parse_event_stream(artifact_dir / "events.jsonl")
        except Exception as exc:
            errors.append(redactor.text(f"event capture: {type(exc).__name__}: {exc}"))
        final_text = (artifact_dir / "final.txt").read_text(
            encoding="utf-8", errors="replace"
        )
        if fixture is not None:
            try:
                audit_final_subject_tree(fixture.repo)
                git = capture_git(fixture.repo, fixture.baseline_commit, redactor)
                capture_ok = True
            except Exception as exc:
                errors.append(redactor.text(f"git capture: {type(exc).__name__}: {exc}"))
            try:
                input_after = authoritative_inputs(case, variant_path)
                input_after["experiment_sha256"] = sha256_file(experiment.path)
                input_after["judge_schema_sha256"] = sha256_file(
                    experiment.root / "schemas/judge-output.schema.json"
                )
                input_after["codex_cli_version"] = _codex_version(fake)
                if input_after != expected_inputs:
                    raise RuntimeError("frozen evaluator input changed before hidden checks")
                checks = run_hidden_checks(case, fixture.repo, redactor)
                input_after = authoritative_inputs(case, variant_path)
                input_after["experiment_sha256"] = sha256_file(experiment.path)
                input_after["judge_schema_sha256"] = sha256_file(
                    experiment.root / "schemas/judge-output.schema.json"
                )
                input_after["codex_cli_version"] = _codex_version(fake)
                if input_after != expected_inputs:
                    raise RuntimeError("frozen evaluator input changed during hidden checks")
            except Exception as exc:
                errors.append(redactor.text(f"hidden checks: {type(exc).__name__}: {exc}"))
                checks = ()
            try:
                mechanical = score_run(
                    case, run_result, events, final_text, git, checks, fixture.repo
                )
                if not capture_ok:
                    for field in (
                        "allowed_paths_only",
                        "forbidden_paths_untouched",
                        "required_unchanged_regions_preserved",
                        "no_unauthorized_commit",
                        "no_unrequested_artifacts",
                    ):
                        mechanical["fields"][field] = False
                        if field not in mechanical["failed_fields"]:
                            mechanical["failed_fields"].append(field)
                    mechanical["hard_pass"] = False
                    mechanical["mechanical_score"] = 0
            except Exception as exc:
                errors.append(redactor.text(f"mechanical scoring: {type(exc).__name__}: {exc}"))
        if not input_after:
            try:
                input_after = authoritative_inputs(case, variant_path)
                input_after["experiment_sha256"] = sha256_file(experiment.path)
                input_after["judge_schema_sha256"] = sha256_file(
                    experiment.root / "schemas/judge-output.schema.json"
                )
                input_after["codex_cli_version"] = _codex_version(fake)
            except Exception as exc:
                errors.append(redactor.text(f"final input hash: {type(exc).__name__}: {exc}"))
        inputs_stable = bool(
            input_before
            and input_before == expected_inputs
            and input_after == expected_inputs
        )
        if errors:
            run_result = RunResult(
                status="INTERRUPTED",
                exit_code=run_result.exit_code,
                duration_seconds=run_result.duration_seconds,
                timed_out=run_result.timed_out,
                interrupted=True,
            )
            mechanical["fields"]["runner_completed"] = False
            mechanical["hard_pass"] = False
            if "runner_completed" not in mechanical["failed_fields"]:
                mechanical["failed_fields"].append("runner_completed")
        frozen = frozen_fields(
            experiment,
            case,
            evaluator,
            fake=fake,
            authoritative=expected_inputs,
        )
        manifest = {
            "schema_version": 1,
            **frozen,
            "invariant_sha256": invariant_hash(frozen),
            "experiment_id": experiment.experiment_id,
            "variant_id": variant_id,
            "variant_sha256": expected_inputs["variant_sha256"],
            "case_id": case.id,
            "replicate": replicate,
            "baseline_commit": fixture.baseline_commit if fixture else None,
            "final_head": git.final_head,
            "unauthorized_commit": git.unauthorized_commit,
            "fixture_input_sha256": fixture.fixture_hash if fixture else None,
            "frozen_inputs_before": input_before,
            "frozen_inputs_after": input_after,
            "frozen_inputs_stable": inputs_stable,
            "start_timestamp": started,
            "end_timestamp": utc_now(),
            "status": run_result.status,
            "runner_error": "; ".join(errors) if errors else None,
        }
        checks_json = [asdict(check) for check in checks]
        commands_json = list(events.commands)
        write_json(artifact_dir / "manifest.json", manifest)
        (artifact_dir / "git-status.txt").write_text(git.status, encoding="utf-8")
        (artifact_dir / "diff.patch").write_text(git.diff, encoding="utf-8")
        (artifact_dir / "historical-diff.patch").write_text(
            git.historical_diff, encoding="utf-8"
        )
        write_json(artifact_dir / "untracked.json", list(git.untracked))
        write_json(artifact_dir / "commands.json", commands_json)
        write_json(artifact_dir / "checks.json", checks_json)
        write_json(artifact_dir / "mechanical-score.json", mechanical)
        summary = {
            "schema_version": 1,
            "manifest": manifest,
            "status": run_result.status,
            "exit_code": run_result.exit_code,
            "duration_seconds": run_result.duration_seconds,
            "timed_out": run_result.timed_out,
            "interrupted": run_result.interrupted,
            "final_text": final_text,
            "diff": git.diff,
            "historical_diff_path": "historical-diff.patch",
            "changed_paths": list(git.changed_paths),
            "commands": commands_json,
            "checks": checks_json,
            "mechanical": mechanical,
            "usage": events.usage,
            "valid_event_stream": events.valid,
            "malformed_event_lines": list(events.malformed_lines),
        }
        write_json(artifact_dir / "run-summary.json", summary)
        return summary
    finally:
        if fixture is not None:
            fixture.cleanup()


def _judge_prompt() -> str:
    return (
        "Read packet.json and judge-output.schema.json. Apply the packet's judge "
        "instructions. Return only one JSON object conforming exactly to the schema."
    )


def run_live_judge(
    experiment: ExperimentConfig,
    packet: dict[str, Any],
    redactor: Redactor,
) -> tuple[str, dict[str, Any] | None, str | None]:
    isolated_home = os.environ.get("MDSEVAL_CODEX_HOME")
    if not isolated_home:
        return "NOT_RUN", None, "MDSEVAL_CODEX_HOME is not set"
    with tempfile.TemporaryDirectory(prefix="mdseval-judge-") as temporary:
        repo = Path(temporary)
        write_json(repo / "packet.json", packet)
        shutil.copy2(
            experiment.root / "schemas" / "judge-output.schema.json",
            repo / "judge-output.schema.json",
        )
        init_repository(repo)
        output = repo / "judge-output.json"
        command = build_judge_command(experiment, repo, output)
        process = run_process_group(
            command,
            cwd=repo,
            input_text=_judge_prompt(),
            timeout=experiment.judge.timeout_seconds,
            environment=isolated_environment(isolated_home),
        )
        if process.timed_out:
            return "NOT_RUN", None, "judge timed out"
        if process.interrupted:
            return "NOT_RUN", None, "judge interrupted"
        if process.returncode or not output.is_file():
            return "NOT_RUN", None, redactor.text(
                f"judge exited {process.returncode}: {process.stderr}"
            )
        try:
            parsed = parse_judge_output(output.read_text(encoding="utf-8"))
        except Exception as exc:
            return "NOT_RUN", None, redactor.text(f"invalid judge output: {exc}")
        return "COMPLETED", redactor.object(parsed), None


def execute_pair_experiment(
    *,
    experiment: ExperimentConfig,
    runner: SubjectRunner,
    variant_a: str,
    variant_b: str,
    suite: str,
    repeats: int,
    fake: bool,
    run_id: str | None = None,
    run_judge: bool = True,
    live_runner_status: str | None = None,
    artifact_variant_a: str | None = None,
    artifact_variant_b: str | None = None,
    write_default_report: bool = True,
    manifest_metadata: dict[str, Any] | None = None,
) -> tuple[Path, list[dict[str, Any]], dict[str, Any]]:
    if repeats <= 0:
        raise ValueError("repeats must be positive")
    if suite not in experiment.suites:
        raise ValueError(f"unknown suite: {suite}")
    if variant_a not in experiment.variants or variant_b not in experiment.variants:
        raise ValueError("unknown variant")
    evaluator = evaluator_identity(experiment.root, require_clean=not fake)
    run_dir = create_run_directory(experiment.root, run_id)
    redactor = Redactor(environment_secret_values())
    started = utc_now()
    artifact_variant_a = artifact_variant_a or variant_a
    artifact_variant_b = artifact_variant_b or variant_b
    comparisons: list[dict[str, Any]] = []
    run_records: list[dict[str, Any]] = []
    input_snapshots = {
        (case_id, variant_id): freeze_inputs(
            experiment,
            experiment.cases[case_id],
            experiment.variants[variant_id],
            fake=fake,
        )
        for case_id in experiment.suites[suite]
        for variant_id in {variant_a, variant_b}
    }
    for case_id in experiment.suites[suite]:
        case = experiment.cases[case_id]
        for replicate in range(1, repeats + 1):
            order = deterministic_pair_order(
                experiment.run_order_seed, case_id, replicate, variant_a, variant_b
            )
            summaries: dict[str, dict[str, Any]] = {}
            for variant_id in order:
                artifact_id = (
                    artifact_variant_a if variant_id == variant_a else artifact_variant_b
                )
                artifact = (
                    run_dir / "variants" / artifact_id / case_id / str(replicate)
                )
                summaries[variant_id] = execute_one(
                    experiment=experiment,
                    case=case,
                    variant_id=variant_id,
                    variant_path=experiment.variants[variant_id],
                    replicate=replicate,
                    artifact_dir=artifact,
                    runner=runner,
                    evaluator=evaluator,
                    fake=fake,
                    redactor=redactor,
                    expected_inputs=input_snapshots[(case_id, variant_id)],
                )
                run_records.append(summaries[variant_id]["manifest"])
            left, right = summaries[variant_a], summaries[variant_b]
            mismatches = invariant_mismatches(left["manifest"], right["manifest"])
            abort = False
            try:
                instruction_texts = tuple(
                    _verified_instruction_text(experiment.variants[item], input_snapshots[(case_id, item)]["variant_sha256"])
                    for item in (variant_a, variant_b)
                )
            except (OSError, UnicodeError, RuntimeError) as exc:
                mismatches["variant_input_before_judge"] = ("frozen", type(exc).__name__)
                instruction_texts = ("", "")
                abort = True
            packet, labels = ({}, {}) if abort else build_blinded_packet(
                case_id=case_id,
                replicate=replicate,
                seed=experiment.run_order_seed,
                contract=case.contract_path.read_text(encoding="utf-8"),
                fixture=case.fixture_dir,
                left=left,
                right=right,
                variant_ids=(variant_a, variant_b, artifact_variant_a, artifact_variant_b),
                variant_paths=(
                    str(experiment.variants[variant_a]),
                    str(experiment.variants[variant_b]),
                ),
                instruction_texts=instruction_texts,
            )
            packet = redactor.object(packet)
            judge_status = "NOT_RUN"
            judge_output = None
            judge_error = None
            qualitative_winner = "NOT_RUN"
            expected_runtime = input_snapshots[(case_id, variant_a)][
                "codex_cli_version"
            ]
            if (
                _codex_version(fake) != expected_runtime
                or sha256_file(experiment.root / "schemas/judge-output.schema.json")
                != input_snapshots[(case_id, variant_a)]["judge_schema_sha256"]
            ):
                mismatches["judge_runtime_or_schema"] = (
                    expected_runtime,
                    _codex_version(fake),
                )
            if run_judge and not fake and not mismatches:
                judge_status, judge_output, judge_error = run_live_judge(
                    experiment, packet, redactor
                )
                if _codex_version(fake) != expected_runtime:
                    mismatches["judge_runtime_after"] = (
                        expected_runtime,
                        _codex_version(fake),
                    )
                if judge_output:
                    side = restore_winner(judge_output["winner"], labels)
                    qualitative_winner = (
                        "TIE"
                        if side == "TIE"
                        else variant_a
                        if side == "left"
                        else variant_b
                    )
            comparison_path = Path("comparisons") / f"{case_id}-{replicate}.json"
            raw_names = (
                "manifest.json",
                "events.jsonl",
                "stderr.txt",
                "final.txt",
                "git-status.txt",
                "diff.patch",
                "historical-diff.patch",
                "untracked.json",
                "commands.json",
                "checks.json",
                "mechanical-score.json",
                "run-summary.json",
            )
            artifact_roots = {
                "champion": (
                    Path("variants") / artifact_variant_a / case_id / str(replicate)
                ),
                "candidate": (
                    Path("variants") / artifact_variant_b / case_id / str(replicate)
                ),
            }
            raw_artifact_paths = {
                side: {
                    name: (root / name).as_posix()
                    for name in raw_names
                }
                for side, root in artifact_roots.items()
            }
            inputs_stable = bool(
                left["manifest"].get("frozen_inputs_stable")
                and right["manifest"].get("frozen_inputs_stable")
            )
            if not inputs_stable:
                mismatches["frozen_inputs_stable"] = (
                    left["manifest"].get("frozen_inputs_stable"),
                    right["manifest"].get("frozen_inputs_stable"),
                )
            comparison = {
                "schema_version": 1,
                "case_id": case_id,
                "suite": case.suite,
                "replicate": replicate,
                "run_order": list(order),
                "valid": not mismatches and inputs_stable,
                "invariant_mismatches": mismatches,
                "left_variant_internal": variant_a,
                "right_variant_internal": variant_b,
                "champion": left,
                "candidate": right,
                "qualitative_status": judge_status,
                "qualitative_winner": (
                    "candidate"
                    if qualitative_winner == variant_b
                    else "champion"
                    if qualitative_winner == variant_a
                    else qualitative_winner
                ),
                "judge_labels_internal": labels,
                "judge_packet": packet,
                "judge_output": judge_output,
                "judge_error": judge_error,
                "evidence_path": comparison_path.as_posix(),
                "raw_artifact_paths": raw_artifact_paths,
            }
            (run_dir / "comparisons").mkdir(parents=True, exist_ok=True)
            write_json(run_dir / comparison_path, comparison)
            comparisons.append(comparison)
            if abort: break
        if abort: break
    final_inputs_stable = True
    for (case_id, variant_id), expected in input_snapshots.items():
        current = authoritative_inputs(
            experiment.cases[case_id], experiment.variants[variant_id]
        )
        current["experiment_sha256"] = sha256_file(experiment.path)
        current["judge_schema_sha256"] = sha256_file(
            experiment.root / "schemas/judge-output.schema.json"
        )
        current["codex_cli_version"] = _codex_version(fake)
        final_inputs_stable = final_inputs_stable and current == expected
    final_evaluator = evaluator_identity(experiment.root, require_clean=not fake)
    final_inputs_stable = final_inputs_stable and final_evaluator == evaluator
    manifest = {
        "schema_version": 1,
        "experiment_id": experiment.experiment_id,
        "experiment_sha256": next(iter(input_snapshots.values()))["experiment_sha256"],
        "variant_hashes": {
            variant_a: input_snapshots[
                (experiment.suites[suite][0], variant_a)
            ]["variant_sha256"],
            variant_b: input_snapshots[
                (experiment.suites[suite][0], variant_b)
            ]["variant_sha256"],
        },
        "case_hashes": {
            case_id: input_snapshots[(case_id, variant_a)]["case_definition_sha256"]
            for case_id in experiment.suites[suite]
        },
        "fixture_hashes": {
            case_id: input_snapshots[(case_id, variant_a)]["fixture_tree_sha256"]
            for case_id in experiment.suites[suite]
        },
        "wrapper_prompt_sha256": sha256_text(WRAPPER_PROMPT),
        "judge_schema_sha256": next(iter(input_snapshots.values()))[
            "judge_schema_sha256"
        ],
        **evaluator,
        "codex_cli_version": next(iter(input_snapshots.values()))[
            "codex_cli_version"
        ],
        "python_version": platform.python_version(),
        "os": platform.system(),
        "architecture": platform.machine(),
        "model": experiment.runner.model,
        "reasoning_effort": experiment.runner.reasoning_effort,
        "sandbox": experiment.runner.sandbox,
        "approval_policy": experiment.runner.approval_policy,
        "run_order_seed": experiment.run_order_seed,
        "suite": suite,
        "repeats": repeats,
        "start_timestamp": started,
        "end_timestamp": utc_now(),
        "run_count": len(run_records),
        "run_manifests": run_records,
        "frozen_inputs_stable": final_inputs_stable,
        "sealed_candidate": manifest_metadata,
    }
    manifest["invariant_sha256"] = sha256_text(
        json.dumps(
            {
                key: manifest[key]
                for key in (
                    "experiment_sha256",
                    "case_hashes",
                    "fixture_hashes",
                    "wrapper_prompt_sha256",
                    "judge_schema_sha256",
                    "evaluator_commit",
                    "evaluator_state_sha256",
                    "codex_cli_version",
                    "python_version",
                    "os",
                    "architecture",
                    "model",
                    "reasoning_effort",
                    "sandbox",
                    "approval_policy",
                    "run_order_seed",
                )
            },
            sort_keys=True,
        )
    )
    manifest["control_binding_sha256"] = sha256_text(
        json.dumps(
            {
                key: manifest[key]
                for key in (
                    "experiment_sha256",
                    "wrapper_prompt_sha256",
                    "judge_schema_sha256",
                    "evaluator_commit",
                    "evaluator_state_sha256",
                    "codex_cli_version",
                    "python_version",
                    "os",
                    "architecture",
                    "model",
                    "reasoning_effort",
                    "sandbox",
                    "approval_policy",
                    "run_order_seed",
                )
            },
            sort_keys=True,
        )
    )
    write_json(run_dir / "experiment-manifest.json", manifest)
    status = live_runner_status or ("LIVE_RUNNER_UNAVAILABLE" if fake else doctor(experiment).code)
    verdict = "NOT_RUN" if fake else (
        "INVALID_COMPARISON"
        if not final_inputs_stable or any(not item["valid"] for item in comparisons)
        else "INCONCLUSIVE"
    )
    report = build_report(
        mode="demo" if fake else "comparison",
        experiment_id=experiment.experiment_id,
        verdict=verdict,
        champion_hash=manifest["variant_hashes"][variant_a],
        candidate_hash=manifest["variant_hashes"][variant_b],
        candidate_id=variant_b if variant_b in experiment.candidate_ids else None,
        comparisons=comparisons,
        live_runner_status=status,
    )
    if write_default_report:
        write_report(run_dir, report)
    return run_dir, comparisons, manifest


def execute_variant_experiment(
    *,
    experiment: ExperimentConfig,
    runner: SubjectRunner,
    variant_id: str,
    suite: str,
    repeats: int,
    run_id: str | None = None,
) -> tuple[Path, list[dict[str, Any]], dict[str, Any]]:
    if repeats <= 0:
        raise ValueError("repeats must be positive")
    if suite not in experiment.suites or variant_id not in experiment.variants:
        raise ValueError("unknown suite or variant")
    evaluator = evaluator_identity(experiment.root, require_clean=True)
    run_dir = create_run_directory(experiment.root, run_id)
    redactor = Redactor(environment_secret_values())
    started = utc_now()
    input_snapshots = {
        case_id: freeze_inputs(
            experiment,
            experiment.cases[case_id],
            experiment.variants[variant_id],
            fake=False,
        )
        for case_id in experiment.suites[suite]
    }
    summaries: list[dict[str, Any]] = []
    for case_id in experiment.suites[suite]:
        case = experiment.cases[case_id]
        for replicate in range(1, repeats + 1):
            artifact = run_dir / "variants" / variant_id / case_id / str(replicate)
            summaries.append(
                execute_one(
                    experiment=experiment,
                    case=case,
                    variant_id=variant_id,
                    variant_path=experiment.variants[variant_id],
                    replicate=replicate,
                    artifact_dir=artifact,
                    runner=runner,
                    evaluator=evaluator,
                    fake=False,
                    redactor=redactor,
                    expected_inputs=input_snapshots[case_id],
                )
            )
    final_inputs_stable = True
    for case_id, expected in input_snapshots.items():
        current = authoritative_inputs(
            experiment.cases[case_id], experiment.variants[variant_id]
        )
        current["experiment_sha256"] = sha256_file(experiment.path)
        current["judge_schema_sha256"] = sha256_file(
            experiment.root / "schemas/judge-output.schema.json"
        )
        current["codex_cli_version"] = _codex_version(False)
        final_inputs_stable = final_inputs_stable and current == expected
    final_evaluator = evaluator_identity(experiment.root, require_clean=True)
    final_inputs_stable = final_inputs_stable and final_evaluator == evaluator
    manifest = {
        "schema_version": 1,
        "experiment_id": experiment.experiment_id,
        "experiment_sha256": next(iter(input_snapshots.values()))["experiment_sha256"],
        "variant_hashes": {
            variant_id: next(iter(input_snapshots.values()))["variant_sha256"]
        },
        "case_hashes": {
            case_id: input_snapshots[case_id]["case_definition_sha256"]
            for case_id in experiment.suites[suite]
        },
        "fixture_hashes": {
            case_id: input_snapshots[case_id]["fixture_tree_sha256"]
            for case_id in experiment.suites[suite]
        },
        "wrapper_prompt_sha256": sha256_text(WRAPPER_PROMPT),
        "judge_schema_sha256": next(iter(input_snapshots.values()))[
            "judge_schema_sha256"
        ],
        **evaluator,
        "codex_cli_version": next(iter(input_snapshots.values()))[
            "codex_cli_version"
        ],
        "python_version": platform.python_version(),
        "os": platform.system(),
        "architecture": platform.machine(),
        "model": experiment.runner.model,
        "reasoning_effort": experiment.runner.reasoning_effort,
        "sandbox": experiment.runner.sandbox,
        "approval_policy": experiment.runner.approval_policy,
        "run_order_seed": experiment.run_order_seed,
        "suite": suite,
        "repeats": repeats,
        "start_timestamp": started,
        "end_timestamp": utc_now(),
        "run_count": len(summaries),
        "run_manifests": [item["manifest"] for item in summaries],
        "frozen_inputs_stable": final_inputs_stable,
    }
    write_json(run_dir / "experiment-manifest.json", manifest)
    report = build_report(
        mode="single-variant",
        experiment_id=experiment.experiment_id,
        verdict="NOT_RUN",
        champion_hash=manifest["variant_hashes"][variant_id]
        if variant_id == "champion"
        else None,
        candidate_hash=manifest["variant_hashes"][variant_id]
        if variant_id != "champion"
        else None,
        candidate_id=variant_id if variant_id in experiment.candidate_ids else None,
        comparisons=[],
        live_runner_status=doctor(experiment).code,
    )
    report["single_variant_runs"] = summaries
    report["subject_run_count"] = len(summaries)
    write_report(run_dir, report)
    return run_dir, summaries, manifest
