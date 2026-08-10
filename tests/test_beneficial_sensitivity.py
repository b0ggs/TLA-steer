from __future__ import annotations

import hashlib
import io
import itertools
import json
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from fractions import Fraction
from pathlib import Path
from unittest import mock

from mdseval.beneficial_sensitivity import (
    GRID, STRATA, TASK_ID, _checker, analyze, build_schedules,
    classify_failure, compare, exact_sign_test, filtered_schedule, load_design,
    main, objective_resolved, replay, resume_boundary, retry_decision,
    runtime_matches, select_tasks, service_metadata, simulate, smoke_passes,
    stratified_bootstrap, verify_power,
)
from mdseval.hashing import sha256_file

ROOT = Path(__file__).resolve().parents[1]
DESIGN = ROOT / "experiments/coder-beneficial-sensitivity-m2.json"


class BeneficialSensitivityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.design = load_design(DESIGN)

    def mutated_design(self, change) -> Path:
        value = json.loads(DESIGN.read_text())
        change(value)
        temporary = tempfile.NamedTemporaryFile("w", suffix=".json", delete=False)
        with temporary:
            json.dump(value, temporary)
        self.addCleanup(Path(temporary.name).unlink, missing_ok=True)
        return Path(temporary.name)

    def evidence(self) -> dict:
        calibration = {task: [True, True, True, False, False, False] for task in TASK_ID}
        selection = select_tasks(self.design, {task: 3 for task in TASK_ID})
        selected = selection["selected_ids"]
        return {
            "schema": "mdseval.coder-beneficial-sensitivity-m2-evidence-v1",
            "launched_calls": 297,
            "calibration": calibration,
            "controls": {task: {"N1": [True], "N2": [True], "H": [False]} for task in selected},
            "helpful": {task: {"P": [True] * 4, "N": [False] * 4} for task in selected},
            "invalid": [], "superseded": [],
        }

    def test_config_hash_path_runtime_and_blockers_are_strict(self) -> None:
        self.assertEqual((self.design["runtime"]["model"], self.design["runtime"]["reasoning_effort"]), ("gpt-5.6-sol", "high"))
        self.assertEqual([item["id"] for item in self.design["blockers"]], ["B001", "B002", "B003", "B004"])
        self.assertEqual((ROOT / "controls/coder/null-m2.md").read_bytes(), b"")
        cases = (
            lambda d: d["runtime"].update(model="gpt-5.6-terra"),
            lambda d: d["runtime"].update(reasoning_effort="medium"),
            lambda d: d["runtime"].update(timeout_seconds=299),
            lambda d: d["runtime"].update(max_parallel_runs=2),
            lambda d: d["runtime"].update(network_for_agent_commands=True),
            lambda d: d.update(extra="override"),
            lambda d: d["treatments"]["null"].update(path="../escape"),
            lambda d: d["calls"].update(absolute_cap=315),
            lambda d: d["invalidity"].update(smoke_retry=True),
        )
        for change in cases:
            with self.subTest(change=change), self.assertRaises(ValueError):
                load_design(self.mutated_design(change), ROOT)

    def test_frozen_hashes_and_historical_v2_remain_bound(self) -> None:
        expected = self.design["artifacts"]
        for relative in ("src/mdseval/outcome_mvp.py", "tests/test_outcome_mvp.py", "experiments/coder-outcomes-v2-mvp.json", "evals/qualification/coder-outcomes-v2/oracle-variants.json"):
            self.assertEqual(sha256_file(ROOT / relative), expected[relative])
        self.assertEqual(sha256_file(ROOT / "controls/coder/no-implementation-v2.md"), "aaf88530c73385ad6d38a45dae67be4872e650afc27d620a8d640430e2ec5606")

    def test_schedules_are_opaque_balanced_frozen_and_capped(self) -> None:
        schedules = build_schedules(self.design)
        self.assertEqual(schedules, build_schedules(self.design))
        self.assertEqual({stage: len(rows) for stage, rows in schedules["base"].items()}, {"calibration": 120, "controls": 60, "helpful": 160})
        self.assertEqual({stage: len(rows) for stage, rows in schedules["fallback"].items()}, {"calibration": 120, "controls": 60, "helpful": 160})
        self.assertEqual(schedules["sentinels"], self.design["schedules"])
        self.assertTrue(all("treatment" not in row and row["opaque_arm_id"].startswith("O") for stage in schedules["base"].values() for row in stage))
        selected = select_tasks(self.design, {task: 3 for task in TASK_ID})["selected_ids"]
        controls, helpful = filtered_schedule(self.design, "controls", selected), filtered_schedule(self.design, "helpful", selected)
        self.assertEqual((len(controls["slots"]), len(helpful["slots"])), (48, 128))
        self.assertEqual(controls["slots"], [row for row in schedules["base"]["controls"] if row["task_id"] in selected])
        self.assertEqual((1 + 120 + 48 + 128, 1 + 126 + 51 + 136), (297, 314))
        self.assertEqual(len({row["slot_id"] for stage in schedules["base"].values() for row in stage}), 340)

    def test_selection_is_exact_balanced_and_stops_on_short_stratum(self) -> None:
        successes = {task: (index % 5) + 1 for index, task in enumerate(TASK_ID)}
        first = select_tasks(self.design, successes)
        self.assertEqual(first, select_tasks(self.design, successes))
        self.assertEqual(len(first["selected_ids"]), 16)
        for stratum in STRATA:
            self.assertEqual(sum(task.startswith(stratum + "-") for task in first["selected_ids"]), 4)
        for task in self.design["master"]["strata"]["feature"][:2]:
            successes[task] = 0
        stopped = select_tasks(self.design, successes)
        self.assertEqual((stopped["status"], stopped["selected_ids"]), ("SENSITIVITY_NOT_DEMONSTRATED", []))

    def test_retry_invalidity_and_resume_tables_are_arm_blind(self) -> None:
        replaceable = ("evaluator_failure", "machine_failure", "authentication_failure", "service_failure")
        for code in replaceable:
            self.assertEqual(classify_failure(self.design, code, False), "REPLACE_BLOCK")
            self.assertEqual(classify_failure(self.design, code, True), "Y_ZERO")
        for code in self.design["invalidity"]["score_zero"] + ["unexpected"]:
            self.assertEqual(classify_failure(self.design, code, False), "Y_ZERO")
        self.assertEqual(retry_decision("controls", 1), "FROZEN_FALLBACK_AT_STAGE_END")
        self.assertEqual(retry_decision("helpful", 2), "INVALID")
        self.assertEqual(retry_decision("calibration", 1, True), "INVALID")
        self.assertEqual(retry_decision("smoke", 1), "INVALID")
        cases = (("calibration", 1, True), ("controls", 3, True), ("controls", 2, False), ("helpful", 2, True), ("helpful", 1, False))
        for stage, count, expected in cases:
            self.assertIs(resume_boundary(stage, count), expected)

    def test_objective_requires_every_mechanical_field_without_override(self) -> None:
        payload = {"resolved": True, "environment": {"passed": True}, "requirements": {"R1": {"passed": True}, "R2": {"passed": True}}, "regressions": {"G1": {"passed": True}}, "integrity": {"passed": True}}
        self.assertTrue(objective_resolved(payload))
        for path in (("environment", "passed"), ("requirements", "R1"), ("regressions", "G1"), ("integrity", "passed")):
            changed = json.loads(json.dumps(payload))
            if path[1] == "passed": changed[path[0]]["passed"] = False
            else: changed[path[0]][path[1]]["passed"] = False
            self.assertFalse(objective_resolved(changed))
        payload["judge_override"] = True; payload["resolved"] = False
        self.assertFalse(objective_resolved(payload))

    @staticmethod
    def brute(differences) -> Fraction:
        nonzero = [value for value in differences if value]
        observed = abs(sum(nonzero, Fraction()))
        extreme = sum(abs(sum((value if sign else -value for value, sign in zip(nonzero, signs)), Fraction())) >= observed for signs in itertools.product((False, True), repeat=len(nonzero)))
        return Fraction(extreme, 1 << len(nonzero))

    def test_exact_sign_test_matches_bruteforce_for_every_k_through_16(self) -> None:
        for k in range(17):
            values = tuple(Fraction((index % 4) + 1, 4) * (-1 if index % 3 == 0 else 1) for index in range(k))
            result = exact_sign_test(values)
            self.assertEqual(Fraction(*result["fraction"]), self.brute(values))
            self.assertEqual(result["assignments"], 1 << k)
        result = exact_sign_test((Fraction(1),) * 6 + (Fraction(0),) * 10)
        self.assertEqual((result["nonzero"], result["fraction"]), (6, [1, 32]))

    def test_directional_rule_and_attainable_helpful_minimum(self) -> None:
        tasks = tuple(f"t-{index}" for index in range(16))
        a = {task: [True] * 4 for task in tasks}
        b = {task: [False] * 4 for task in tasks}
        strong = compare(a, b)
        self.assertTrue(strong["passes"])
        a = {task: [False] * 4 for task in tasks}
        for task in tasks[:13]: a[task][0] = True
        minimum = compare(a, b)
        self.assertEqual(minimum["effect"], [13, 64])
        self.assertTrue(minimum["passes"])
        aa = compare(a, a)
        self.assertFalse(aa["passes"])

    def test_bootstrap_uses_frozen_zero_based_endpoints(self) -> None:
        rows = {task: Fraction(index // 5, 4) for index, task in enumerate(TASK_ID)}
        strata = self.design["master"]["strata"]
        first = stratified_bootstrap(rows, strata)
        self.assertEqual(first, [0.375, 0.375])

    def test_protocol_power_grid_exact_draw_order(self) -> None:
        result = verify_power(self.design, 2000)
        self.assertEqual([(row["null"], row["helpful"], row["expected"]) for row in result["rows"]], list(GRID))
        self.assertEqual([round(row["observed"], 4) for row in result["rows"]], [.883, .865, .8355, .8485, .875, .925, .947])

    def test_all_verdicts_and_aa_name_are_fail_closed(self) -> None:
        evidence = self.evidence()
        with mock.patch("mdseval.beneficial_sensitivity.post_calibration_power", return_value=.9), mock.patch("mdseval.beneficial_sensitivity.stratified_bootstrap", return_value=[0.0, 1.0]):
            passed = analyze(self.design, evidence)
            self.assertEqual((passed["verdict"], passed["aa"]["gate"]), ("SENSITIVITY_DEMONSTRATED", "NO_FALSE_WINNER"))
            failed = json.loads(json.dumps(evidence)); selected = passed["selection"]["selected_ids"]
            failed["helpful"] = {task: {"P": [False] * 4, "N": [False] * 4} for task in selected}
            self.assertEqual(analyze(self.design, failed)["verdict"], "SENSITIVITY_NOT_DEMONSTRATED")
            failed = json.loads(json.dumps(evidence)); failed["controls"] = {task: {"N1": [False], "N2": [False], "H": [False]} for task in selected}
            self.assertEqual(analyze(self.design, failed)["verdict"], "SENSITIVITY_NOT_DEMONSTRATED")
            invalid = json.loads(json.dumps(evidence)); invalid["launched_calls"] = 315
            self.assertEqual(analyze(self.design, invalid)["verdict"], "INVALID")

    def test_fake_simulation_and_replay_are_offline_create_once_and_tamper_evident(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            with mock.patch("mdseval.beneficial_sensitivity.post_calibration_power", return_value=.9), mock.patch("mdseval.beneficial_sensitivity.stratified_bootstrap", return_value=[0.0, 1.0]):
                report = simulate(self.design, root / "simulation")
            self.assertEqual(report["verdict"], "SENSITIVITY_DEMONSTRATED")
            live = root / "runs/demo/live"; live.mkdir(parents=True)
            evidence = self.evidence(); evidence_path = live / "evidence.json"; evidence_path.write_text(json.dumps(evidence))
            manifest = {"design_sha256": sha256_file(DESIGN), "schedule_sentinels": self.design["schedules"], "evidence_sha256": sha256_file(evidence_path)}
            (live / "manifest.json").write_text(json.dumps(manifest))
            with mock.patch("mdseval.beneficial_sensitivity.post_calibration_power", return_value=.9), mock.patch("mdseval.beneficial_sensitivity.stratified_bootstrap", return_value=[0.0, 1.0]):
                replayed = replay(self.design, "demo", root)
            self.assertEqual(replayed, report)
            with self.assertRaises(FileExistsError), mock.patch("mdseval.beneficial_sensitivity.post_calibration_power", return_value=.9):
                replay(self.design, "demo", root)
            evidence_path.write_text("{}")
            (root / "runs/demo/replay").rename(root / "old-replay")
            with self.assertRaisesRegex(ValueError, "tampering"):
                replay(self.design, "demo", root)

    def test_offline_paths_do_not_import_or_construct_live_runner(self) -> None:
        with mock.patch("mdseval.runner.codex_cli.CodexCLI") as live:
            with tempfile.TemporaryDirectory() as temporary, mock.patch("mdseval.beneficial_sensitivity.post_calibration_power", return_value=.9), mock.patch("mdseval.beneficial_sensitivity.stratified_bootstrap", return_value=[0.0, 1.0]):
                simulate(self.design, Path(temporary) / "sim")
            with self.assertRaisesRegex(RuntimeError, "VALIDATION_BLOCKERS"):
                from mdseval.beneficial_sensitivity import run_stage
                run_stage(self.design, "demo", "smoke", Path("missing"))
            live.assert_not_called()

    def test_checker_uses_resolved_sys_executable_and_runtime_metadata_matches(self) -> None:
        outcome = mock.Mock(returncode=0, timed_out=False, interrupted=False, stdout=json.dumps({"resolved": False}), stderr="")
        with mock.patch("mdseval.beneficial_sensitivity.run_process_group", return_value=outcome) as called:
            _checker(ROOT / "evals/m2/coder-beneficial-sensitivity/bug-01/check.py", ROOT)
        self.assertEqual(called.call_args.args[0][0], str(Path(sys.executable).resolve()))
        requested = {"model": "gpt-5.6-sol", "reasoning_effort": "high"}
        self.assertTrue(runtime_matches(requested, requested))
        for observed in ({}, {"model": "gpt-5.6-sol"}, {"model": "other", "reasoning_effort": "high"}):
            self.assertFalse(runtime_matches(requested, observed))
        observed = service_metadata(({"type": "thread.started", "metadata": {"model": "gpt-5.6-sol", "model_reasoning_effort": "high"}},))
        result = mock.Mock(exit_code=0, timed_out=False, interrupted=False)
        self.assertTrue(smoke_passes(result, "IMPLEMENTED\nSMOKE_READY", (), True, requested, observed))
        for final, changed, complete, metadata in (("wrong", (), True, observed), ("IMPLEMENTED\nSMOKE_READY", ("x",), True, observed), ("IMPLEMENTED\nSMOKE_READY", (), False, observed), ("IMPLEMENTED\nSMOKE_READY", (), True, {})):
            self.assertFalse(smoke_passes(result, final, changed, complete, requested, metadata))

    def test_cli_is_exact_and_rejects_every_runtime_or_output_override(self) -> None:
        output = io.StringIO()
        with self.assertRaises(SystemExit), redirect_stdout(output):
            main(["--help"])
        self.assertTrue(all(command in output.getvalue() for command in ("validate", "qualify", "verify-power", "simulate", "run-stage", "replay")))
        with redirect_stdout(io.StringIO()):
            self.assertEqual(main(["validate", "--experiment", str(DESIGN)]), 1)
        for option in ("--model", "--reasoning-effort", "--timeout", "--network", "--parallelism", "--output"):
            with self.subTest(option=option), self.assertRaises(SystemExit), redirect_stderr(io.StringIO()):
                main(["run-stage", "--experiment", str(DESIGN), "--instance", "x", "--stage", "smoke", "--authorization-receipt", "x", option, "x"])


if __name__ == "__main__":
    unittest.main()
