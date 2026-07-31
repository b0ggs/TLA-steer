from __future__ import annotations

import copy
import unittest

from mdseval.compare import (
    BAD_CONTROL_MARKERS,
    BAD_CONTROL_TARGET_CASES,
    bad_control_activation_record,
    classify_bad_control_failure,
    evaluate_aa,
    evaluate_bad_control,
    invariant_mismatches,
)


def _bad_control_inputs(
    target_winners: list[str],
    activated: int = 6,
    non_target_winners: tuple[str, str] = ("TIE", "TIE"),
) -> tuple[list[dict], list[dict], list[str], list[dict]]:
    target_cases = sorted(BAD_CONTROL_TARGET_CASES)
    cases = target_cases + ["ambiguity-must-clarify", "goal-status-422"]
    champion: list[dict] = []
    bad: list[dict] = []
    records: list[dict] = []
    for index, case_id in enumerate(cases):
        markers = BAD_CONTROL_MARKERS.get(case_id)
        diff = (
            f"+{markers[0]}\n+{markers[1]}\n"
            if markers and index < activated
            else ""
        )
        records.append(
            bad_control_activation_record(
                case_id, 1, "IMPLEMENTED", {"diff": diff}
            )
        )
        key = {"case_id": case_id, "replicate": 1, "hard_pass": True}
        champion.append(dict(key))
        bad.append(dict(key))
    return champion, bad, target_winners + list(non_target_winners), records


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

    def test_six_exact_added_signatures_activate_and_close_matches_do_not(self) -> None:
        self.assertEqual(
            BAD_CONTROL_TARGET_CASES,
            {
                "ambiguity-repo-resolves",
                "bug-reproduce-mutable-default",
                "feature-json-output",
                "scope-remove-own-orphan",
                "scope-ttl-zero",
                "simplicity-username-lowercase",
            },
        )
        for case_id, markers in BAD_CONTROL_MARKERS.items():
            with self.subTest(case_id=case_id):
                positive = {"diff": f"+{markers[0]}\n+{markers[1]}\n"}
                close = {"diff": f"+{markers[0]}\n-{markers[1]}\n"}
                self.assertEqual(
                    classify_bad_control_failure(case_id, "IMPLEMENTED", positive),
                    {"overengineering"},
                )
                self.assertEqual(
                    classify_bad_control_failure(case_id, "IMPLEMENTED", close), set()
                )
                record = bad_control_activation_record(
                    case_id, 2, "IMPLEMENTED", positive
                )
                self.assertEqual(
                    record,
                    {
                        "case_id": case_id,
                        "replicate": 2,
                        "target": True,
                        "activated": True,
                        "failure_classes": ["overengineering"],
                    },
                )
        self.assertFalse(
            bad_control_activation_record(
                "goal-status-422",
                1,
                "IMPLEMENTED",
                {"diff": "+DurationFormat\n+duration_format\n"},
            )["activated"]
        )

    def test_activation_records_require_five_and_classes_do_not_change_inference(self) -> None:
        inputs = _bad_control_inputs(["champion"] * 5 + ["TIE"], activated=5)
        result = evaluate_bad_control(*inputs)
        self.assertEqual(result["status"], "PASSED")
        self.assertEqual(len(result["activation_records"]), 8)
        self.assertEqual(result["activated_target_count"], 5)
        self.assertEqual(
            [(item["case_id"], item["replicate"]) for item in result["activation_records"]],
            [(item["case_id"], 1) for item in inputs[3]],
        )
        insufficient = evaluate_bad_control(
            *_bad_control_inputs(["champion"] * 5 + ["TIE"], activated=4)
        )
        self.assertEqual(insufficient["status"], "CONTROL_NOT_ACTIVATED")
        noisy = copy.deepcopy(inputs)
        noisy[3][0]["failure_classes"] = ["drive_by_cleanup", "overengineering"]
        noisy_result = evaluate_bad_control(*noisy)
        self.assertEqual(noisy_result["sample_size"], result["sample_size"])
        self.assertEqual(
            noisy_result["qualitative_p_value_exact"],
            result["qualitative_p_value_exact"],
        )
        self.assertEqual(
            noisy_result["failure_classes"], ["drive_by_cleanup", "overengineering"]
        )

    def test_exact_six_target_decision_boundaries(self) -> None:
        rows = (
            (["champion"] * 5 + ["TIE"], "PASSED", (1, 32)),
            (["champion"] * 4 + ["TIE"] * 2, "INCONCLUSIVE", (1, 16)),
            (["champion"] * 6, "PASSED", (1, 64)),
        )
        for winners, status, exact in rows:
            with self.subTest(winners=winners):
                result = evaluate_bad_control(*_bad_control_inputs(winners))
                self.assertEqual(result["status"], status)
                self.assertEqual(
                    result["qualitative_p_value_exact"],
                    {"numerator": exact[0], "denominator": exact[1]},
                )
                self.assertEqual(result["qualitative_alpha_exact"], {"numerator": 1, "denominator": 20})

    def test_only_targeted_bad_wins_trip_the_veto_and_enter_the_test(self) -> None:
        targeted = evaluate_bad_control(
            *_bad_control_inputs(["champion"] * 5 + ["deliberately-bad"])
        )
        self.assertEqual(targeted["status"], "EVALUATOR_BAD_CONTROL_FAILED")
        self.assertTrue(targeted["targeted_bad_win_veto_triggered"])
        non_target = evaluate_bad_control(
            *_bad_control_inputs(
                ["champion"] * 5 + ["TIE"],
                non_target_winners=("deliberately-bad", "TIE"),
            )
        )
        self.assertEqual(non_target["status"], "PASSED")
        self.assertFalse(non_target["targeted_bad_win_veto_triggered"])
        self.assertEqual(non_target["qualitative_counts"]["deliberately_bad"], 0)
        self.assertEqual(
            non_target["non_target_qualitative_counts"]["deliberately_bad"], 1
        )
        self.assertEqual(non_target["qualitative_p_value_exact"], {"numerator": 1, "denominator": 32})

    def test_unknown_misaligned_duplicate_missing_and_mechanical_deficit_fail(self) -> None:
        base = _bad_control_inputs(["champion"] * 5 + ["TIE"])
        unknown = copy.deepcopy(base)
        unknown[2][0] = "unknown"
        misaligned = copy.deepcopy(base)
        misaligned[0][0], misaligned[0][1] = misaligned[0][1], misaligned[0][0]
        duplicate = copy.deepcopy(base)
        for rows in (duplicate[0], duplicate[1], duplicate[3]):
            rows[1]["case_id"] = rows[0]["case_id"]
        missing = copy.deepcopy(base)
        for rows in missing:
            rows.pop(0)
        deficit = copy.deepcopy(base)
        deficit[0][0]["hard_pass"] = False
        incomplete = copy.deepcopy(base)
        incomplete[1][0].pop("hard_pass")
        for name, inputs in (
            ("unknown", unknown),
            ("misaligned", misaligned),
            ("duplicate", duplicate),
            ("missing", missing),
            ("deficit", deficit),
            ("incomplete", incomplete),
        ):
            with self.subTest(name=name):
                result = evaluate_bad_control(*inputs)
                self.assertEqual(result["status"], "EVALUATOR_BAD_CONTROL_FAILED")
                self.assertFalse(result["passed"])
