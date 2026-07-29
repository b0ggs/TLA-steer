"""Gate-first human promotion recommendation policy."""

from __future__ import annotations

import statistics
from collections import defaultdict
from typing import Any

TARGETED_CASES = frozenset(
    {
        "ambiguity-must-clarify",
        "ambiguity-repo-resolves",
        "simplicity-username-lowercase",
        "scope-ttl-zero",
        "scope-remove-own-orphan",
        "bug-reproduce-mutable-default",
    }
)
HOLDOUT_CASES = frozenset({"breadth-layered-settings", "goal-real-entrypoint"})
REQUIRED_CASES = TARGETED_CASES | HOLDOUT_CASES | frozenset(
    {"feature-json-output", "goal-status-422"}
)


def _field_rate(comparisons: list[dict[str, Any]], side: str, field: str) -> float:
    if not comparisons:
        return 0.0
    return sum(
        bool(item[side]["mechanical"]["fields"].get(field)) for item in comparisons
    ) / len(comparisons)


def evaluate_promotion(
    comparisons: list[dict[str, Any]],
    *,
    aa_passed: bool,
    bad_control_passed: bool,
    evidence_frozen: bool = True,
    token_increase_justification: dict[str, Any] | None = None,
    evaluator_hash: str | None = None,
    control_evidence: dict[str, dict[str, Any]] | None = None,
    expected_repeats: int = 2,
) -> dict[str, Any]:
    reasons: list[str] = []
    if not comparisons or not evidence_frozen or any(not item.get("valid", False) for item in comparisons):
        return {
            "verdict": "INVALID_COMPARISON",
            "reasons": ["missing, mismatched, or unfrozen comparison evidence"],
        }

    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for comparison in comparisons:
        grouped[comparison["case_id"]].append(comparison)
    missing_targeted = sorted(TARGETED_CASES - set(grouped))
    missing_holdout = sorted(HOLDOUT_CASES - set(grouped))
    missing_required = sorted(REQUIRED_CASES - set(grouped))
    unexpected_cases = sorted(set(grouped) - REQUIRED_CASES)
    wrong_suites = sorted(
        {
            item["case_id"]
            for item in comparisons
            if item.get("suite")
            != (
                "holdout"
                if item["case_id"] in HOLDOUT_CASES
                else "dev"
            )
        }
    )
    insufficient_repeats = sorted(
        case_id
        for case_id in REQUIRED_CASES
        if len(grouped.get(case_id, [])) != expected_repeats
        or {item.get("replicate") for item in grouped.get(case_id, [])}
        != set(range(1, expected_repeats + 1))
    )
    regressions: list[dict[str, Any]] = []
    for case_id, items in sorted(grouped.items()):
        champion_clean = all(
            item["champion"]["mechanical"]["hard_pass"] for item in items
        )
        candidate_failed = [
            item["replicate"]
            for item in items
            if not item["candidate"]["mechanical"]["hard_pass"]
        ]
        if champion_clean and candidate_failed:
            regressions.append({"case_id": case_id, "replicates": candidate_failed})
    if regressions:
        return {
            "verdict": "REJECT",
            "reasons": ["candidate introduced a hard regression"],
            "hard_regressions": regressions,
        }

    for field, label in (
        ("hidden_behavior_passed", "hidden-behavior pass rate"),
        ("expected_disposition", "correct-disposition rate"),
    ):
        champion_rate = _field_rate(comparisons, "champion", field)
        candidate_rate = _field_rate(comparisons, "candidate", field)
        if candidate_rate < champion_rate:
            return {
                "verdict": "REJECT",
                "reasons": [f"candidate {label} is lower than champion"],
                "rates": {"champion": champion_rate, "candidate": candidate_rate},
            }

    holdout_regressions = [
        item["case_id"]
        for item in comparisons
        if item.get("suite") == "holdout"
        and item["champion"]["mechanical"]["hard_pass"]
        and not item["candidate"]["mechanical"]["hard_pass"]
    ]
    if holdout_regressions:
        hard_regressions = [
            {"case_id": case_id, "replicates": [
                item["replicate"]
                for item in comparisons
                if item["case_id"] == case_id
                and item["champion"]["mechanical"]["hard_pass"]
                and not item["candidate"]["mechanical"]["hard_pass"]
            ]}
            for case_id in sorted(set(holdout_regressions))
        ]
        return {
            "verdict": "REJECT",
            "reasons": ["candidate has a holdout hard regression"],
            "holdout_regressions": sorted(set(holdout_regressions)),
            "hard_regressions": hard_regressions,
        }

    targeted = [item for item in comparisons if item["case_id"] in TARGETED_CASES]
    wins = sum(item.get("qualitative_winner") == "candidate" for item in targeted)
    losses = sum(item.get("qualitative_winner") == "champion" for item in targeted)
    ties = sum(item.get("qualitative_winner") == "TIE" for item in targeted)
    if not aa_passed:
        reasons.append("A/A calibration has not passed on the frozen evaluator")
    if not bad_control_passed:
        reasons.append("bad-control validation has not passed on the frozen evaluator")
    evidence_matches = bool(
        evaluator_hash
        and control_evidence
        and all(
            control_evidence.get(name, {}).get("passed")
            and control_evidence[name].get("evaluator_hash") == evaluator_hash
            and control_evidence[name].get("invariant_hash")
            == control_evidence.get("comparison", {}).get("invariant_hash")
            for name in ("aa", "bad_control")
        )
    )
    if not evidence_matches:
        reasons.append("control evidence is not bound to the same evaluator and invariants")
    if missing_targeted:
        reasons.append(f"missing targeted cases: {', '.join(missing_targeted)}")
    if missing_holdout:
        reasons.append(f"missing holdout cases: {', '.join(missing_holdout)}")
    if missing_required:
        reasons.append(f"missing required cases: {', '.join(missing_required)}")
    if unexpected_cases:
        reasons.append(f"unexpected cases: {', '.join(unexpected_cases)}")
    if wrong_suites:
        reasons.append(f"cases have incorrect suite labels: {', '.join(wrong_suites)}")
    if insufficient_repeats:
        reasons.append(
            f"required replicate coverage is incomplete: {', '.join(insufficient_repeats)}"
        )
    if wins < 3 or losses > 1:
        reasons.append("targeted replicate-level qualitative threshold was not met")
    if any(
        item.get("qualitative_winner") not in {"candidate", "champion", "TIE"}
        for item in comparisons
    ):
        reasons.append("qualitative evidence is incomplete")

    champion_tokens = [
        item["champion"].get("usage", {}).get("total_tokens", 0) for item in comparisons
    ]
    candidate_tokens = [
        item["candidate"].get("usage", {}).get("total_tokens", 0) for item in comparisons
    ]
    if any(
        not item[side].get("usage", {}).get("usage_reported", False)
        for item in comparisons
        for side in ("champion", "candidate")
    ):
        reasons.append("token usage evidence is incomplete")
    champion_median = statistics.median(champion_tokens) if champion_tokens else 0
    candidate_median = statistics.median(candidate_tokens) if candidate_tokens else 0
    token_ratio = (
        candidate_median / champion_median
        if champion_median
        else (1.0 if candidate_median == 0 else None)
    )
    justification_valid = bool(
        isinstance(token_increase_justification, dict)
        and isinstance(token_increase_justification.get("correctness_gain"), str)
        and token_increase_justification["correctness_gain"].strip()
        and isinstance(token_increase_justification.get("evidence"), list)
        and token_increase_justification["evidence"]
    )
    if (token_ratio is None or token_ratio > 1.25) and not justification_valid:
        reasons.append(
            "median total tokens increased by more than 25% without structured correctness justification"
        )
    verdict = "PROMOTE" if not reasons else "INCONCLUSIVE"
    return {
        "verdict": verdict,
        "reasons": reasons,
        "hard_regressions": [],
        "targeted_replicate_results": {
            "wins": wins,
            "losses": losses,
            "ties": ties,
            "count": len(targeted),
        },
        "median_total_tokens": {
            "champion": champion_median,
            "candidate": candidate_median,
            "ratio": token_ratio,
        },
        "token_increase_justification": token_increase_justification,
    }
