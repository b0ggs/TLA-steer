from __future__ import annotations

import json
import threading
import time
import unittest
from pathlib import Path

from tla_steer.contract import (
    CONTROLLER_SCHEMA_VERSION,
    PROPOSAL_SCHEMA_VERSION,
    ContractError,
    Proposal,
    State,
    TARGET_SPECS,
    controller_from_json,
    validate_controller,
    validate_proposal,
)
from tla_steer.smc import (
    ActionObservation,
    IncrementalScore,
    SMCConfig,
    run_smc,
    score_action_observations,
    score_initial_state,
)


ROOT = Path(__file__).resolve().parents[1]


def state(
    *,
    clock: int = 0,
    light_a: str = "green",
    timer_a: int = 0,
    light_b: str = "red",
    timer_b: int = 2,
) -> dict[str, int | str]:
    return {
        "clock": clock,
        "lightA": light_a,
        "timerA": timer_a,
        "lightB": light_b,
        "timerB": timer_b,
    }


def controller_document() -> dict[str, object]:
    enabled = state()
    successor = state(clock=1, timer_a=1, timer_b=3)
    disabled = state(timer_a=6)
    steps: list[dict[str, object]] = []
    for target, (kind, symbol) in TARGET_SPECS.items():
        step_id = "initial" if kind == "initial" else symbol
        common: dict[str, object] = {
            "id": step_id,
            "kind": kind,
            "target": target,
            "python_symbol": symbol,
            "proposal_instruction": f"Produce only {symbol}.",
        }
        if kind == "initial":
            common["expected_initial"] = state()
        else:
            common["probes"] = [
                {"state": enabled, "expected_successor": successor},
                {"state": disabled, "expected_successor": None},
            ]
        steps.append(common)
    return {"schema_version": CONTROLLER_SCHEMA_VERSION, "steps": steps}


def proposal_for(step) -> Proposal:
    if step.kind == "initial":
        fragment = (
            'INITIAL = {"clock": 0, "lightA": "green", "timerA": 0, '
            '"lightB": "red", "timerB": 2}'
        )
    else:
        fragment = f"def {step.python_symbol}(state):\n    return None"
    return Proposal(
        schema_version=PROPOSAL_SCHEMA_VERSION,
        step_id=step.id,
        python_fragment=fragment,
    )


class ContractTests(unittest.TestCase):
    def test_controller_is_exactly_eight_balanced_semantic_steps(self) -> None:
        controller = validate_controller(controller_document())
        self.assertEqual(len(controller.steps), 8)
        self.assertEqual({step.target for step in controller.steps}, set(TARGET_SPECS))
        action = next(step for step in controller.steps if step.kind == "action")
        view = action.follower_view()
        self.assertIn("probe_states", view)
        self.assertNotIn("expected_successor", json.dumps(view))

        parsed = controller_from_json(json.dumps(controller.as_dict()))
        self.assertEqual(parsed, controller)

    def test_controller_rejects_missing_target_and_unbalanced_probes(self) -> None:
        missing = controller_document()
        steps = missing["steps"]
        assert isinstance(steps, list)
        steps[-1] = dict(steps[-2])
        steps[-1]["id"] = "duplicate_target_new_id"
        with self.assertRaisesRegex(ContractError, "semantic target"):
            validate_controller(missing)

        unbalanced = controller_document()
        action = unbalanced["steps"][1]
        assert isinstance(action, dict)
        probes = action["probes"]
        assert isinstance(probes, list)
        probes[1] = {
            "state": state(clock=2),
            "expected_successor": state(clock=3),
        }
        with self.assertRaisesRegex(ContractError, "expected-disabled"):
            validate_controller(unbalanced)

    def test_proposal_is_bound_to_step_and_one_fragment(self) -> None:
        controller = validate_controller(controller_document())
        action = controller.steps[1]
        valid = validate_proposal(proposal_for(action), step=action)
        self.assertEqual(valid.step_id, action.id)

        wrong = Proposal(
            schema_version=PROPOSAL_SCHEMA_VERSION,
            step_id=controller.steps[2].id,
            python_fragment=proposal_for(action).python_fragment,
        )
        with self.assertRaisesRegex(ContractError, "does not match"):
            validate_proposal(wrong, step=action)

        imported = Proposal(
            schema_version=PROPOSAL_SCHEMA_VERSION,
            step_id=action.id,
            python_fragment=(
                f"def {action.python_symbol}(state):\n"
                "    import os\n"
                "    return None"
            ),
        )
        with self.assertRaisesRegex(ContractError, "forbidden"):
            validate_proposal(imported, step=action)

    def test_output_schema_documents_are_valid_json_and_frozen_versions(self) -> None:
        controller_schema = json.loads(
            (ROOT / "schemas/controller.schema.json").read_text(encoding="utf-8")
        )
        proposal_schema = json.loads(
            (ROOT / "schemas/proposal.schema.json").read_text(encoding="utf-8")
        )
        self.assertEqual(
            controller_schema["properties"]["schema_version"]["const"],
            CONTROLLER_SCHEMA_VERSION,
        )
        self.assertEqual(
            proposal_schema["properties"]["schema_version"]["const"],
            PROPOSAL_SCHEMA_VERSION,
        )
        self.assertEqual(controller_schema["properties"]["steps"]["minItems"], 8)
        self.assertFalse(controller_schema["additionalProperties"])
        self.assertFalse(proposal_schema["additionalProperties"])


