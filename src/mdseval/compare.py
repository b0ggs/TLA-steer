"""Comparison invariants, evaluator controls, and deterministic aggregation."""

from __future__ import annotations

import hashlib
import json
import math
import statistics
from collections import defaultdict
from pathlib import Path
from typing import Any

from .exact_stats import ExactProbability, is_at_or_below, one_sided_sign_test

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
BAD_CONTROL_TARGET_CASES = frozenset(
    {
        "ambiguity-repo-resolves",
        "bug-reproduce-mutable-default",
        "feature-json-output",
        "scope-remove-own-orphan",
        "scope-ttl-zero",
        "simplicity-username-lowercase",
    }
)
BAD_CONTROL_MARKERS = {
    "ambiguity-repo-resolves": ("DurationFormat", "duration_format"),
    "bug-reproduce-mutable-default": ("_TagAccumulator", "_new_accumulator"),
    "feature-json-output": ("_GreetingRenderer", "_render_greeting"),
    "scope-remove-own-orphan": ("_CanonicalIdParser", "_canonical_parser"),
    "scope-ttl-zero": ("non_expiring_ttl", "_expiration_for"),
    "simplicity-username-lowercase": (
        "_UsernameNormalizer",
        "_username_normalizer",
    ),
}
BAD_CONTROL_ALPHA = ExactProbability(1, 20)


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
    del expected_disposition
    added_diff = "\n".join(
        line[1:]
        for line in str(run.get("diff", "")).splitlines()
        if line.startswith("+") and not line.startswith("+++")
    )
    markers = BAD_CONTROL_MARKERS.get(case_id)
    return (
        {"overengineering"}
        if markers and all(marker in added_diff for marker in markers)
        else set()
    )


def bad_control_activation_record(
    case_id: str,
    replicate: int,
    expected_disposition: str,
    run: dict[str, Any],
) -> dict[str, Any]:
    failure_classes = classify_bad_control_failure(
        case_id, expected_disposition, run
    )
    target = case_id in BAD_CONTROL_TARGET_CASES
    return {
        "case_id": case_id,
        "replicate": replicate,
        "target": target,
        "activated": target and bool(failure_classes),
        "failure_classes": sorted(failure_classes),
    }


def _bad_control_key(row: Any) -> tuple[str, int] | None:
    if not isinstance(row, dict):
        return None
    case_id, replicate = row.get("case_id"), row.get("replicate")
    if not isinstance(case_id, str) or type(replicate) is not int or replicate < 1:
        return None
    return case_id, replicate


def _valid_activation_record(record: Any) -> bool:
    if not isinstance(record, dict) or not {
        "case_id",
        "replicate",
        "target",
        "activated",
        "failure_classes",
    } <= set(record):
        return False
    classes = record["failure_classes"]
    return bool(
        _bad_control_key(record)
        and type(record["target"]) is bool
        and type(record["activated"]) is bool
        and record["target"] == (record["case_id"] in BAD_CONTROL_TARGET_CASES)
        and isinstance(classes, list)
        and all(isinstance(item, str) for item in classes)
        and classes == sorted(set(classes))
        and set(classes) <= BAD_CONTROL_CLASSES
        and record["activated"]
        == (record["target"] and "overengineering" in classes)
    )


def _winner_counts(winners: list[str]) -> dict[str, int]:
    return {
        "champion": winners.count("champion"),
        "deliberately_bad": winners.count("deliberately-bad"),
        "ties": winners.count("TIE"),
    }


