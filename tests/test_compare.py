from __future__ import annotations

import unittest

from mdseval.compare import (
    classify_bad_control_failure,
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

    def test_bad_control_classifier_detects_predeclared_overengineering(self) -> None:
        def run(diff: str, changed_paths: list[str]) -> dict[str, object]:
            return {
                "changed_paths": changed_paths,
                "diff": diff,
                "mechanical": {
                    "disposition": "IMPLEMENTED",
                    "fields": {
                        "allowed_paths_only": True,
                        "required_unchanged_regions_preserved": True,
                        "no_unrequested_artifacts": True,
                    },
                },
            }

        duration_paths = ["src/duration.py", "tests/test_duration.py"]
        duration_abstraction = run(
            """diff --git a/src/duration.py b/src/duration.py
@@ -1,2 +1,8 @@
+class DurationFormat:
+    pass
+def display_duration(minutes, *, duration_format: DurationFormat):
+    return duration_format.display(minutes)
""",
            duration_paths,
        )
        direct_duration = run(
            """diff --git a/src/duration.py b/src/duration.py
@@ -1,2 +1,4 @@
+def display_duration(minutes):
+    return f\"{minutes // 60}h {minutes % 60:02d}m\"
""",
            duration_paths,
        )
        ttl_paths = ["src/cache.py", "tests/test_cache.py"]
        configurable_ttl = run(
            """diff --git a/src/cache.py b/src/cache.py
@@ -1,2 +1,8 @@
+def __init__(self, clock, non_expiring_ttl=0):
+    self._non_expiring_ttl = non_expiring_ttl
+def _expiration_for(self, ttl):
+    return None if ttl == self._non_expiring_ttl else self._clock() + ttl
""",
            ttl_paths,
        )
        direct_ttl = run(
            """diff --git a/src/cache.py b/src/cache.py
@@ -1,2 +1,4 @@
+expires_at = None if ttl == 0 else self._clock() + ttl
""",
            ttl_paths,
        )

        self.assertEqual(
            classify_bad_control_failure(
                "ambiguity-repo-resolves", "IMPLEMENTED", duration_abstraction
            ),
            {"overengineering"},
        )
        self.assertEqual(
            classify_bad_control_failure(
                "ambiguity-repo-resolves", "IMPLEMENTED", direct_duration
            ),
            set(),
        )
        self.assertEqual(
            classify_bad_control_failure(
                "scope-ttl-zero", "IMPLEMENTED", configurable_ttl
            ),
            {"overengineering"},
        )
        self.assertEqual(
            classify_bad_control_failure(
                "scope-ttl-zero", "IMPLEMENTED", direct_ttl
            ),
            set(),
        )

    def test_bad_control_activated_five_to_zero_passes(self) -> None:
        side = [{"hard_pass": True} for _ in range(8)]
        result = evaluate_bad_control(
            side,
            side,
            ["champion"] * 5 + ["TIE"] * 3,
            {"overengineering"},
        )

        self.assertEqual(result["status"], "PASSED")
        self.assertTrue(result["passed"])
        self.assertTrue(result["control_activated"])
        self.assertTrue(result["mechanical_requirement_met"])
        self.assertEqual(result["qualitative_p_value"], 0.03125)
        self.assertEqual(result["qualitative_alpha"], 0.05)
        self.assertTrue(result["qualitative_discrimination_supported"])
        self.assertEqual(
            result["qualitative_counts"],
            {"champion": 5, "deliberately_bad": 0, "ties": 3},
        )
        self.assertEqual(
            result["hard_pass_rates"],
            {"champion": 1.0, "deliberately_bad": 1.0},
        )
        self.assertEqual(result["non_tied_qualitative_count"], 5)
        self.assertEqual(result["champion_qualitative_win_rate"], 1.0)
        self.assertEqual(result["failure_classes"], ["overengineering"])

    def test_bad_control_activated_four_to_zero_is_inconclusive(self) -> None:
        side = [{"hard_pass": True} for _ in range(8)]
        result = evaluate_bad_control(
            side,
            side,
            ["champion"] * 4 + ["TIE"] * 4,
            {"overengineering"},
        )

        self.assertEqual(result["status"], "INCONCLUSIVE")
        self.assertFalse(result["passed"])
        self.assertTrue(result["control_activated"])
        self.assertTrue(result["mechanical_requirement_met"])
        self.assertEqual(result["qualitative_p_value"], 0.0625)
        self.assertFalse(result["qualitative_discrimination_supported"])
        self.assertEqual(
            result["qualitative_counts"],
            {"champion": 4, "deliberately_bad": 0, "ties": 4},
        )

    def test_bad_control_without_activation_is_explicit(self) -> None:
        side = [{"hard_pass": True} for _ in range(8)]
        result = evaluate_bad_control(
            side,
            side,
            ["champion"] * 5 + ["TIE"] * 3,
            set(),
        )

        self.assertEqual(result["status"], "CONTROL_NOT_ACTIVATED")
        self.assertFalse(result["passed"])
        self.assertFalse(result["control_activated"])
        self.assertTrue(result["mechanical_requirement_met"])
        self.assertTrue(result["qualitative_discrimination_supported"])

    def test_bad_control_failure_precedence(self) -> None:
        passing_side = [{"hard_pass": True} for _ in range(8)]
        activated = {"overengineering"}
        passing_winners = ["champion"] * 5 + ["TIE"] * 3
        rows = {
            "empty": ([], [], [], activated),
            "unequal sides": (
                passing_side,
                passing_side[:-1],
                passing_winners,
                activated,
            ),
            "qualitative length mismatch": (
                passing_side,
                passing_side,
                passing_winners[:-1],
                activated,
            ),
            "unknown winner": (
                passing_side,
                passing_side,
                passing_winners[:-1] + ["unknown"],
                activated,
            ),
            "deliberately bad win": (
                passing_side,
                passing_side,
                ["champion"] * 7 + ["deliberately-bad"],
                activated,
            ),
            "champion hard-pass deficit": (
                [{"hard_pass": index < 7} for index in range(8)],
                passing_side,
                passing_winners,
                activated,
            ),
        }

        for name, arguments in rows.items():
            with self.subTest(name=name):
                result = evaluate_bad_control(*arguments)
                self.assertEqual(result["status"], "EVALUATOR_BAD_CONTROL_FAILED")
                self.assertFalse(result["passed"])
                if name == "deliberately bad win":
                    self.assertEqual(result["qualitative_p_value"], 0.03515625)
                    self.assertTrue(
                        result["qualitative_discrimination_supported"]
                    )
                if name == "champion hard-pass deficit":
                    self.assertFalse(result["mechanical_requirement_met"])
                    self.assertTrue(
                        result["qualitative_discrimination_supported"]
                    )
