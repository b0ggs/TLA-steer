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

    def test_aa_pass_and_position_bias_fail(self) -> None:
        side = [{"hard_pass": True, "mechanical_score": 100} for _ in range(8)]
        passed = evaluate_aa(side, side, ["TIE"] * 8)
        self.assertTrue(passed["passed"])
        biased = evaluate_aa(side, side, ["A"] * 8)
        self.assertFalse(biased["passed"])
        self.assertFalse(evaluate_aa([], [], [])["passed"])

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
