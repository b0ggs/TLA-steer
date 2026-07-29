"""Command-line interface for MD Eval."""

from __future__ import annotations

import argparse
import json
import os
import sys
from dataclasses import replace
from pathlib import Path
from typing import Any, Sequence

from .capture import Redactor, write_json
from .compare import (
    classify_bad_control_failure,
    evaluate_aa,
    evaluate_bad_control,
)
from .config import ConfigError, ExperimentConfig, load_experiment
from .execution import (
    current_control_context,
    execute_pair_experiment,
    execute_variant_experiment,
    manifest_matches_authoritative,
)
from .hashing import sha256_file
from .promotion import evaluate_promotion
from .report import build_report, write_report
from .runner.codex_cli import CodexCLI, doctor, live_smoke
from .runner.fake import FakeAdapter, FakePlan


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="mdseval")
    subparsers = parser.add_subparsers(dest="command", required=True)

    def add_experiment(command: argparse.ArgumentParser) -> None:
        command.add_argument(
            "--experiment", default="experiments/coder-v1.json", type=Path
        )

    validate = subparsers.add_parser("validate", help="validate all offline inputs")
    add_experiment(validate)

    diagnose = subparsers.add_parser("doctor", help="diagnose the live Codex runner")
    add_experiment(diagnose)
    diagnose.add_argument("--runner", choices=("codex",), default="codex")
    diagnose.add_argument("--live-smoke", action="store_true")

    demo = subparsers.add_parser("demo", help="run deterministic fake plumbing")
    add_experiment(demo)
    demo.add_argument("--run-id")

    run = subparsers.add_parser("run", help="run one live variant")
    add_experiment(run)
    run.add_argument("--variant", required=True)
    run.add_argument("--suite", default="smoke")
    run.add_argument("--repeats", type=int, default=1)
    run.add_argument("--run-id")

    calibrate = subparsers.add_parser("calibrate", help="run live A/A calibration")
    add_experiment(calibrate)
    calibrate.add_argument("--suite", default="dev")
    calibrate.add_argument("--repeats", type=int)
    calibrate.add_argument("--run-id")

    compare = subparsers.add_parser("compare", help="run a live pairwise comparison")
    add_experiment(compare)
    compare.add_argument("--variant-a", required=True)
    compare.add_argument("--variant-b", required=True)
    compare.add_argument("--suite", default="dev")
    compare.add_argument("--repeats", type=int)
    compare.add_argument("--seal-candidate", action="store_true")
    compare.add_argument("--run-id")
    return parser


def _print_json(value: Any) -> None:
    print(json.dumps(value, indent=2, sort_keys=True))


def _evidence_path(experiment: ExperimentConfig) -> Path:
    reports_root = experiment.root / "reports"
    if reports_root.is_symlink() or not reports_root.is_dir():
        raise RuntimeError("reports must be a real directory")
    try:
        reports_root.resolve().relative_to(experiment.root.resolve())
    except ValueError as exc:
        raise RuntimeError("reports directory escapes evaluator root") from exc
    path = reports_root / "evidence-index.json"
    if path.is_symlink():
        raise RuntimeError("evidence index must not be a symlink")
    try:
        path.resolve().relative_to(reports_root.resolve())
    except ValueError as exc:
        raise RuntimeError("evidence index escapes reports root") from exc
    return path


def _load_evidence(experiment: ExperimentConfig) -> list[dict[str, Any]]:
    path = _evidence_path(experiment)
    if not path.is_file():
        return []
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise RuntimeError(f"invalid evidence index: {exc}") from exc
    return value if isinstance(value, list) else []


def _record_evidence(experiment: ExperimentConfig, entry: dict[str, Any]) -> None:
    entries = _load_evidence(experiment)
    entries.append(entry)
    write_json(_evidence_path(experiment), entries)


