"""JSON-ready and Markdown comparison reporting."""

from __future__ import annotations

from pathlib import Path
import statistics
from typing import Any

from .capture import write_json
from .compare import aggregate_by_case
from .promotion import REQUIRED_CASES


def build_report(
    *,
    mode: str,
    experiment_id: str,
    verdict: str,
    champion_hash: str | None,
    candidate_hash: str | None,
    comparisons: list[dict[str, Any]],
    aa_status: str = "NOT_RUN",
    bad_control_status: str = "NOT_RUN",
    live_runner_status: str = "LIVE_RUNNER_UNAVAILABLE",
    promotion: dict[str, Any] | None = None,
    live_evidence_complete: bool = False,
    runtime_model: str = "gpt-5.6-sol",
    runtime_reasoning_effort: str = "high",
) -> dict[str, Any]:
    hard_regressions = (promotion or {}).get("hard_regressions", [])
    targeted = (promotion or {}).get(
        "targeted_replicate_results", {"wins": 0, "losses": 0, "ties": 0, "count": 0}
    )
    holdout = [item for item in comparisons if item.get("suite") == "holdout"]
    holdout_outcome = "NOT_RUN"
    if holdout:
        holdout_outcome = (
            "HARD_REGRESSION"
            if any(
                item["champion"]["mechanical"].get("hard_pass")
                and not item["candidate"]["mechanical"].get("hard_pass")
                for item in holdout
            )
            else "NO_HARD_REGRESSION"
        )
    champion_tokens = [
        item["champion"].get("usage", {}).get("total_tokens", 0)
        for item in comparisons
    ]
    candidate_tokens = [
        item["candidate"].get("usage", {}).get("total_tokens", 0)
        for item in comparisons
    ]
    champion_durations = [
        item["champion"].get("duration_seconds", 0) for item in comparisons
    ]
    candidate_durations = [
        item["candidate"].get("duration_seconds", 0) for item in comparisons
    ]
    champion_median_tokens = (
        statistics.median(champion_tokens) if champion_tokens else 0
    )
    candidate_median_tokens = (
        statistics.median(candidate_tokens) if candidate_tokens else 0
    )
    median_token_ratio = (
        candidate_median_tokens / champion_median_tokens
        if champion_median_tokens
        else (1.0 if candidate_median_tokens == 0 else None)
    )
    return {
        "schema_version": 1,
        "mode": mode,
        "experiment_id": experiment_id,
        "verdict": verdict,
        "live_runner_status": live_runner_status,
        "quality_claim_established": mode == "candidate-comparison"
        and live_runner_status == "LIVE_RUNNER_AVAILABLE"
        and live_evidence_complete
        and REQUIRED_CASES <= {item["case_id"] for item in comparisons}
        and verdict in {"PROMOTE", "REJECT", "INCONCLUSIVE"},
        "aa_calibration": aa_status,
        "bad_control_validation": bad_control_status,
        "variant_hashes": {
            "champion": champion_hash,
            "candidate": candidate_hash,
        },
        "baseline_metadata": {
            "champion_declared_model": "GPT-5.5",
            "champion_declared_reasoning_effort": "xhigh",
            "experiment_runtime_model": runtime_model,
            "experiment_runtime_reasoning_effort": runtime_reasoning_effort,
            "mismatch_preserved": (
                runtime_model != "GPT-5.5"
                or runtime_reasoning_effort != "xhigh"
            ),
            "note": (
                "The source champion declares GPT-5.5 @ xhigh; the experiment "
                "runtime is pinned separately and the source baseline is unchanged."
            ),
        },
        "case_count": len({item["case_id"] for item in comparisons}),
        "comparison_count": len(comparisons),
        "subject_run_count": len(comparisons) * 2,
        "hard_regressions": hard_regressions,
        "targeted_replicate_results": targeted,
        "holdout_outcome": holdout_outcome,
        "token_duration_comparison": {
            "total_tokens": {
                "champion": sum(champion_tokens),
                "candidate": sum(candidate_tokens),
            },
            "median_duration_seconds": {
                "champion": statistics.median(champion_durations)
                if champion_durations
                else 0,
                "candidate": statistics.median(candidate_durations)
                if candidate_durations
                else 0,
            },
            "median_total_tokens": {
                "champion": champion_median_tokens,
                "candidate": candidate_median_tokens,
                "ratio": median_token_ratio,
                "within_25_percent_gate": median_token_ratio is not None
                and median_token_ratio <= 1.25,
            },
        },
        "case_aggregation": aggregate_by_case(comparisons) if comparisons else {},
        "comparisons": comparisons,
        "promotion": promotion,
    }


