from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from mdseval.scout import (
    CHECKER_SOURCE,
    FAKE_SUBJECT_SOURCE,
    ScoutError,
    _write_live_launch_record,
    classify_infrastructure_failure,
    classify_scout,
    load_cohort,
    load_config,
    record_launch,
    run_smoke,
    verify_smoke,
)


ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "experiments/coder-beneficial-sensitivity-m2-scout-v1.json"
COHORT = ROOT / "evals/development/coder-beneficial-sensitivity-m2/scout-v1/cohort-v1.json"


class ScoutSmokeTests(unittest.TestCase):
    def test_offline_smoke_captures_and_verifies_two_fresh_replays(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / "evidence"
            result = run_smoke(CONFIG, output)
            receipt = verify_smoke(output)
            self.assertEqual(result["status"], "PASS")
            self.assertEqual(result["live_model_calls"], 0)
            self.assertEqual(result["evidence_file_count"], 17)
            self.assertEqual(receipt["status"], "PASS")
            self.assertEqual(len(receipt["evidence"]), 16)
            self.assertEqual(load_config(CONFIG)["phase"], "A")

    def test_changed_protected_input_fails_without_pass_receipt(self) -> None:
        tampering_subject = FAKE_SUBJECT_SOURCE.replace(
            'print("IMPLEMENTED")',
            '(repo / "protected.txt").write_text("CHANGED\\n", encoding="utf-8")\nprint("IMPLEMENTED")',
        )
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / "evidence"
            with self.assertRaisesRegex(ScoutError, "protected input changed"):
                run_smoke(CONFIG, output, fake_subject_source=tampering_subject)
            self.assertFalse((output / "receipt.json").exists())

    def test_malformed_checker_output_fails_closed(self) -> None:
        malformed_checker = 'print("not-json")\n'
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / "evidence"
            with self.assertRaisesRegex(ScoutError, "malformed checker output"):
                run_smoke(CONFIG, output, checker_source=malformed_checker)
            self.assertFalse((output / "receipt.json").exists())

    def test_missing_or_modified_evidence_fails_verification(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            missing = root / "missing"
            run_smoke(CONFIG, missing)
            (missing / "replay-02/subject.stdout.txt").unlink()
            with self.assertRaisesRegex(ScoutError, "missing or unexpected"):
                verify_smoke(missing)

            modified = root / "modified"
            run_smoke(CONFIG, modified)
            (modified / "manifest.json").write_text("{}\n", encoding="utf-8")
            with self.assertRaisesRegex(ScoutError, "evidence hash drift"):
                verify_smoke(modified)

    def test_existing_output_is_not_overwritten(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / "evidence"
            run_smoke(CONFIG, output)
            with self.assertRaisesRegex(ScoutError, "create-once"):
                run_smoke(CONFIG, output)


class ScoutPhaseBTests(unittest.TestCase):
    @staticmethod
    def checker_result(requirements: list[str], passed: int, resolved: bool) -> dict[str, object]:
        return {
            "environment": {"passed": True},
            "integrity": {"passed": True},
            "regressions": {"G1": {"passed": True}},
            "requirements": {
                name: {"passed": index < passed}
                for index, name in enumerate(requirements)
            },
            "resolved": resolved,
        }

    def test_frozen_cohort_binds_six_tasks_and_exact_runtime(self) -> None:
        cohort = load_cohort(COHORT)
        self.assertEqual(len(cohort["tasks"]), 6)
        self.assertEqual(len(cohort["schedule"]), 18)
        self.assertEqual(cohort["runtime"]["model"], "gpt-5.6-sol")
        self.assertEqual(cohort["runtime"]["reasoning_effort"], "high")
        self.assertEqual(cohort["runtime"]["timeout_seconds"], 300)
        self.assertFalse(cohort["sandbox"]["network_access"])
        self.assertFalse(cohort["sandbox"]["subagents_enabled"])

    def test_replacement_caps_do_not_advance_usable_schedule(self) -> None:
        cohort = load_cohort(COHORT)
        state: dict[str, object] = {
            "launches": 0,
            "usable": 0,
            "replacements": 0,
            "replacements_by_author": {},
        }
        task_id = cohort["schedule"][0]
        state = record_launch(
            cohort, state, task_id, usable=False, infrastructure_failure=True
        )
        state = record_launch(
            cohort, state, task_id, usable=False, infrastructure_failure=True
        )
        self.assertEqual(state["usable"], 0)
        self.assertEqual(state["replacements"], 2)
        with self.assertRaisesRegex(ScoutError, "replacement cap"):
            record_launch(
                cohort, state, task_id, usable=False, infrastructure_failure=True
            )

    def test_section_13_classification_requires_exact_18_and_finds_witness(self) -> None:
        cohort = load_cohort(COHORT)
        bindings = {item["id"]: item for item in cohort["tasks"]}
        witnesses = {"scout-a-bug-01", "scout-b-integration-01"}
        seen: dict[str, int] = {}
        attempts: list[dict[str, object]] = []
        for task_id in cohort["schedule"]:
            occurrence = seen.get(task_id, 0)
            seen[task_id] = occurrence + 1
            requirement_ids = bindings[task_id]["requirements"]
            if task_id in witnesses:
                resolved = occurrence == 0
                passed = 8 if resolved else 5
            else:
                resolved = False
                passed = 0
            attempts.append(
                {
                    "task_id": task_id,
                    "usable": True,
                    "valid": True,
                    "checker_result": self.checker_result(
                        requirement_ids, passed, resolved
                    ),
                    "fidelity_defect": False,
                }
            )
        with self.assertRaisesRegex(ScoutError, "exact frozen 18"):
            classify_scout(cohort, attempts[:-1])
        report = classify_scout(cohort, attempts)
        self.assertEqual(report["decision"], "SCOUT_PASS")
        self.assertEqual(set(report["witness_task_ids"]), witnesses)
        self.assertEqual(report["tasks"]["scout-a-bug-01"]["label"], "promising")

    def test_non_omission_failure_is_wrong_failure_mode(self) -> None:
        cohort = load_cohort(COHORT)
        bindings = {item["id"]: item for item in cohort["tasks"]}
        attempts = []
        for task_id in cohort["schedule"]:
            result = self.checker_result(bindings[task_id]["requirements"], 5, False)
            if task_id == "scout-a-bug-01":
                result["integrity"] = {"passed": False}
            attempts.append(
                {"task_id": task_id, "usable": True, "valid": True,
                 "checker_result": result, "fidelity_defect": False}
            )
        report = classify_scout(cohort, attempts)
        self.assertEqual(
            report["tasks"]["scout-a-bug-01"]["label"], "wrong-failure-mode"
        )
        self.assertEqual(report["decision"], "SCOUT_NO_PASS")

    def test_generic_nonzero_with_scoreable_checker_is_usable(self) -> None:
        infrastructure = classify_infrastructure_failure(
            launch_exception="",
            timed_out=False,
            returncode=7,
            events_jsonl="",
            stderr="generic command failure",
            final_text="",
            changed_paths=(),
            untracked=(),
        )
        checker_scoreable = True
        self.assertFalse(infrastructure)
        self.assertTrue(checker_scoreable and not infrastructure)

    def test_explicit_pre_output_auth_failure_is_replaceable(self) -> None:
        event = json.dumps(
            {"type": "error", "message": "Authentication failed: login required"}
        ) + "\n"
        infrastructure = classify_infrastructure_failure(
            launch_exception="",
            timed_out=False,
            returncode=1,
            events_jsonl=event,
            stderr="",
            final_text="",
            changed_paths=(),
            untracked=(),
        )
        self.assertTrue(infrastructure)
        cohort = load_cohort(COHORT)
        state = record_launch(
            cohort,
            {"launches": 0, "usable": 0, "replacements": 0,
             "replacements_by_author": {}},
            cohort["schedule"][0],
            usable=False,
            infrastructure_failure=infrastructure,
        )
        self.assertEqual(state["replacements"], 1)
        self.assertEqual(state["usable"], 0)

    def test_scoreable_timeout_is_usable(self) -> None:
        infrastructure = classify_infrastructure_failure(
            launch_exception="",
            timed_out=True,
            returncode=None,
            events_jsonl="",
            stderr="transport error",
            final_text="",
            changed_paths=(),
            untracked=(),
        )
        checker_scoreable = True
        self.assertFalse(infrastructure)
        self.assertTrue(checker_scoreable and not infrastructure)

    def test_live_launch_evidence_is_one_canonical_create_once_file(self) -> None:
        record = {
            "schema": "mdseval.coder-beneficial-sensitivity-m2-live-launch-v1",
            "raw": {
                "events_jsonl": '{"type":"turn.started"}\n',
                "stderr": "stderr bytes as redacted text\n",
                "final": "IMPLEMENTED\n",
                "checker_stdout": '{"resolved":true}\n',
                "checker_stderr": "",
            },
            "checker": {"scoreable": True, "result": {"resolved": True}},
            "command": ["codex", "exec"],
            "git": {"diff": ""},
        }
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            _write_live_launch_record(root, 1, record)
            paths = [path for path in root.rglob("*") if path.is_file()]
            self.assertEqual([path.name for path in paths], ["launch-001.json"])
            self.assertEqual(json.loads(paths[0].read_text(encoding="utf-8")), record)
            with self.assertRaisesRegex(ScoutError, "create-once"):
                _write_live_launch_record(root, 1, record)

    def test_worst_case_evidence_path_count_stays_below_cap(self) -> None:
        evidence = ROOT / "runs/development/coder-beneficial-sensitivity-m2/scout-v1"
        phase_a_expected = {"comparison.json", "manifest.json", "receipt.json"} | {
            f"replay-{replay:02d}/{name}"
            for replay in (1, 2)
            for name in ("checker.json", "checker.stderr.txt", "checker.stdout.txt",
                         "result.json", "subject.json", "subject.stderr.txt",
                         "subject.stdout.txt")
        }
        phase_a_actual = {
            path.relative_to(evidence).as_posix()
            for path in evidence.glob("replay-*/*") if path.is_file()
        } | {path.name for path in evidence.iterdir() if path.is_file()}
        cohort = load_cohort(COHORT)
        admission_expected = set(cohort["admission_evidence"]["files"])
        admission_actual = {
            path.relative_to(evidence / "admission").as_posix()
            for path in (evidence / "admission").rglob("*") if path.is_file()
        }
        qualification_expected = {"manifest.json", "summary.json"} | {
            f"tasks/{task['id']}.json" for task in cohort["tasks"]
        }
        qualification_actual = {
            path.relative_to(evidence / "qualification").as_posix()
            for path in (evidence / "qualification").rglob("*") if path.is_file()
        }
        self.assertEqual((phase_a_actual, admission_actual, qualification_actual),
                         (phase_a_expected, admission_expected, qualification_expected))
        existing = sum(map(len, (phase_a_actual, admission_actual, qualification_actual)))
        self.assertEqual(existing, 45)
        live_maximum = cohort["replacements"]["absolute_launch_max"] + 2
        self.assertLessEqual(existing + live_maximum, 200)


if __name__ == "__main__":
    unittest.main()