def _latest_evidence(
    experiment: ExperimentConfig,
    kind: str,
    binding_hash: str,
) -> dict[str, Any] | None:
    candidates = [
        item
        for item in _load_evidence(experiment)
        if item.get("kind") == kind
        and item.get("invariant_hash") == binding_hash
        and item.get("experiment_sha256") == sha256_file(experiment.path)
    ]
    if not candidates:
        return None
    item = candidates[-1]
    report_path = Path(item.get("report_path", ""))
    manifest_path = Path(item.get("manifest_path", ""))
    try:
        report_path.resolve().relative_to((experiment.root / "runs").resolve())
        manifest_path.resolve().relative_to((experiment.root / "runs").resolve())
    except (ValueError, OSError):
        return None
    if (
        not report_path.is_file()
        or not manifest_path.is_file()
        or sha256_file(report_path) != item.get("report_sha256")
        or sha256_file(manifest_path) != item.get("manifest_sha256")
    ):
        return None
    report = json.loads(report_path.read_text(encoding="utf-8"))
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if kind == "aa":
        derived_passed = bool(report.get("aa_result", {}).get("passed"))
        expected_repeats = experiment.default_repeats
    else:
        derived_passed = bool(report.get("bad_control_result", {}).get("passed"))
        expected_repeats = 1
    if (
        derived_passed != item.get("passed")
        or item.get("suite") != "dev"
        or item.get("repeats") != expected_repeats
        or tuple(item.get("case_ids", ())) != experiment.suites["dev"]
        or manifest.get("control_binding_sha256") != item.get("invariant_hash")
        or manifest.get("evaluator_state_sha256") != item.get("evaluator_hash")
        or manifest.get("suite") != "dev"
        or manifest.get("repeats") != expected_repeats
        or set(manifest.get("case_hashes", ())) != set(experiment.suites["dev"])
    ):
        return None
    return item


def _report_entry(
    kind: str,
    run_dir: Path,
    manifest: dict[str, Any],
    passed: bool,
    **extra: Any,
) -> dict[str, Any]:
    return {
        "schema_version": 1,
        "kind": kind,
        "passed": passed,
        "evaluator_hash": manifest["evaluator_state_sha256"],
        "invariant_hash": manifest["control_binding_sha256"],
        "experiment_sha256": manifest["experiment_sha256"],
        "report_path": str(run_dir / "report.json"),
        "report_sha256": sha256_file(run_dir / "report.json"),
        "manifest_path": str(run_dir / "experiment-manifest.json"),
        "manifest_sha256": sha256_file(run_dir / "experiment-manifest.json"),
        "end_timestamp": manifest["end_timestamp"],
        **extra,
    }


def _demo_plans() -> dict[str, FakePlan]:
    return {
        "ambiguity-must-clarify": FakePlan(
            final_text=(
                "NEEDS_CLARIFICATION\nShould the approved compact duration format "
                "be `1h 05m` or `1:05`?\n"
            )
        ),
        "bug-reproduce-mutable-default": FakePlan(
            events=(
                {
                    "type": "command",
                    "command": "python3 -m unittest tests.test_tags",
                    "exit_code": 1,
                },
                {"type": "file_change", "paths": ["src/tags.py"]},
                {
                    "type": "command",
                    "command": "python3 -m unittest tests.test_tags",
                    "exit_code": 0,
                },
            )
        ),
    }


def _require_live(experiment: ExperimentConfig) -> None:
    result = doctor(experiment)
    if not result.available:
        raise RuntimeError(result.code)


def _command_validate(experiment: ExperimentConfig) -> int:
    print(
        f"VALID: {experiment.experiment_id}; "
        f"{len(experiment.cases)} cases; {len(experiment.variants)} variants"
    )
    return 0


