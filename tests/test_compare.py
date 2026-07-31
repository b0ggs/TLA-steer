from __future__ import annotations

import unittest

from mdseval.compare import (
    evaluate_aa,
    evaluate_bad_control,
    invariant_mismatches,
)


class CompareTests(unittest.TestCase):
    def test_independent_invariant_mismatch_is_invalid(self) -> None:
        base = {
            field: "same"
            for field in (
                "experiment_sha256",
                "case_definition_sha256",
                "fixture_tree_sha256",
                "wrapper_prompt_sha256",
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
        }
        other = dict(base)
        other["python_version"] = "different"
        self.assertEqual(
            invariant_mismatches(base, other)["python_version"],
            ("same", "different"),
        )

    def test_aa_all_ties_passes_position_veto_with_warning(self) -> None:
        side = [{"hard_pass": True, "mechanical_score": 100} for _ in range(8)]
        result = evaluate_aa(side, side, ["TIE"] * 8)
        self.assertTrue(result["passed"])
        self.assertEqual(result["non_tied_qualitative_count"], 0)
        self.assertEqual(result["qualitative_position_bias_p_value"], 1.0)
        self.assertEqual(result["warnings"], ["LOW_DECISIVE_QUALITATIVE_SAMPLE"])

    def test_aa_four_to_zero_with_twelve_ties_does_not_trip_veto(self) -> None:
        side = [{"hard_pass": True, "mechanical_score": 100} for _ in range(16)]
        result = evaluate_aa(side, side, ["A"] * 4 + ["TIE"] * 12)
        self.assertTrue(result["passed"])
        self.assertAlmostEqual(result["qualitative_position_bias_p_value"], 0.125)
        self.assertFalse(result["qualitative_position_bias_detected"])
        self.assertEqual(result["qualitative_side_win_rates"], {"A": 1.0, "B": 0.0})
        self.assertEqual(result["warnings"], ["LOW_DECISIVE_QUALITATIVE_SAMPLE"])

    def test_aa_eight_to_zero_trips_position_veto(self) -> None:
        side = [{"hard_pass": True, "mechanical_score": 100} for _ in range(8)]
        result = evaluate_aa(side, side, ["A"] * 8)
        self.assertFalse(result["passed"])
        self.assertAlmostEqual(
            result["qualitative_position_bias_p_value"], 0.0078125
        )
        self.assertTrue(result["qualitative_position_bias_detected"])

    def test_aa_balanced_twenty_has_no_low_sample_warning(self) -> None:
        side = [{"hard_pass": True, "mechanical_score": 100} for _ in range(20)]
        result = evaluate_aa(side, side, ["A"] * 10 + ["B"] * 10)
        self.assertTrue(result["passed"])
        self.assertEqual(result["qualitative_position_bias_p_value"], 1.0)
        self.assertEqual(result["warnings"], [])

    def test_aa_structural_and_mechanical_failures_still_fail(self) -> None:
        self.assertFalse(evaluate_aa([], [], [])["passed"])
        side_a = [{"hard_pass": True, "mechanical_score": 100} for _ in range(8)]
        hard_b = [
            {"hard_pass": index < 6, "mechanical_score": 100}
            for index in range(8)
        ]
        score_b = [{"hard_pass": True, "mechanical_score": 94} for _ in range(8)]
        self.assertFalse(evaluate_aa(side_a, hard_b, ["TIE"] * 8)["passed"])
        self.assertFalse(evaluate_aa(side_a, score_b, ["TIE"] * 8)["passed"])

    def test_bad_control_thresholds(self) -> None:
        champion = [{"hard_pass": True} for _ in range(10)]
        bad = [{"hard_pass": False} for _ in range(10)]
        result = evaluate_bad_control(
            champion,
            bad,
            ["champion"] * 8 + ["TIE"] * 2,
            {"unnecessary_clarification", "overengineering", "missing_reproduction"},
        )
        self.assertTrue(result["passed"])
        result = evaluate_bad_control(champion, bad, ["TIE"] * 10, {"false_completion"})
        self.assertFalse(result["passed"])