class IncrementalScoringTests(unittest.TestCase):
    def test_initial_score_counts_exact_fields(self) -> None:
        expected = State(0, "green", 0, "red", 2)
        exact = score_initial_state(expected, expected)
        wrong = score_initial_state(State(1, "green", 0, "red", 2), expected)
        self.assertEqual(exact.value, 1.0)
        self.assertEqual(wrong.value, 0.8)
        self.assertEqual(score_initial_state(None, expected).value, 0.0)

    def test_action_score_balances_enabledness_and_successor(self) -> None:
        enabled = State(1, "green", 1, "red", 3)
        perfect = score_action_observations(
            [
                ActionObservation(enabled, enabled),
                ActionObservation(None, None),
            ]
        )
        always_disabled = score_action_observations(
            [
                ActionObservation(enabled, None),
                ActionObservation(None, None),
            ]
        )
        wrong_successor = score_action_observations(
            [
                ActionObservation(enabled, State(2, "green", 1, "red", 3)),
                ActionObservation(None, None),
            ]
        )
        self.assertEqual(perfect.value, 1.0)
        self.assertEqual(always_disabled.value, 0.0)
        self.assertEqual(wrong_successor.value, 0.5)
        self.assertEqual(
            score_action_observations(
                [
                    ActionObservation(enabled, enabled, input_mutated=True),
                    ActionObservation(None, None),
                ]
            ).value,
            0.0,
        )


class SMCTests(unittest.TestCase):
    def test_deterministic_fake_run_forces_resampling_and_records_ancestry(self) -> None:
        controller = validate_controller(controller_document())
        active = 0
        maximum_active = 0
        calls = 0
        lock = threading.Lock()

        def follower(particle, step):
            nonlocal active, maximum_active, calls
            with lock:
                active += 1
                calls += 1
                maximum_active = max(maximum_active, active)
            time.sleep(0.003)
            with lock:
                active -= 1
            return proposal_for(step)

        def scorer(particle, step, proposal):
            if step.id == "initial":
                return 1.0 if particle.particle_id == "p00-0000" else 0.0
            return IncrementalScore(1.0, (("fake_exact", 1.0),))

        config = SMCConfig(population_size=8, concurrency=4, seed=17)
        result = run_smc(controller, follower, scorer, config=config)
        self.assertTrue(result.completed)
        self.assertEqual(result.stopping_reason, "completed")
        self.assertEqual(len(result.traces), 8)
        first = result.traces[0]
        self.assertTrue(first.resampled)
        self.assertEqual(first.ess, 1.0)
        self.assertEqual(set(first.ancestor_ids), {"p00-0000"})
        self.assertEqual(len(set(first.output_particle_ids)), 8)
        self.assertEqual(calls, 64)
        self.assertGreaterEqual(maximum_active, 2)
        self.assertLessEqual(maximum_active, 4)
        self.assertIsNotNone(result.official_particle)
        official = result.official_particle
        assert official is not None
        self.assertEqual(official.completed_step_index, 7)
        self.assertEqual(len(official.fragments), 8)
        self.assertEqual(official.ancestry, ("p00-0000",))

        again = run_smc(
            controller,
            lambda particle, step: proposal_for(step),
            scorer,
            config=config,
        )
        self.assertEqual(
            [trace.ancestor_ids for trace in again.traces],
            [trace.ancestor_ids for trace in result.traces],
        )
        self.assertEqual(
            again.official_particle_index, result.official_particle_index
        )

    def test_all_zero_increment_stops_with_particle_collapse(self) -> None:
        controller = validate_controller(controller_document())
        calls = 0

        def follower(particle, step):
            nonlocal calls
            calls += 1
            return proposal_for(step)

        result = run_smc(
            controller,
            follower,
            lambda particle, step, proposal: 0.0,
            config=SMCConfig(population_size=2, concurrency=2, seed=1),
        )
        self.assertTrue(result.collapsed)
        self.assertIsNone(result.official_particle)
        self.assertEqual(result.selection_weights, (0.0, 0.0))
        self.assertEqual(len(result.traces), 1)
        self.assertTrue(result.traces[0].particle_collapse)
        self.assertEqual(calls, 2)

    def test_official_output_is_seeded_weighted_draw_not_argmax(self) -> None:
        controller = validate_controller(controller_document())

        def scorer(particle, step, proposal):
            if step.id == controller.steps[-1].id:
                return 0.75 if particle.particle_id == "p00-0000" else 0.25
            return 1.0

        result = run_smc(
            controller,
            lambda particle, step: proposal_for(step),
            scorer,
            config=SMCConfig(population_size=2, concurrency=2, seed=2),
        )
        self.assertAlmostEqual(result.selection_weights[0], 0.75)
        self.assertAlmostEqual(result.selection_weights[1], 0.25)
        self.assertEqual(result.official_particle_index, 1)
        self.assertEqual(result.official_particle.particle_id, "p00-0001")
        self.assertLess(
            result.selection_weights[result.official_particle_index],
            max(result.selection_weights),
        )


if __name__ == "__main__":
    unittest.main()
