from __future__ import annotations

import unittest

from mdseval.promotion import REQUIRED_CASES, TARGETED_CASES, evaluate_promotion


def side(hard: bool = True, tokens: int = 100) -> dict:
    return {
        "mechanical": {
            "hard_pass": hard,
            "fields": {
                "hidden_behavior_passed": hard,
                "expected_disposition": hard,
            },
        },
        "usage": {"total_tokens": tokens, "usage_reported": True},
    }


def comparisons() -> list[dict]:
    values = []
    win_budget = 6
    for case_id in sorted(REQUIRED_CASES):
        for replicate in (1, 2):
            winner = "TIE"
            if case_id in TARGETED_CASES and win_budget:
                winner = "candidate"
                win_budget -= 1
            values.append(
                {
                    "valid": True,
                    "case_id": case_id,
                    "suite": "holdout"
                    if case_id in {"breadth-layered-settings", "goal-real-entrypoint"}
                    else "dev",
                    "replicate": replicate,
                    "champion": side(),
                    "candidate": side(),
                    "qualitative_winner": winner,
                }
            )
    return values


def controls() -> dict:
    return {
        "comparison": {"invariant_hash": "frozen"},
        "aa": {"passed": True, "evaluator_hash": "eval", "invariant_hash": "frozen"},
        "bad_control": {
            "passed": True,
            "evaluator_hash": "eval",
            "invariant_hash": "frozen",
        },
    }


class PromotionTests(unittest.TestCase):
    def test_promote_requires_complete_bound_evidence(self) -> None:
        result = evaluate_promotion(
            comparisons(),
            aa_passed=True,
            bad_control_passed=True,
            evaluator_hash="eval",
            control_evidence=controls(),
        )
        self.assertEqual(result["verdict"], "PROMOTE")

    def test_reject_hard_regression(self) -> None:
        values = comparisons()
        values[0]["candidate"] = side(False)
        result = evaluate_promotion(
            values,
            aa_passed=True,
            bad_control_passed=True,
            evaluator_hash="eval",
            control_evidence=controls(),
        )
        self.assertEqual(result["verdict"], "REJECT")

    def test_inconclusive_for_missing_controls_or_coverage(self) -> None:
        result = evaluate_promotion(
            comparisons(),
            aa_passed=False,
            bad_control_passed=False,
        )
        self.assertEqual(result["verdict"], "INCONCLUSIVE")
        result = evaluate_promotion(
            comparisons()[:2],
            aa_passed=True,
            bad_control_passed=True,
            evaluator_hash="eval",
            control_evidence=controls(),
        )
        self.assertEqual(result["verdict"], "INCONCLUSIVE")

    def test_invalid_comparison_precedes_other_gates(self) -> None:
        values = comparisons()
        values[0]["valid"] = False
        self.assertEqual(
            evaluate_promotion(values, aa_passed=True, bad_control_passed=True)[
                "verdict"
            ],
            "INVALID_COMPARISON",
        )

    def test_duplicate_replicate_and_missing_usage_cannot_promote(self) -> None:
        values = comparisons()
        values[1]["replicate"] = 1
        values[2]["candidate"]["usage"]["usage_reported"] = False
        result = evaluate_promotion(
            values,
            aa_passed=True,
            bad_control_passed=True,
            evaluator_hash="eval",
            control_evidence=controls(),
        )
        self.assertEqual(result["verdict"], "INCONCLUSIVE")