def _hard_label(side: dict[str, Any]) -> str:
    mechanical = side.get("mechanical", {})
    return "PASS" if mechanical.get("hard_pass") else "FAIL"


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        f"# MD Eval report: {report['experiment_id']}",
        "",
        f"VERDICT: {report['verdict']}",
        report["live_runner_status"],
    ]
    if not report.get("quality_claim_established"):
        lines.append("No claim about CODER.md quality has been established.")
    lines.extend(
        [
            "",
            f"- A/A calibration: {report['aa_calibration']}",
            f"- Bad-control validation: {report['bad_control_validation']}",
            f"- Champion SHA-256: `{report['variant_hashes'].get('champion')}`",
            f"- Candidate SHA-256: `{report['variant_hashes'].get('candidate')}`",
            (
                "- Baseline metadata: champion declares "
                f"`{report['baseline_metadata']['champion_declared_model']} @ "
                f"{report['baseline_metadata']['champion_declared_reasoning_effort']}`; "
                "experiment runtime is "
                f"`{report['baseline_metadata']['experiment_runtime_model']} @ "
                f"{report['baseline_metadata']['experiment_runtime_reasoning_effort']}` "
                "(mismatch preserved; champion source unchanged)"
            ),
            f"- Cases: {report['case_count']}",
            f"- Paired replicates: {report['comparison_count']}",
            f"- Subject runs: {report['subject_run_count']}",
            f"- Hard regressions: {len(report['hard_regressions'])}",
            f"- Holdout outcome: {report['holdout_outcome']}",
            (
                "- Total tokens (champion / candidate): "
                f"{report['token_duration_comparison']['total_tokens']['champion']} / "
                f"{report['token_duration_comparison']['total_tokens']['candidate']}"
            ),
            (
                "- Median duration seconds (champion / candidate): "
                f"{report['token_duration_comparison']['median_duration_seconds']['champion']:.3f} / "
                f"{report['token_duration_comparison']['median_duration_seconds']['candidate']:.3f}"
            ),
            (
                "- Median total-token ratio (candidate / champion): "
                f"{report['token_duration_comparison']['median_total_tokens']['ratio']} "
                "(25% gate: "
                f"{'PASS' if report['token_duration_comparison']['median_total_tokens']['within_25_percent_gate'] else 'REVIEW'})"
            ),
            (
                "- Targeted replicate results: "
                f"{report['targeted_replicate_results'].get('wins', 0)} wins / "
                f"{report['targeted_replicate_results'].get('losses', 0)} losses / "
                f"{report['targeted_replicate_results'].get('ties', 0)} ties"
            ),
            "",
            "| Case | Champion hard result | Candidate hard result | Mechanical delta | Qualitative result | Tokens | Duration | Evidence path |",
            "| --- | --- | --- | ---: | --- | ---: | ---: | --- |",
        ]
    )
    case_ids = sorted({item["case_id"] for item in report["comparisons"]})
    for case_id in case_ids:
        items = [item for item in report["comparisons"] if item["case_id"] == case_id]
        champion_passes = sum(
            bool(item["champion"]["mechanical"].get("hard_pass")) for item in items
        )
        candidate_passes = sum(
            bool(item["candidate"]["mechanical"].get("hard_pass")) for item in items
        )
        delta = statistics.fmean(
            item["candidate"]["mechanical"].get("mechanical_score", 0)
            - item["champion"]["mechanical"].get("mechanical_score", 0)
            for item in items
        )
        wins = sum(item.get("qualitative_winner") == "candidate" for item in items)
        losses = sum(item.get("qualitative_winner") == "champion" for item in items)
        ties = sum(item.get("qualitative_winner") == "TIE" for item in items)
        token_text = (
            f"{sum(item['champion'].get('usage', {}).get('total_tokens', 0) for item in items)} / "
            f"{sum(item['candidate'].get('usage', {}).get('total_tokens', 0) for item in items)}"
        )
        duration_text = (
            f"{statistics.median(item['champion'].get('duration_seconds', 0) for item in items):.3f} / "
            f"{statistics.median(item['candidate'].get('duration_seconds', 0) for item in items):.3f}"
        )
        evidence_links = [
            f"[r{item['replicate']}]({item['evidence_path']})"
            for item in items
            if item.get("evidence_path")
        ]
        evidence_link = "<br>".join(evidence_links) if evidence_links else "—"
        lines.append(
            f"| {case_id} ({len(items)} reps) | {champion_passes}/{len(items)} PASS | "
            f"{candidate_passes}/{len(items)} PASS | {delta:+.1f} | "
            f"{wins}W/{losses}L/{ties}T | {token_text} | "
            f"{duration_text} | {evidence_link} |"
        )
    lines.append("")
    raw_rows: list[str] = []
    for item in report["comparisons"]:
        raw = item.get("raw_artifact_paths", {})
        for side in ("champion", "candidate"):
            links = raw.get(side, {})
            if isinstance(links, dict) and links:
                rendered = ", ".join(
                    f"[{name}]({path})" for name, path in sorted(links.items())
                )
                raw_rows.append(
                    f"- `{item['case_id']}` replicate {item['replicate']} "
                    f"{side}: {rendered}"
                )
    if raw_rows:
        lines.extend(["## Raw run artifacts", "", *raw_rows, ""])
    lines.append(
        "Mechanical hard failures remain visible and are never overridden by qualitative judgment."
    )
    return "\n".join(lines) + "\n"


def write_report(run_dir: Path, report: dict[str, Any]) -> None:
    write_json(run_dir / "report.json", report)
    (run_dir / "report.md").write_text(render_markdown(report), encoding="utf-8")