def _command_doctor(experiment: ExperimentConfig, live: bool) -> int:
    result = doctor(experiment)
    payload = {
        "status": result.code,
        "checks": result.checks,
        "command": list(result.command),
        "model_call_made": bool(live and result.available),
    }
    live_allowed = result.available
    smoke_succeeded = False
    if live and live_allowed:
        smoke = live_smoke(experiment, redactor=Redactor())
        payload["live_smoke"] = {
            "status": smoke.status,
            "exit_code": smoke.exit_code,
            "duration_seconds": smoke.duration_seconds,
        }
        smoke_succeeded = smoke.status == "COMPLETED" and smoke.exit_code == 0
        payload["status"] = (
            "LIVE_RUNNER_AVAILABLE"
            if smoke_succeeded
            else "LIVE_RUNNER_UNAVAILABLE"
        )
        payload["model_call_made"] = True
    _print_json(payload)
    return 0 if result.available and (not live or smoke_succeeded) else 1


def _command_demo(experiment: ExperimentConfig, run_id: str | None) -> int:
    run_dir, _, _ = execute_pair_experiment(
        experiment=experiment,
        runner=FakeAdapter(_demo_plans()),
        variant_a="champion",
        variant_b="karpathy-v1",
        suite="smoke",
        repeats=1,
        fake=True,
        run_id=run_id,
        run_judge=False,
    )
    print(f"DEMO_COMPLETE: {run_dir}")
    print("VERDICT: NOT_RUN")
    print("LIVE_RUNNER_UNAVAILABLE")
    print("No claim about CODER.md quality has been established.")
    return 0


def _command_run(
    experiment: ExperimentConfig,
    variant: str,
    suite: str,
    repeats: int,
    run_id: str | None,
) -> int:
    _require_live(experiment)
    run_dir, summaries, manifest = execute_variant_experiment(
        experiment=experiment,
        runner=CodexCLI(experiment.runner),
        variant_id=variant,
        suite=suite,
        repeats=repeats,
        run_id=run_id,
    )
    if (
        not manifest.get("frozen_inputs_stable")
        or not manifest_matches_authoritative(experiment, manifest, fake=False)
        or any(
            item["status"] != "COMPLETED"
            or item["exit_code"] != 0
            or not item["valid_event_stream"]
            for item in summaries
        )
    ):
        print(f"RUNNER_FAILURE: {run_dir}")
        return 1
    print(f"RUN_COMPLETE: {run_dir}")
    return 0


def _command_calibrate(
    experiment: ExperimentConfig,
    suite: str,
    repeats: int,
    run_id: str | None,
) -> int:
    if suite != "dev" or repeats != experiment.default_repeats:
        raise ValueError("A/A calibration requires the locked dev suite and default repeats")
    _require_live(experiment)
    aliases = {
        **experiment.variants,
        "champion-aa-a": experiment.variants["champion"],
        "champion-aa-b": experiment.variants["champion"],
    }
    aa_experiment = replace(experiment, variants=aliases)
    run_dir, comparisons, manifest = execute_pair_experiment(
        experiment=aa_experiment,
        runner=CodexCLI(experiment.runner),
        variant_a="champion-aa-a",
        variant_b="champion-aa-b",
        artifact_variant_a="champion-aa-a",
        artifact_variant_b="champion-aa-b",
        suite=suite,
        repeats=repeats,
        fake=False,
        run_id=run_id,
        write_default_report=False,
    )
    side_a = [item["champion"]["mechanical"] for item in comparisons]
    side_b = [item["candidate"]["mechanical"] for item in comparisons]
    runners_healthy = bool(
        manifest.get("frozen_inputs_stable")
        and manifest_matches_authoritative(aa_experiment, manifest, fake=False)
        and all(item["valid"] for item in comparisons)
        and all(
            side["status"] == "COMPLETED"
            and side["exit_code"] == 0
            and side["valid_event_stream"]
            for item in comparisons
            for side in (item["champion"], item["candidate"])
        )
    )
    judges_complete = all(
        item.get("judge_output") is not None and item.get("qualitative_status") == "COMPLETED"
        for item in comparisons
    )
    winners = [
        item["judge_output"]["winner"]
        for item in comparisons
        if item.get("judge_output") is not None
    ]
    result = evaluate_aa(side_a, side_b, winners)
    if not runners_healthy or not judges_complete or len(winners) != len(comparisons):
        result["passed"] = False
        result["status"] = "EVALUATOR_NOT_CALIBRATED"
        result["evidence_complete"] = False
    report = build_report(
        mode="calibration",
        experiment_id=experiment.experiment_id,
        verdict="INCONCLUSIVE",
        champion_hash=manifest["variant_hashes"]["champion-aa-a"],
        candidate_hash=manifest["variant_hashes"]["champion-aa-b"],
        comparisons=comparisons,
        aa_status=result["status"],
        live_runner_status="LIVE_RUNNER_AVAILABLE",
        live_evidence_complete=runners_healthy and judges_complete,
    )
    report["aa_result"] = result
    write_report(run_dir, report)
    _record_evidence(
        experiment,
        _report_entry(
            "aa",
            run_dir,
            manifest,
            result["passed"],
            suite=suite,
            repeats=repeats,
            case_ids=list(experiment.suites[suite]),
        ),
    ) if manifest_matches_authoritative(aa_experiment, manifest, fake=False) else None
    print(f"{result['status']}: {run_dir}")
    return 0 if result["passed"] else 1


