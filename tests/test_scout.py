from __future__ import annotations

import errno
import hashlib
import json
import subprocess
import tempfile
import unittest
from pathlib import Path

from mdseval.capture import Redactor
from mdseval.hashing import tree_sha256
from mdseval.scout import (
    CHECKER_SOURCE,
    FAKE_SUBJECT_SOURCE,
    ScoutError,
    _capture_subject_launch,
    _write_live_launch_record,
    advance_rolling_campaign,
    _rolling_manifest,
    _rolling_disposition,
    _rolling_authorization,
    _write_json_once,
    build_fidelity_clearance,
    classify_infrastructure_failure,
    classify_rolling_task,
    canonical,
    classify_scout,
    load_cohort,
    load_config,
    record_launch,
    run_smoke,
    new_rolling_state,
    validate_rolling_semantic_clearance,
    validate_live_freeze,
    verify_rolling_evidence,
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

    @staticmethod
    def fidelity(
        task_id: str, *, passed: bool = True, root_cause: str | None = None,
        shared: bool = False, digest: str = "a" * 64,
    ) -> dict[str, object]:
        return {
            "schema": "mdseval.coder-beneficial-sensitivity-m2-launch-fidelity-v1",
            "static_clearance_sha256": digest, "static_status": "PASS",
            "task_id": task_id, "checker_binding_passed": True,
            "checker_workspace_unchanged": True,
            "protected_workspace_passed": passed,
            "task_fidelity_passed": passed,
            "root_cause": None if passed else (root_cause or f"protected:{task_id}"),
            "shared_recipe_or_admission_defect": shared,
        }

    @staticmethod
    def static_fidelity(cohort: dict[str, object]) -> dict[str, object]:
        qualification = ROOT / "runs/development/coder-beneficial-sensitivity-m2/scout-v1/qualification"
        return build_fidelity_clearance(cohort, qualification)

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
        static_fidelity = self.static_fidelity(cohort)
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
                    "fidelity_clearance": self.fidelity(
                        task_id, digest=static_fidelity["clearance_sha256"]
                    ),
                }
            )
        with self.assertRaisesRegex(ScoutError, "exact frozen 18"):
            classify_scout(cohort, attempts[:-1], static_fidelity)
        with self.assertRaisesRegex(ScoutError, "static fidelity clearance"):
            classify_scout(cohort, attempts)
        clearance = attempts[0].pop("fidelity_clearance")
        with self.assertRaisesRegex(ScoutError, "fidelity clearance"):
            classify_scout(cohort, attempts, static_fidelity)
        attempts[0]["fidelity_clearance"] = clearance
        report = classify_scout(cohort, attempts, static_fidelity)
        self.assertEqual(report["decision"], "SCOUT_PASS")
        self.assertEqual(set(report["witness_task_ids"]), witnesses)
        self.assertEqual(report["tasks"]["scout-a-bug-01"]["label"], "promising")
        attempts[0]["fidelity_clearance"] = self.fidelity(
            attempts[0]["task_id"], passed=False, root_cause="task-specific",
            digest=static_fidelity["clearance_sha256"],
        )
        failed = classify_scout(cohort, attempts, static_fidelity)
        self.assertEqual(failed["decision"], "SCOUT_NO_PASS")
        self.assertEqual(failed["tasks"][attempts[0]["task_id"]]["label"], "invalid")

        first_task = attempts[0]["task_id"]
        for attempt in attempts:
            attempt["fidelity_clearance"] = self.fidelity(
                attempt["task_id"],
                passed=attempt["task_id"] != first_task,
                root_cause="protected-workspace",
                digest=static_fidelity["clearance_sha256"],
            )
        isolated = classify_scout(cohort, attempts, static_fidelity)
        self.assertEqual(isolated["checker_fidelity_root_causes"], {"protected-workspace": 1})
        self.assertFalse(isolated["shared_fidelity_defect"])

        for attempt in attempts:
            attempt["fidelity_clearance"] = self.fidelity(
                attempt["task_id"], digest=static_fidelity["clearance_sha256"]
            )
        for task_id in ("scout-c-bug-01", "scout-c-integration-01"):
            attempt = next(item for item in attempts if item["task_id"] == task_id)
            attempt["fidelity_clearance"] = self.fidelity(
                task_id, passed=False, root_cause="checker-workspace",
                digest=static_fidelity["clearance_sha256"],
            )
        repeated = classify_scout(cohort, attempts, static_fidelity)
        self.assertEqual(repeated["checker_fidelity_root_causes"], {"checker-workspace": 2})
        self.assertTrue(repeated["shared_fidelity_defect"])
        self.assertEqual(repeated["decision"], "SCOUT_NO_PASS")

    def test_non_omission_failure_is_wrong_failure_mode(self) -> None:
        cohort = load_cohort(COHORT)
        static_fidelity = self.static_fidelity(cohort)
        bindings = {item["id"]: item for item in cohort["tasks"]}
        attempts = []
        for task_id in cohort["schedule"]:
            result = self.checker_result(bindings[task_id]["requirements"], 5, False)
            if task_id == "scout-a-bug-01":
                result["integrity"] = {"passed": False}
            attempts.append(
                {"task_id": task_id, "usable": True, "valid": True,
                 "checker_result": result,
                 "fidelity_clearance": self.fidelity(
                     task_id, digest=static_fidelity["clearance_sha256"])}
            )
        report = classify_scout(cohort, attempts, static_fidelity)
        self.assertEqual(
            report["tasks"]["scout-a-bug-01"]["label"], "wrong-failure-mode"
        )
        self.assertEqual(report["decision"], "SCOUT_NO_PASS")

    def test_generic_nonzero_with_scoreable_checker_is_usable(self) -> None:
        infrastructure = classify_infrastructure_failure(
            spawn_error=None,
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
            spawn_error=None,
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
            spawn_error=None,
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

    def test_spawn_oserror_is_structured_narrow_and_runtime_error_propagates(self) -> None:
        def missing() -> object:
            raise FileNotFoundError(errno.ENOENT, "spawn TOKEN=secret")

        outcome, reason = _capture_subject_launch(missing, Redactor())
        self.assertIsNone(outcome.returncode)
        self.assertEqual(
            reason,
            {"type": "FileNotFoundError", "message": "[Errno 2] spawn TOKEN=[REDACTED]",
             "errno": errno.ENOENT},
        )
        self.assertTrue(classify_infrastructure_failure(
            spawn_error=reason, timed_out=False, returncode=None,
            events_jsonl="", stderr="", final_text="", changed_paths=(), untracked=(),
        ))

        def unknown() -> object:
            raise OSError(999, "unknown spawn failure")

        _, unknown_reason = _capture_subject_launch(unknown, Redactor())
        self.assertFalse(classify_infrastructure_failure(
            spawn_error=unknown_reason, timed_out=False, returncode=None,
            events_jsonl="", stderr="", final_text="", changed_paths=(), untracked=(),
        ))
        with self.assertRaisesRegex(RuntimeError, "internal"):
            _capture_subject_launch(
                lambda: (_ for _ in ()).throw(RuntimeError("internal")), Redactor()
            )

    def test_freeze_validation_requires_exact_clean_descended_head(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            repo = Path(temporary)

            def git(*arguments: str) -> str:
                result = subprocess.run(
                    ["git", *arguments], cwd=repo, check=True,
                    stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
                )
                return result.stdout.strip()

            git("init", "-q", "--template=")
            git("config", "user.name", "Scout Test")
            git("config", "user.email", "scout@invalid.local")
            tracked = repo / "tracked.txt"
            tracked.write_text("one\n", encoding="utf-8")
            git("add", "tracked.txt")
            git("commit", "-q", "-m", "one")
            start = git("rev-parse", "HEAD")
            self.assertEqual(validate_live_freeze(repo, start, start)["freeze_commit"], start)
            with self.assertRaisesRegex(ScoutError, "full lowercase"):
                validate_live_freeze(repo, start, "short")
            tracked.write_text("dirty\n", encoding="utf-8")
            with self.assertRaisesRegex(ScoutError, "dirty"):
                validate_live_freeze(repo, start, start)
            tracked.write_text("two\n", encoding="utf-8")
            git("add", "tracked.txt")
            git("commit", "-q", "-m", "two")
            freeze = git("rev-parse", "HEAD")
            self.assertEqual(
                validate_live_freeze(repo, start, freeze)["authorization_start_commit"],
                start,
            )
            with self.assertRaisesRegex(ScoutError, "HEAD"):
                validate_live_freeze(repo, start, start)

    def test_static_fidelity_clearance_binds_all_offline_evidence(self) -> None:
        cohort = load_cohort(COHORT)
        qualification = ROOT / "runs/development/coder-beneficial-sensitivity-m2/scout-v1/qualification"
        clearance = build_fidelity_clearance(cohort, qualification)
        self.assertEqual(clearance["status"], "PASS")
        self.assertEqual(len(clearance["qualification"]["task_records"]), 6)
        self.assertEqual(clearance["admission"]["files"], cohort["admission_evidence"]["files"])
        self.assertEqual(len(clearance["clearance_sha256"]), 64)

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


class RollingScoutTests(unittest.TestCase):
    @staticmethod
    def roles() -> list[dict[str, str]]:
        return [{"author_id": f"a{index // 2}", "blind_validator_id": f"a{(index // 2 + 1) % 6}"} for index in range(12)]
    @staticmethod
    def binding(task_id: str, author: str = "author-a", family: str = "bug", recipe: str = "1" * 64, count: int = 8) -> dict[str, object]:
        return {
            "id": task_id, "author_id": author, "family_id": family,
            "requirements": [f"R{number}" for number in range(1, count + 1)],
            "recipe_sha256": recipe, "task_sha256": "2" * 64,
            "public_tree_sha256": "3" * 64, "checker_sha256": "4" * 64,
            "admission_sha256": "5" * 64, "reference_sha256": "6" * 64,
            "issue_contract_sha256": "7" * 64, "blind_submission_sha256": "8" * 64,
        }

    @staticmethod
    def attempts(binding: dict[str, object], kind: str = "promising", root: str | None = None, shared: bool = False) -> list[dict[str, object]]:
        requirements = binding["requirements"]
        passed_by_kind = {"promising": (len(requirements), 5, 5), "floor": (4, 4, 4), "ceiling": (len(requirements),) * 3}
        resolved_by_kind = {"promising": (True, False, False), "floor": (False,) * 3, "ceiling": (True,) * 3}
        attempts = []
        for passed, resolved in zip(passed_by_kind[kind], resolved_by_kind[kind]):
            fidelity_passed = root is None
            attempts.append({
                "task_id": binding["id"], "usable": True, "valid": fidelity_passed,
                "checker_result": ScoutPhaseBTests.checker_result(requirements, passed, resolved),
                "fidelity_clearance": ScoutPhaseBTests.fidelity(binding["id"], passed=fidelity_passed,
                    root_cause=root, shared=shared, digest="9" * 64),
            })
        return attempts
    @staticmethod
    def clearance(binding: dict[str, object], phase: str = "exploration") -> dict[str, object]:
        return {
            "schema": "mdseval.coder-beneficial-sensitivity-m2-rolling-semantic-clearance-v1",
            "status": "PASS", "task_id": binding["id"], "author_id": binding["author_id"],
            "phase": phase, "blind_validator_id": "validator", "semantic_reviewer_id": "gatekeeper-c",
            "clearance_stage": "after-blind-submission-before-subject-exposure",
            **{key: binding[key] for key in ("task_sha256", "public_tree_sha256", "checker_sha256",
                "admission_sha256", "issue_contract_sha256", "blind_submission_sha256", "recipe_sha256")},
            "scored_requirement_ids": binding["requirements"],
            "all_scored_requirements_in_scope": True, "all_checker_constraints_public": True,
            "hidden_specificity_absent": True, "scope_routing_contradictions_absent": True,
            "recipe_task_independent": True, "mechanical_admission_only": phase == "replication",
            "producer_received_only_frozen_recipe": phase == "replication",
        }
    @staticmethod
    def raw_launch(binding: dict[str, object], ordinal: int, header: dict[str, object], *, replacement: bool = False) -> dict[str, object]:
        result = ScoutPhaseBTests.checker_result(binding["requirements"], 4, False)
        checker = {"scoreable": True, "result": result}
        raw = {"events_jsonl": "", "stderr": "", "final": "" if replacement else "done", "checker_stdout": "", "checker_stderr": ""}
        static_base = {"schema": "mdseval.coder-beneficial-sensitivity-m2-fidelity-clearance-v1", "status": "PASS", "qualification": {"sha256": header["qualification_sha256"]}, "admission": {"semantic_clearance_sha256": header["clearance"]["sha256"]}, "shared_recipe_or_admission_defect": False}
        static = {**static_base, "clearance_sha256": hashlib.sha256(canonical(static_base)).hexdigest()}
        fidelity = ScoutPhaseBTests.fidelity(binding["id"], digest=static["clearance_sha256"])
        return {
            "schema": "mdseval.coder-beneficial-sensitivity-m2-live-launch-v1", "launch_ordinal": ordinal,
            "task_id": binding["id"], "author_id": binding["author_id"], "family_id": binding["family_id"],
            **header["freeze"], "runtime": header["execution"]["runtime"], "sandbox": header["execution"]["sandbox"],
            "wrapper_sha256": header["execution"]["wrapper"]["prompt_sha256"],
            "subject": {"spawn_error": {"type": "FileNotFoundError", "message": "missing", "errno": errno.ENOENT} if replacement else None, "timed_out": False, "returncode": None if replacement else 0},
            "git": {"changed_paths": [], "untracked": []}, "raw": raw, "checker": checker,
            "fidelity": {"static": static, "launch": fidelity}, "usable": not replacement, "infrastructure_failure": replacement,
            "raw_evidence_sha256": {**{key: hashlib.sha256(value.encode()).hexdigest() for key, value in raw.items()}, "checker": hashlib.sha256(canonical(checker)).hexdigest()},
        }
    def test_semantic_clearance_rejects_absent_scope_and_hidden_specificity(self) -> None:
        binding = self.binding("task-a", count=12)
        with self.assertRaisesRegex(ScoutError, "required"):
            validate_rolling_semantic_clearance(binding, None, phase="exploration")
        for field in ("all_scored_requirements_in_scope", "all_checker_constraints_public", "hidden_specificity_absent", "scope_routing_contradictions_absent"):
            clearance = self.clearance(binding)
            clearance[field] = False
            with self.assertRaisesRegex(ScoutError, "failed or drifted"):
                validate_rolling_semantic_clearance(binding, clearance, phase="exploration")
        self.assertEqual(validate_rolling_semantic_clearance(binding, self.clearance(binding), phase="exploration")["status"], "PASS")
        with self.assertRaisesRegex(ScoutError, "8 through 12"):
            validate_rolling_semantic_clearance(self.binding("short", count=7), None, phase="exploration")
        roles = self.roles(); execution = {"wrapper": {}, "runtime": {}, "sandbox": {}}
        candidate = {"campaign_id": "auth", "start_commit": "1" * 40, "task_root": "tasks", **execution}
        authorization = {"schema": "mdseval.coder-beneficial-sensitivity-m2-rolling-authorization-v1", "campaign_id": "auth", "start_commit": "1" * 40, "task_root": "tasks", "evidence_root": "evidence", "execution_sha256": hashlib.sha256(canonical(execution)).hexdigest(), "candidate_cap": 12, "planned_usable_attempt_cap": 36, "replacement_launch_cap": 1, "gatekeeper_id": "gatekeeper", "role_schedule": roles}
        bad_schedules = [{**authorization, "gatekeeper_id": "a0"}, {**authorization, "role_schedule": [*roles[:2], {**roles[2], "author_id": "a0"}, *roles[3:]]}, {**authorization, "role_schedule": [{**roles[0], "blind_validator_id": "outsider"}, *roles[1:]]}]
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary); evidence = root / "evidence"; evidence.mkdir(); path = root / "authorization.json"
            for bad in bad_schedules:
                path.write_bytes(canonical(bad))
                with self.assertRaisesRegex(ScoutError, "authorization"): _rolling_authorization(path, candidate, root, evidence)
        cli = subprocess.run(["python3", str(ROOT / "scripts/coder_beneficial_sensitivity_m2_scout.py"), "rolling-run"], capture_output=True, text=True)
        self.assertEqual((cli.returncode, json.loads(cli.stdout)["status"]), (1, "FAIL")); self.assertIn("requires explicit", cli.stdout)
    def test_task_classification_requires_three_contiguous_usable_attempts(self) -> None:
        binding = self.binding("task-a")
        attempts = self.attempts(binding)
        with self.assertRaisesRegex(ScoutError, "three contiguous"):
            classify_rolling_task(binding, attempts[:2])
        report = classify_rolling_task(binding, attempts)
        self.assertEqual((report["label"], report["q"], report["resolved_count"]), ("promising", 0.75, 1))
        attempts[1]["task_id"] = "other"
        with self.assertRaisesRegex(ScoutError, "three contiguous"):
            classify_rolling_task(binding, attempts)
        contradictory = self.attempts(binding)
        contradictory[0]["checker_result"]["resolved"] = False
        with self.assertRaisesRegex(ScoutError, "conjunction"):
            classify_rolling_task(binding, contradictory)
        empty_root = self.attempts(binding, root="x")
        empty_root[0]["fidelity_clearance"]["root_cause"] = ""
        with self.assertRaisesRegex(ScoutError, "fidelity"):
            classify_rolling_task(binding, empty_root)
    def test_campaign_explores_then_requires_independent_frozen_recipe_replica(self) -> None:
        state = new_rolling_state("campaign")
        floor = self.binding("floor", recipe="a" * 64)
        state = advance_rolling_campaign(state, floor, classify_rolling_task(floor, self.attempts(floor, "floor")))
        winner = self.binding("winner", "author-b", "integration", "b" * 64)
        state = advance_rolling_campaign(state, winner, classify_rolling_task(winner, self.attempts(winner)))
        self.assertEqual((state["status"], state["winner_task_id"]), ("REPLICATION", "winner"))
        for bad in (
            self.binding("wrong-recipe", "author-c", "feature", "c" * 64),
            self.binding("same-author", "author-b", "feature", "b" * 64),
            self.binding("same-family", "author-c", "integration", "b" * 64),
        ):
            with self.assertRaisesRegex(ScoutError, "replica"):
                advance_rolling_campaign(state, bad, classify_rolling_task(bad, self.attempts(bad)))
        replica = self.binding("replica", "author-c", "feature", "b" * 64)
        state = advance_rolling_campaign(state, replica, classify_rolling_task(replica, self.attempts(replica)))
        self.assertEqual((state["status"], state["witness_task_ids"]), ("ROLLING_PASS", ["winner", "replica"]))
        with self.assertRaisesRegex(ScoutError, "terminal"):
            advance_rolling_campaign(state, replica, classify_rolling_task(replica, self.attempts(replica)))
    def test_caps_rotation_and_repeated_fidelity_fail_closed(self) -> None:
        state = new_rolling_state("cap")
        for number in range(5):
            task = self.binding(f"floor-{number}", f"author-{number}", f"family-{number}", f"{number + 1:x}" * 64)
            state = advance_rolling_campaign(state, task, classify_rolling_task(task, self.attempts(task, "floor")))
        winner = self.binding("winner", "author-5", "family-5", "f" * 64)
        state = advance_rolling_campaign(state, winner, classify_rolling_task(winner, self.attempts(winner)))
        for number in range(6, 12):
            task = self.binding(f"rep-{number}", f"author-{number}", f"family-{number}", "f" * 64)
            state = advance_rolling_campaign(state, task, classify_rolling_task(task, self.attempts(task, "floor")))
        self.assertEqual((state["status"], len(state["candidates"]), state["planned_usable_attempts"]), ("ROLLING_NO_PASS", 12, 36))
        repeated = new_rolling_state("fidelity")
        for number in range(2):
            task = self.binding(f"bad-{number}", f"writer-{number}", f"kind-{number}")
            report = classify_rolling_task(task, self.attempts(task, root="checker-binding")); repeated = advance_rolling_campaign(repeated, task, report)
        self.assertEqual(repeated["status"], "ROLLING_NO_PASS")
        failed = new_rolling_state("six-floors")
        for number in range(6):
            task = self.binding(f"only-floor-{number}", f"new-{number}", f"new-kind-{number}")
            failed = advance_rolling_campaign(failed, task, classify_rolling_task(task, self.attempts(task, "floor")))
        self.assertEqual(failed["status"], "ROLLING_NO_PASS")
        rotated = new_rolling_state("rotation")
        for number in range(2):
            task = self.binding(f"twice-{number}", "same-author", f"family-{number}")
            rotated = advance_rolling_campaign(rotated, task, classify_rolling_task(task, self.attempts(task, "floor")))
        third = self.binding("third", "same-author", "family-3")
        with self.assertRaisesRegex(ScoutError, "two exposed"):
            advance_rolling_campaign(rotated, third, classify_rolling_task(third, self.attempts(third, "floor")))
    def test_exact_evidence_reconstructs_replacement_and_rejects_tampering(self) -> None:
        roles = self.roles()
        execution = {"wrapper": {"prompt_sha256": "f" * 64}, "runtime": {}, "sandbox": {}}
        authorization = {"campaign_id": "evidence", "start_commit": "3" * 40, "authorization_sha256": "a" * 64,
                         "gatekeeper_id": "gatekeeper", "role_schedule": roles,
                         "execution_sha256": hashlib.sha256(canonical(execution)).hexdigest(), "replacement_launch_cap": 1}
        with tempfile.TemporaryDirectory() as temporary:
            root, candidate = Path(temporary) / "rolling", Path(temporary) / "rolling/candidate-01"
            candidate.mkdir(parents=True)
            artifact, clearance_file, public = Path(temporary) / "candidate.json", Path(temporary) / "clearance.json", Path(temporary) / "public"
            artifact.write_text("candidate\n", encoding="utf-8"); clearance_file.write_text("clearance\n", encoding="utf-8")
            public.mkdir()
            binding = self.binding("first", "a0")
            _write_json_once(root / "manifest.json", _rolling_manifest(authorization))
            qualification_sha = _write_json_once(candidate / "qualification.json", {"status": "PASS"})
            header = {"schema": "mdseval.coder-beneficial-sensitivity-m2-rolling-header-v1", "ordinal": 1,
                      "campaign_id": "evidence", "phase": "exploration", "binding": binding,
                      "candidate": {"path": "candidate.json", "sha256": hashlib.sha256(artifact.read_bytes()).hexdigest()},
                      "clearance": {"path": "clearance.json", "sha256": hashlib.sha256(clearance_file.read_bytes()).hexdigest()},
                      "qualification_sha256": qualification_sha, "freeze": {"authorization_start_commit": "3" * 40, "freeze_commit": "4" * 40},
                      "roles": {**roles[0], "gatekeeper_id": "gatekeeper"}, "execution": execution,
                      "authorization_sha256": "a" * 64, "artifacts": {"candidate.json": hashlib.sha256(artifact.read_bytes()).hexdigest(), "clearance.json": hashlib.sha256(clearance_file.read_bytes()).hexdigest()},
                      "public": {"path": "public", "tree_sha256": tree_sha256(public)}}
            _write_json_once(candidate / "header.json", header)
            launches = [self.raw_launch(binding, index, header, replacement=index == 1) for index in range(1, 5)]
            for index, launch in enumerate(launches, 1): _write_json_once(candidate / f"launch-{index:03d}.json", launch)
            replay = verify_rolling_evidence(root, authorization, Path(temporary))
            self.assertEqual((len(replay["pending"]["attempts"]), replay["replacements"]), (3, 1))
            for bad_freeze in ({"authorization_start_commit": "2" * 40, "freeze_commit": "4" * 40}, {**header["freeze"], "extra": True}, {"authorization_start_commit": "3" * 40, "freeze_commit": "A" * 40}):
                (candidate / "header.json").write_bytes(canonical({**header, "freeze": bad_freeze}))
                with self.assertRaisesRegex(ScoutError, "freeze"): verify_rolling_evidence(root, authorization, Path(temporary))
            (candidate / "header.json").write_bytes(canonical(header))
            second = candidate / "launch-002.json"; original_second = second.read_bytes(); second.rename(candidate / "launch-005.json")
            with self.assertRaisesRegex(ScoutError, "contiguous"): verify_rolling_evidence(root, authorization, Path(temporary))
            (candidate / "launch-005.json").rename(second); second.write_bytes(canonical(self.raw_launch(binding, 2, header, replacement=True)))
            with self.assertRaisesRegex(ScoutError, "replacement launch cap"): verify_rolling_evidence(root, authorization, Path(temporary))
            second.write_bytes(original_second)
            (candidate / "header.json").write_bytes(canonical({**header, "roles": {**roles[2], "gatekeeper_id": "gatekeeper"}}))
            with self.assertRaisesRegex(ScoutError, "header drift"):
                verify_rolling_evidence(root, authorization, Path(temporary))
            (candidate / "header.json").write_bytes(canonical(header))
            artifact.write_text("drift\n", encoding="utf-8")
            with self.assertRaisesRegex(ScoutError, "prior exposed"):
                verify_rolling_evidence(root, authorization, Path(temporary))
            artifact.write_text("candidate\n", encoding="utf-8")
            (public / "link").symlink_to(artifact)
            with self.assertRaisesRegex(ScoutError, "public packet"):
                verify_rolling_evidence(root, authorization, Path(temporary))
            (public / "link").unlink()
            disposition = {"schema": "mdseval.coder-beneficial-sensitivity-m2-rolling-disposition-v1", "status": "PASS",
                           "task_id": "first", "gatekeeper_id": "gatekeeper", "header_sha256": hashlib.sha256((candidate / "header.json").read_bytes()).hexdigest(),
                           "qualification_sha256": qualification_sha, "launches": [{"path": f"launch-{i:03d}.json", "sha256": hashlib.sha256((candidate / f"launch-{i:03d}.json").read_bytes()).hexdigest()} for i in range(1, 5)],
                           "semantic_fidelity_passed": True, "root_cause": None, "shared_recipe_or_admission_defect": False}
            disposition_path = Path(temporary) / "disposition.json"; _write_json_once(disposition_path, disposition)
            self.assertTrue(_rolling_disposition(disposition_path, header, launches, candidate)["semantic_fidelity_passed"])
            disposition.update({"semantic_fidelity_passed": False, "root_cause": "shared-checker", "shared_recipe_or_admission_defect": True}); disposition_path.write_bytes(canonical(disposition))
            accepted = _rolling_disposition(disposition_path, header, launches, candidate)
            self.assertEqual((accepted["semantic_fidelity_passed"], accepted["shared_recipe_or_admission_defect"]), (False, True))
            disposition.update({"semantic_fidelity_passed": True, "root_cause": None}); disposition_path.write_bytes(canonical(disposition))
            with self.assertRaisesRegex(ScoutError, "disposition"): _rolling_disposition(disposition_path, header, launches, candidate)
            (candidate / "extra.json").write_text("{}\n", encoding="utf-8")
            with self.assertRaisesRegex(ScoutError, "incomplete or unexpected"):
                verify_rolling_evidence(root, authorization)

if __name__ == "__main__":
    unittest.main()
