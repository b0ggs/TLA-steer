from __future__ import annotations

import json
from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
CANDIDATES = ROOT / "tests" / "fixtures" / "candidates"

from tla_steer.verifier import (  # noqa: E402
    EXACT,
    INVALID_CANDIDATE,
    SEMANTIC_MISMATCH,
    verify_candidate,
)


class TwoLightsVerifierTests(unittest.TestCase):
    def verify(self, name: str) -> dict[str, object]:
        result = verify_candidate(CANDIDATES / name)
        json.dumps(result)
        return result

    def test_golden_candidate_is_exact(self) -> None:
        result = self.verify("golden.py")

        self.assertEqual(result["outcome"], EXACT)
        self.assertTrue(result["exact"])
        self.assertTrue(result["initial_exact"])
        self.assertTrue(result["transition_sound"])
        self.assertTrue(result["transition_complete"])
        self.assertTrue(result["rooted_state_exact"])
        self.assertEqual(result["rooted_reachable_state_count"], 3_528)
        self.assertEqual(result["candidate_transition_count"], 6_960)
        self.assertEqual(result["observed_state_action_pairs"], 24_696)
        self.assertEqual(result["frame_violations"], 0)
        self.assertEqual(result["contract_failures"], [])

    def test_fallback_containment_is_labeled_honestly(self) -> None:
        result = self.verify("golden.py")

        self.assertEqual(result["containment_mode"], "prototype_local")
        self.assertEqual(result["runner"]["python_flags"], ["-I", "-S"])
        self.assertIn("not a hostile-code security boundary", result["containment_note"])

    def test_wrong_initial_is_not_hidden_by_equal_unrooted_graph(self) -> None:
        result = self.verify("wrong_initial.py")

        self.assertEqual(result["outcome"], SEMANTIC_MISMATCH)
        self.assertFalse(result["initial_exact"])
        self.assertTrue(result["transition_sound"])
        self.assertTrue(result["transition_complete"])
        self.assertTrue(result["rooted_state_exact"])
        self.assertEqual(result["counterexamples"][0]["kind"], "initial_mismatch")

    def test_loose_tick_guard_reports_extra_labeled_edges(self) -> None:
        result = self.verify("loose_tick_guard.py")

        self.assertEqual(result["outcome"], SEMANTIC_MISMATCH)
        self.assertFalse(result["transition_sound"])
        self.assertTrue(result["transition_complete"])
        self.assertGreater(result["per_action"]["Tick"]["false_positive"], 0)
        self.assertEqual(result["per_action"]["Tick"]["false_negative"], 0)

    def test_tight_guard_reports_missing_labeled_edges(self) -> None:
        result = self.verify("tight_a_red_guard.py")

        self.assertEqual(result["outcome"], SEMANTIC_MISMATCH)
        self.assertTrue(result["transition_sound"])
        self.assertFalse(result["transition_complete"])
        self.assertGreater(
            result["per_action"]["ARedToGreen"]["false_negative"], 0
        )
        self.assertEqual(result["per_action"]["ARedToGreen"]["false_positive"], 0)

    def test_copy_error_reports_wrong_successors_and_frame_violations(self) -> None:
        result = self.verify("frame_copy_error.py")

        self.assertEqual(result["outcome"], SEMANTIC_MISMATCH)
        self.assertGreater(
            result["per_action"]["BGreenToYellow"]["wrong_successor"], 0
        )
        self.assertGreater(result["frame_violations"], 0)
        self.assertGreater(result["frame_violation_fields"]["timerA"], 0)

    def test_input_mutation_is_an_invalid_candidate(self) -> None:
        result = self.verify("mutating_tick.py")

        self.assertEqual(result["outcome"], INVALID_CANDIDATE)
        self.assertFalse(result["exact"])
        self.assertTrue(result["runtime_failure"])
        self.assertIn("input_mutation", result["contract_failures"][0])
        self.assertEqual(result["counterexamples"][0]["action"], "Tick")


if __name__ == "__main__":
    unittest.main()
