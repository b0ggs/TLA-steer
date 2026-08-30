from __future__ import annotations

from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from tla_steer.oracle import (  # noqa: E402
    ACTION_LABELS,
    EXPECTED_ACTION_COUNTS,
    EXPECTED_STATE_COUNT,
    EXPECTED_TRANSITION_COUNT,
    initial_state,
    is_type_correct_state,
    iter_type_correct_states,
    oracle_successor,
    self_check,
)


class TwoLightsOracleTests(unittest.TestCase):
    def test_exhaustive_self_check_matches_frozen_graph(self) -> None:
        summary = self_check()

        self.assertEqual(summary.state_count, EXPECTED_STATE_COUNT)
        self.assertEqual(summary.transition_count, EXPECTED_TRANSITION_COUNT)
        self.assertEqual(summary.reachable_state_count, EXPECTED_STATE_COUNT)
        self.assertEqual(dict(summary.action_counts), EXPECTED_ACTION_COUNTS)
        self.assertTrue(summary.as_dict()["all_type_correct_states_reachable"])

    def test_enumeration_is_exact_and_unique(self) -> None:
        states = list(iter_type_correct_states())
        keys = {
            (
                state["clock"],
                state["lightA"],
                state["timerA"],
                state["lightB"],
                state["timerB"],
            )
            for state in states
        }

        self.assertEqual(len(states), EXPECTED_STATE_COUNT)
        self.assertEqual(len(keys), EXPECTED_STATE_COUNT)
        self.assertTrue(all(is_type_correct_state(state) for state in states))

    def test_actions_are_pure_and_observe_boundary_guards(self) -> None:
        state = {
            "clock": 7,
            "lightA": "green",
            "timerA": 3,
            "lightB": "red",
            "timerB": 5,
        }
        before = dict(state)
        successor = oracle_successor("Tick", state)

        self.assertEqual(state, before)
        self.assertEqual(
            successor,
            {
                "clock": 0,
                "lightA": "green",
                "timerA": 4,
                "lightB": "red",
                "timerB": 6,
            },
        )

        maxed = dict(state)
        maxed["timerB"] = 6
        self.assertIsNone(oracle_successor("Tick", maxed))

        early = dict(state)
        early["timerA"] = 2
        self.assertIsNone(oracle_successor("AGreenToYellow", early))
        self.assertIsNotNone(oracle_successor("AGreenToYellow", state))

    def test_state_type_check_rejects_bool_and_shape_changes(self) -> None:
        valid = initial_state()
        self.assertTrue(is_type_correct_state(valid))

        boolean_clock = dict(valid)
        boolean_clock["clock"] = False
        self.assertFalse(is_type_correct_state(boolean_clock))

        extra_field = dict(valid)
        extra_field["extra"] = 1
        self.assertFalse(is_type_correct_state(extra_field))

    def test_action_label_order_is_frozen(self) -> None:
        self.assertEqual(tuple(EXPECTED_ACTION_COUNTS), ACTION_LABELS)


if __name__ == "__main__":
    unittest.main()
