"""Comparison invariants, evaluator controls, and deterministic aggregation."""

from __future__ import annotations

import hashlib
import json
import math
import statistics
from collections import defaultdict
from pathlib import Path
from typing import Any

FROZEN_PAIR_FIELDS = (
    "experiment_sha256",
    "case_definition_sha256",
    "fixture_tree_sha256",
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

BAD_CONTROL_CLASSES = frozenset(
    {
        "unnecessary_clarification",
        "overengineering",
        "drive_by_cleanup",
        "missing_reproduction",
        "false_completion",
    }
)


def invariant_mismatches(
    left: dict[str, Any], right: dict[str, Any]
) -> dict[str, tuple[Any, Any]]:
    mismatches: dict[str, tuple[Any, Any]] = {}
    for field in FROZEN_PAIR_FIELDS:
        if field not in left or field not in right or left.get(field) != right.get(field):
            mismatches[field] = (left.get(field), right.get(field))
    return mismatches


def comparison_is_valid(left: dict[str, Any], right: dict[str, Any]) -> bool:
    return not invariant_mismatches(left, right)


def deterministic_pair_order(
    seed: int, case_id: str, replicate: int, variant_a: str, variant_b: str
) -> tuple[str, str]:
    digest = hashlib.sha256(f"{seed}:{case_id}:{replicate}".encode("utf-8")).digest()
    return (variant_a, variant_b) if digest[0] % 2 == 0 else (variant_b, variant_a)


def _two_sided_binomial_p_value(a_wins: int, decisive_count: int) -> float:
    if decisive_count == 0:
        return 1.0
    denominator = 2**decisive_count
    lower = sum(
        math.comb(decisive_count, count) for count in range(a_wins + 1)
    ) / denominator
    upper = sum(
        math.comb(decisive_count, count)
        for count in range(a_wins, decisive_count + 1)
    ) / denominator
    return min(1.0, 2 * min(lower, upper))


def evaluate_aa(
    side_a: list[dict[str, Any]],
    side_b: list[dict[str, Any]],
    qualitative_winners: list[str],
) -> dict[str, Any]:
    hard_a = sum(bool(item["hard_pass"]) for item in side_a)
    hard_b = sum(bool(item["hard_pass"]) for item in side_b)
    mean_a = statistics.fmean(item["mechanical_score"] for item in side_a) if side_a else 0
    mean_b = statistics.fmean(item["mechanical_score"] for item in side_b) if side_b else 0
    non_ties = [winner for winner in qualitative_winners if winner in {"A", "B"}]
    side_a_rate = non_ties.count("A") / len(non_ties) if non_ties else 0
    side_b_rate = non_ties.count("B") / len(non_ties) if non_ties else 0
    position_p_value = _two_sided_binomial_p_value(
        non_ties.count("A"), len(non_ties)
    )
    position_bias_detected = position_p_value <= 0.05
    passed = (
        bool(side_a)
        and len(side_a) == len(side_b)
        and len(qualitative_winners) == len(side_a)
        and all(winner in {"A", "B", "TIE"} for winner in qualitative_winners)
        and abs(hard_a - hard_b) <= 1
        and abs(mean_a - mean_b) <= 5
        and not position_bias_detected
    )
    return {
        "status": "PASSED" if passed else "EVALUATOR_NOT_CALIBRATED",
        "passed": passed,
        "sample_size": min(len(side_a), len(side_b)),
        "hard_pass_counts": {"A": hard_a, "B": hard_b},
        "mean_mechanical_scores": {"A": mean_a, "B": mean_b},
        "non_tied_qualitative_count": len(non_ties),
        "qualitative_side_win_rates": {"A": side_a_rate, "B": side_b_rate},
        "qualitative_position_bias_p_value": position_p_value,
        "qualitative_position_bias_detected": position_bias_detected,
        "warnings": (
            ["LOW_DECISIVE_QUALITATIVE_SAMPLE"] if len(non_ties) < 20 else []
        ),
    }


def classify_bad_control_failure(
    case_id: str, expected_disposition: str, run: dict[str, Any]
) -> set[str]:
    mechanical = run.get("mechanical", {})
    fields = mechanical.get("fields", {})
    disposition = mechanical.get("disposition")
    classes: set[str] = set()
    if expected_disposition == "IMPLEMENTED" and disposition == "NEEDS_CLARIFICATION":
        classes.add("unnecessary_clarification")
        return classes
    if case_id == "simplicity-username-lowercase" and (
        not fields.get("allowed_paths_only", True)
        or len(run.get("changed_paths", [])) > 2
    ):
        classes.add("overengineering")
    if case_id == "scope-ttl-zero" and (
        not fields.get("required_unchanged_regions_preserved", True)
        or not fields.get("no_unrequested_artifacts", True)
    ):
        classes.add("drive_by_cleanup")
    if (
        case_id == "bug-reproduce-mutable-default"
        and not fields.get("required_pre_edit_evidence", True)
    ):
        classes.add("missing_reproduction")
    if (
        case_id == "goal-status-422"
        and disposition == "IMPLEMENTED"
        and not fields.get("hidden_behavior_passed", True)
    ):
        classes.add("false_completion")
    return classes


def evaluate_bad_control(
    champion: list[dict[str, Any]],
    bad: list[dict[str, Any]],
    qualitative_winners: list[str],
    failure_classes: set[str],
) -> dict[str, Any]:
    unknown = failure_classes - BAD_CONTROL_CLASSES
    if unknown:
        raise ValueError(f"unknown bad-control failure classes: {sorted(unknown)}")
    champion_rate = (
        sum(bool(item["hard_pass"]) for item in champion) / len(champion) if champion else 0
    )
    bad_rate = sum(bool(item["hard_pass"]) for item in bad) / len(bad) if bad else 0
    non_ties = [winner for winner in qualitative_winners if winner != "TIE"]
    champion_win_rate = (
        non_ties.count("champion") / len(non_ties) if non_ties else 0
    )
    passed = (
        bool(champion)
        and len(champion) == len(bad)
        and len(qualitative_winners) == len(champion)
        and all(
            winner in {"champion", "deliberately-bad", "TIE"}
            for winner in qualitative_winners
        )
        and champion_rate >= bad_rate
        and champion_win_rate >= 0.70
        and len(failure_classes) >= 3
    )
    return {
        "status": "PASSED" if passed else "EVALUATOR_BAD_CONTROL_FAILED",
        "passed": passed,
        "sample_size": min(len(champion), len(bad)),
        "hard_pass_rates": {"champion": champion_rate, "deliberately_bad": bad_rate},
        "non_tied_qualitative_count": len(non_ties),
        "champion_qualitative_win_rate": champion_win_rate,
        "failure_classes": sorted(failure_classes),
    }


def aggregate_by_case(comparisons: list[dict[str, Any]]) -> dict[str, Any]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for comparison in comparisons:
        grouped[comparison["case_id"]].append(comparison)
    result: dict[str, Any] = {}
    for case_id, items in sorted(grouped.items()):
        wins = sum(item.get("qualitative_winner") == "candidate" for item in items)
        losses = sum(item.get("qualitative_winner") == "champion" for item in items)
        ties = sum(item.get("qualitative_winner") == "TIE" for item in items)
        result[case_id] = {
            "replicates": len(items),
            "champion_hard_passes": sum(
                bool(item["champion"]["mechanical"]["hard_pass"]) for item in items
            ),
            "candidate_hard_passes": sum(
                bool(item["candidate"]["mechanical"]["hard_pass"]) for item in items
            ),
            "qualitative": {"wins": wins, "losses": losses, "ties": ties},
        }
    return result


def evidence_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()