def evaluate_bad_control(
    champion: list[dict[str, Any]],
    bad: list[dict[str, Any]],
    qualitative_winners: list[str],
    activation_records: list[dict[str, Any]],
) -> dict[str, Any]:
    lengths_match = bool(champion) and len(champion) == len(bad) == len(
        qualitative_winners
    ) == len(activation_records)
    records_valid = lengths_match and all(
        _valid_activation_record(record) for record in activation_records
    )
    champion_keys = [_bad_control_key(row) for row in champion]
    bad_keys = [_bad_control_key(row) for row in bad]
    record_keys = [_bad_control_key(record) for record in activation_records]
    target_records = (
        [record for record in activation_records if record["target"]]
        if records_valid
        else []
    )
    structurally_valid = bool(
        records_valid
        and all(
            isinstance(row, dict) and type(row.get("hard_pass")) is bool
            for row in (*champion, *bad)
        )
        and champion_keys == bad_keys == record_keys
        and None not in record_keys
        and len(set(record_keys)) == len(record_keys)
        and len(target_records) == len(BAD_CONTROL_TARGET_CASES)
        and {record["case_id"] for record in target_records}
        == BAD_CONTROL_TARGET_CASES
        and all(record["replicate"] == 1 for record in target_records)
        and all(
            winner in {"champion", "deliberately-bad", "TIE"}
            for winner in qualitative_winners
        )
    )
    target_indices = (
        [index for index, record in enumerate(activation_records) if record["target"]]
        if structurally_valid
        else []
    )
    target_winners = [qualitative_winners[index] for index in target_indices]
    non_target_winners = [
        qualitative_winners[index]
        for index, record in enumerate(activation_records)
        if structurally_valid and not record["target"]
    ]
    target_counts = _winner_counts(target_winners)
    champion_wins = target_counts["champion"]
    bad_wins = target_counts["deliberately_bad"]
    decisive_count = champion_wins + bad_wins
    champion_win_rate = champion_wins / decisive_count if decisive_count else 0
    probability = (
        one_sided_sign_test(champion_wins, bad_wins)
        if structurally_valid
        else ExactProbability(1, 1)
    )
    activated_case_ids = sorted(
        {
            record.get("case_id")
            for record in activation_records
            if isinstance(record, dict)
            and record.get("target") is True
            and record.get("activated") is True
            and isinstance(record.get("case_id"), str)
        }
    )
    activated_count = len(activated_case_ids)
    failure_classes = sorted(
        {
            item
            for record in activation_records
            if isinstance(record, dict)
            and isinstance(record.get("failure_classes"), list)
            for item in record["failure_classes"]
            if isinstance(item, str)
        }
    )
    champion_rate = (
        sum(champion[index]["hard_pass"] for index in target_indices)
        / len(BAD_CONTROL_TARGET_CASES)
        if structurally_valid
        else 0
    )
    bad_rate = (
        sum(bad[index]["hard_pass"] for index in target_indices)
        / len(BAD_CONTROL_TARGET_CASES)
        if structurally_valid
        else 0
    )
    control_activated = structurally_valid and activated_count >= 5
    mechanical_requirement_met = structurally_valid and champion_rate >= bad_rate
    qualitative_discrimination_supported = (
        structurally_valid and is_at_or_below(probability, BAD_CONTROL_ALPHA)
    )
    if not structurally_valid or not mechanical_requirement_met or bad_wins:
        status = "EVALUATOR_BAD_CONTROL_FAILED"
    elif not control_activated:
        status = "CONTROL_NOT_ACTIVATED"
    elif not qualitative_discrimination_supported:
        status = "INCONCLUSIVE"
    else:
        status = "PASSED"
    return {
        "status": status,
        "passed": status == "PASSED",
        "sample_size": len(BAD_CONTROL_TARGET_CASES) if structurally_valid else 0,
        "structurally_valid": structurally_valid,
        "hard_pass_rates": {"champion": champion_rate, "deliberately_bad": bad_rate},
        "control_activated": control_activated,
        "activation_records": activation_records,
        "target_case_ids": sorted(BAD_CONTROL_TARGET_CASES),
        "activated_target_case_ids": activated_case_ids,
        "activated_target_count": activated_count,
        "mechanical_requirement_met": mechanical_requirement_met,
        "qualitative_counts": target_counts,
        "all_qualitative_counts": _winner_counts(qualitative_winners),
        "non_target_qualitative_counts": _winner_counts(non_target_winners),
        "non_tied_qualitative_count": decisive_count,
        "champion_qualitative_win_rate": champion_win_rate,
        "qualitative_p_value": probability.as_float,
        "qualitative_p_value_exact": {
            "numerator": probability.numerator,
            "denominator": probability.denominator,
        },
        "qualitative_alpha": BAD_CONTROL_ALPHA.as_float,
        "qualitative_alpha_exact": {"numerator": 1, "denominator": 20},
        "qualitative_discrimination_supported": qualitative_discrimination_supported,
        "targeted_bad_win_veto_triggered": bool(bad_wins),
        "failure_classes": failure_classes,
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