def _comparison_controls(
    experiment: ExperimentConfig, manifest: dict[str, Any]
) -> tuple[dict[str, Any] | None, dict[str, Any] | None]:
    binding = manifest["control_binding_sha256"]
    return (
        _latest_evidence(experiment, "aa", binding),
        _latest_evidence(experiment, "bad_control", binding),
    )


def _bad_control_winners(comparisons: list[dict[str, Any]]) -> list[str]:
    return [
        "deliberately-bad"
        if item["qualitative_winner"] == "candidate"
        else item["qualitative_winner"]
        for item in comparisons
    ]


def _load_prior_dev(
    experiment: ExperimentConfig,
    candidate_hash: str,
    binding_hash: str | None,
    current_run_dir: Path | None,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    entries = [
        item
        for item in _load_evidence(experiment)
        if item.get("kind") == "candidate_dev"
        and item.get("completed")
    ]
    if not entries:
        raise RuntimeError(
            "--seal-candidate requires a completed development comparison with the same candidate hash"
        )
    entry = entries[-1]
    if entry.get("candidate_hash") != candidate_hash:
        raise RuntimeError("most recent development comparison has a different candidate hash")
    if binding_hash is not None and entry.get("invariant_hash") != binding_hash:
        raise RuntimeError("development comparison invariant binding does not match")
    report_path = Path(entry["report_path"])
    manifest_path = Path(entry.get("manifest_path", ""))
    runs_root = (experiment.root / "runs").resolve()
    try:
        report_path.resolve().relative_to(runs_root)
        manifest_path.resolve().relative_to(runs_root)
    except (ValueError, OSError) as exc:
        raise RuntimeError("sealed development evidence escapes runs root") from exc
    if (
        not report_path.is_file()
        or not manifest_path.is_file()
        or sha256_file(report_path) != entry["report_sha256"]
        or sha256_file(manifest_path) != entry.get("manifest_sha256")
        or entry.get("suite") != "dev"
        or entry.get("repeats") != experiment.default_repeats
        or tuple(entry.get("case_ids", ())) != experiment.suites["dev"]
    ):
        raise RuntimeError("sealed development report hash mismatch")
    report = json.loads(report_path.read_text(encoding="utf-8"))
    prior_manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if (
        prior_manifest.get("variant_hashes", {}).get("karpathy-v1")
        != candidate_hash
        or prior_manifest.get("experiment_sha256")
        != entry.get("experiment_sha256")
        or prior_manifest.get("control_binding_sha256")
        != entry.get("invariant_hash")
        or prior_manifest.get("evaluator_state_sha256")
        != entry.get("evaluator_hash")
        or report.get("variant_hashes", {}).get("candidate") != candidate_hash
    ):
        raise RuntimeError("sealed development manifest lineage mismatch")
    comparisons = report.get("comparisons", [])
    expected_pairs = len(experiment.suites["dev"]) * experiment.default_repeats
    expected_replicates = {
        (case_id, replicate)
        for case_id in experiment.suites["dev"]
        for replicate in range(1, experiment.default_repeats + 1)
    }
    actual_replicates = {
        (item.get("case_id"), item.get("replicate")) for item in comparisons
    }
    evidence_complete = bool(
        report.get("aa_calibration") == "PASSED"
        and report.get("bad_control_validation") == "PASSED"
        and len(comparisons) == expected_pairs
        and actual_replicates == expected_replicates
        and all(
            item.get("valid")
            and item.get("qualitative_status") == "COMPLETED"
            and item.get("judge_output") is not None
            and all(
                side.get("status") == "COMPLETED"
                and side.get("exit_code") == 0
                and side.get("valid_event_stream")
                for side in (item.get("champion", {}), item.get("candidate", {}))
            )
            for item in comparisons
        )
    )
    if not evidence_complete:
        raise RuntimeError("sealed development comparison has incomplete live evidence")
    prior_run_dir = report_path.parent
    if current_run_dir is not None:
        for comparison in comparisons:
            evidence = comparison.get("evidence_path")
            if evidence:
                comparison["evidence_path"] = os.path.relpath(
                    prior_run_dir / evidence, current_run_dir
                )
            for paths in comparison.get("raw_artifact_paths", {}).values():
                if isinstance(paths, dict):
                    for name, path in paths.items():
                        paths[name] = os.path.relpath(
                            prior_run_dir / path, current_run_dir
                        )
    return comparisons, entry


def _command_compare(
    experiment: ExperimentConfig,
    variant_a: str,
    variant_b: str,
    suite: str,
    repeats: int,
    seal_candidate: bool,
    run_id: str | None,
) -> int:
    if variant_a != "champion" or variant_b not in {
        "karpathy-v1",
        "deliberately-bad",
    }:
        raise ValueError("supported comparisons require champion as variant-a")
    if variant_b == "deliberately-bad":
        if suite != "dev" or repeats != 1 or seal_candidate:
            raise ValueError("bad-control validation requires dev, one repeat, and no seal")
    else:
        if suite == "dev" and (
            repeats != experiment.default_repeats or seal_candidate
        ):
            raise ValueError("candidate development comparison requires default repeats and no seal")
        if suite == "holdout" and (
            repeats != experiment.default_repeats or not seal_candidate
        ):
            raise ValueError("candidate holdout requires default repeats and --seal-candidate")
        if suite not in {"dev", "holdout"}:
            raise ValueError("candidate comparison supports only locked dev or holdout suites")
    candidate_hash = (
        sha256_file(experiment.variants[variant_b])
        if variant_b == "karpathy-v1"
        else None
    )
    preflight_aa = preflight_bad = None
    if variant_b == "karpathy-v1":
        _, preflight_binding = current_control_context(experiment)
        preflight_aa = _latest_evidence(experiment, "aa", preflight_binding)
        preflight_bad = _latest_evidence(experiment, "bad_control", preflight_binding)
        if not preflight_aa or not preflight_aa.get("passed"):
            raise RuntimeError("passing A/A evidence is required before candidate execution")
        if not preflight_bad or not preflight_bad.get("passed"):
            raise RuntimeError("passing bad-control evidence is required before candidate execution")
    sealed_entry = None
    if seal_candidate:
        _, sealed_entry = _load_prior_dev(
            experiment, candidate_hash or "", preflight_binding, None
        )
    _require_live(experiment)
    if seal_candidate and (variant_b != "karpathy-v1" or suite != "holdout"):
        raise ValueError("--seal-candidate is only valid for karpathy-v1 holdout")
    run_dir, comparisons, manifest = execute_pair_experiment(
        experiment=experiment,
        runner=CodexCLI(experiment.runner),
        variant_a=variant_a,
        variant_b=variant_b,
        suite=suite,
        repeats=repeats,
        fake=False,
        run_id=run_id,
        write_default_report=False,
        manifest_metadata=(
            {
                "candidate_sha256": candidate_hash,
                "source_report_path": sealed_entry["report_path"],
                "source_report_sha256": sealed_entry["report_sha256"],
                "source_manifest_path": sealed_entry["manifest_path"],
                "source_manifest_sha256": sealed_entry["manifest_sha256"],
            }
            if sealed_entry
            else None
        ),
    )
    runners_healthy = bool(
        manifest.get("frozen_inputs_stable")
        and manifest_matches_authoritative(experiment, manifest, fake=False)
        and all(item["valid"] for item in comparisons)
        and all(
            side["status"] == "COMPLETED"
            and side["exit_code"] == 0
            and side["valid_event_stream"]
            for item in comparisons
            for side in (item["champion"], item["candidate"])
        )
    )
    judges_complete = all(
        item.get("judge_output") is not None and item.get("qualitative_status") == "COMPLETED"
        for item in comparisons
    )
    if (
        not manifest.get("frozen_inputs_stable")
        or not manifest_matches_authoritative(experiment, manifest, fake=False)
        or any(not item["valid"] for item in comparisons)
    ):
        verdict = "INVALID_COMPARISON"
        result: dict[str, Any] = {
            "verdict": verdict,
            "reasons": ["comparison invariant mismatch"],
        }
        aa_entry = preflight_aa
        bad_entry = preflight_bad
    elif variant_b == "deliberately-bad":
        failure_classes: set[str] = set()
        for item in comparisons:
            failure_classes |= classify_bad_control_failure(
                item["case_id"],
                experiment.cases[item["case_id"]].expected_disposition,
                item["candidate"],
            )
        control = evaluate_bad_control(
            [item["champion"]["mechanical"] for item in comparisons],
            [item["candidate"]["mechanical"] for item in comparisons],
            _bad_control_winners(comparisons),
            failure_classes,
        )
        if not runners_healthy or not judges_complete:
            control["passed"] = False
            control["status"] = "EVALUATOR_BAD_CONTROL_FAILED"
            control["evidence_complete"] = False
        verdict = "INCONCLUSIVE"
        result = {"verdict": verdict, "bad_control_result": control}
        aa_entry = None
        bad_entry = control
    else:
        candidate_hash = manifest["variant_hashes"][variant_b]
        if seal_candidate:
            prior_comparisons, confirmed_entry = _load_prior_dev(
                experiment,
                candidate_hash,
                manifest["control_binding_sha256"],
                run_dir,
            )
            if confirmed_entry != sealed_entry:
                raise RuntimeError("sealed development evidence changed during holdout")
            comparisons = prior_comparisons + comparisons
        aa_entry, bad_entry = _comparison_controls(experiment, manifest)
        if aa_entry != preflight_aa or bad_entry != preflight_bad:
            raise RuntimeError("control evidence changed during candidate comparison")
        control_evidence = {
            "comparison": {
                "invariant_hash": manifest["control_binding_sha256"],
            },
            "aa": aa_entry or {},
            "bad_control": bad_entry or {},
        }
        correctness_gains = sorted(
            {
                item["case_id"]
                for item in comparisons
                if not item["champion"]["mechanical"]["hard_pass"]
                and item["candidate"]["mechanical"]["hard_pass"]
            }
        )
        token_justification = (
            {
                "correctness_gain": (
                    "Candidate hard-passed cases where the champion did not."
                ),
                "evidence": correctness_gains,
            }
            if correctness_gains
            else None
        )
        result = evaluate_promotion(
            comparisons,
            aa_passed=bool(aa_entry and aa_entry["passed"]),
            bad_control_passed=bool(bad_entry and bad_entry["passed"]),
            evaluator_hash=manifest["evaluator_state_sha256"],
            control_evidence=control_evidence,
            expected_repeats=experiment.default_repeats,
            token_increase_justification=token_justification,
        )
        verdict = result["verdict"]
    report = build_report(
        mode="bad-control" if variant_b == "deliberately-bad" else "candidate-comparison",
        experiment_id=experiment.experiment_id,
        verdict=verdict,
        champion_hash=manifest["variant_hashes"][variant_a],
        candidate_hash=manifest["variant_hashes"][variant_b],
        comparisons=comparisons,
        aa_status="PASSED" if aa_entry and aa_entry.get("passed") else "NOT_RUN",
        bad_control_status=(
            bad_entry.get("status", "PASSED")
            if isinstance(bad_entry, dict)
            else "NOT_RUN"
        ),
        live_runner_status="LIVE_RUNNER_AVAILABLE",
        live_evidence_complete=runners_healthy and judges_complete,
        promotion=result if "verdict" in result else None,
    )
    if variant_b == "deliberately-bad" and "bad_control_result" in result:
        report["bad_control_result"] = result["bad_control_result"]
    write_report(run_dir, report)
    if variant_b == "deliberately-bad" and "bad_control_result" in result:
        control = result["bad_control_result"]
        if not manifest_matches_authoritative(experiment, manifest, fake=False):
            print("EVALUATOR_BAD_CONTROL_FAILED: frozen inputs drifted")
            return 1
        _record_evidence(
            experiment,
            _report_entry(
                "bad_control", run_dir, manifest, control["passed"], status=control["status"]
                , suite=suite, repeats=repeats, case_ids=list(experiment.suites[suite])
            ),
        )
        print(f"{control['status']}: {run_dir}")
        return 0 if control["passed"] and runners_healthy and judges_complete else 1
    if variant_b == "deliberately-bad":
        print(f"VERDICT: {verdict}\nREPORT: {run_dir / 'report.md'}")
        return 1
    if (
        suite == "dev"
        and variant_b == "karpathy-v1"
        and runners_healthy
        and judges_complete
        and all(item["valid"] for item in comparisons)
    ):
        if not manifest_matches_authoritative(experiment, manifest, fake=False):
            print("VERDICT: INVALID_COMPARISON")
            return 1
        _record_evidence(
            experiment,
            _report_entry(
                "candidate_dev",
                run_dir,
                manifest,
                passed=True,
                completed=True,
                candidate_hash=manifest["variant_hashes"][variant_b],
                suite=suite,
                repeats=repeats,
                case_ids=list(experiment.suites[suite]),
            ),
        )
    print(f"VERDICT: {verdict}\nREPORT: {run_dir / 'report.md'}")
    return 1 if verdict == "INVALID_COMPARISON" or not runners_healthy else 0


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        experiment = load_experiment(args.experiment)
        if args.command == "validate":
            return _command_validate(experiment)
        if args.command == "doctor":
            return _command_doctor(experiment, args.live_smoke)
        if args.command == "demo":
            return _command_demo(experiment, args.run_id)
        if args.command == "run":
            return _command_run(
                experiment, args.variant, args.suite, args.repeats, args.run_id
            )
        if args.command == "calibrate":
            return _command_calibrate(
                experiment,
                args.suite,
                experiment.default_repeats if args.repeats is None else args.repeats,
                args.run_id,
            )
        if args.command == "compare":
            return _command_compare(
                experiment,
                args.variant_a,
                args.variant_b,
                args.suite,
                experiment.default_repeats if args.repeats is None else args.repeats,
                args.seal_candidate,
                args.run_id,
            )
        raise AssertionError("unreachable")
    except (ConfigError, ValueError, RuntimeError, FileExistsError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
