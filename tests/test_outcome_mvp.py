from __future__ import annotations

import hashlib
import io
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from unittest import mock

from mdseval.outcome_mvp import (
    CASE_SPECS,
    QUALIFICATION_COMMAND,
    analyze,
    build_schedule,
    integrity_snapshot,
    load_design,
    main,
    offline_null_calibration,
    qualify,
    require_environment,
    run_demonstration,
    write_reports,
)
from mdseval.hashing import tree_sha256
from mdseval.runner.base import RunResult

from tests.helpers import ROOT


DESIGN = ROOT / "experiments/coder-outcomes-v2-mvp.json"
TASKS = (
    "add-execution-waves",
    "add-period-summary",
    "compare-scheduled-instants",
    "deduplicate-running-balances",
    "integrate-event-deliveries",
    "integrate-warehouse-availability",
    "refactor-context-merge",
    "refactor-lazy-pagination",
)
TOKEN_FIELDS = (
    "input_tokens",
    "cached_input_tokens",
    "output_tokens",
    "reasoning_tokens",
    "total_tokens",
)
COMMIT = "a" * 40


class OutcomeMVPTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.design = load_design(DESIGN)

    def environment(self, **overrides: object) -> dict[str, object]:
        return {"verified_commit": COMMIT, "clean": True, "authentication_mode": "chatgpt_oauth",
                "isolated_runner_preflight_passed": True, **overrides}

    def qualification_receipt(self, **overrides: object) -> dict[str, object]:
        snapshot = integrity_snapshot(DESIGN, self.design)
        rows = [{"task_id": task, "case_id": case_id, "kind": kind, "repeat": repeat,
                 "expected": expected, "valid": True, "resolved": expected, "integrity": True, "passed": True}
                for task in TASKS for case_id, kind, expected in CASE_SPECS for repeat in range(1, 4)]
        canonical = lambda value: (json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n").encode()
        return {"schema_version": 1, "status": "PASS", "verified_commit": COMMIT,
                "authentication_mode": "chatgpt_oauth", "isolated_runner_preflight_passed": True,
                **{key: snapshot[key] for key in ("evaluator_sha256", "design_sha256", "analysis_sha256", "wrapper_sha256", "task_tree_sha256", "checker_hashes")},
                "oracle_sha256": self.design["qualification"]["oracle_sha256"],
                "command_config": QUALIFICATION_COMMAND,
                "command_config_sha256": hashlib.sha256(canonical(QUALIFICATION_COMMAND)).hexdigest(),
                "results": rows, "results_sha256": hashlib.sha256(canonical(rows)).hexdigest(), **overrides}

    def write_receipt(self, directory: Path, **overrides: object) -> Path:
        path = directory / "qualification-receipt.json"
        path.write_text(json.dumps(self.qualification_receipt(**overrides)), encoding="utf-8")
        return path

    def evidence(
        self,
        *,
        phase: str = "full",
        overrides: dict[tuple[str, str], bool] | None = None,
        retry: tuple[str, str] | None = None,
        invalid_base: bool = False,
        oracle: bool = True,
    ) -> dict[str, object]:
        waves = ("controls", "real") if phase == "full" else ("controls",)
        slots = build_schedule(self.design, TASKS, waves=waves, retry=retry)
        overrides = overrides or {}
        rows = []
        for slot in slots:
            task_index = TASKS.index(slot["task_id"])
            default = slot["label"] != "H" or task_index >= 6
            resolved = overrides.get((slot["label"], slot["task_id"]), default)
            valid = not (
                invalid_base
                and retry == (slot["wave"], slot["task_id"])
                and slot["block_attempt"] == 1
                and slot["label"] == sorted(
                    label
                    for label in self.design["bindings"]
                    if self.design["bindings"][label]["wave"] == slot["wave"]
                )[0]
            )
            rows.append(
                {
                    **slot,
                    "session_id": f"session-{slot['launch_index']}",
                    "workspace_id": f"workspace-{slot['launch_index']}",
                    "raw_artifact_path": f"raw/{slot['launch_index']}",
                    "instruction_sha256": self.design["bindings"][slot["label"]][
                        "sha256"
                    ],
                    "task_sha256": self.design["task_pack"]["task_hashes"][
                        slot["task_id"]
                    ],
                    "observation_valid": valid,
                    "objective_resolved": resolved if valid else None,
                    "subject_integrity": True,
                    "duration_seconds": 0.25,
                    "usage": {field: 1 for field in TOKEN_FIELDS},
                    "usage_reported": True,
                    "tool_calls": 0,
                    "tool_events_reported": True,
                    "raw_capture_path": f"raw/{slot['launch_index']}/events.jsonl",
                    "workspace_snapshot_path": f"raw/{slot['launch_index']}/workspace",
                    "baseline_tree_sha256": "b" * 64,
                    "final_tree_sha256": "c" * 64,
                    "workspace_patch": {"baseline_tree_sha256": "b" * 64,
                                        "final_tree_sha256": "c" * 64, "files": {}},
                    "workspace_contract_hashes": {"before": {"CODER.md": "d" * 64, ".issue-contract.md": "e" * 64},
                                                  "after": {"CODER.md": "d" * 64, ".issue-contract.md": "e" * 64}},
                }
            )
        snapshot = integrity_snapshot(DESIGN, self.design)
        return {
            "schema_version": 2,
            "task_ids": list(reversed(TASKS)),
            "qualification_receipt": self.qualification_receipt(status="PASS" if oracle else "FAIL"),
            "integrity_hashes": {"start": snapshot, "end": json.loads(json.dumps(snapshot))},
            "observations": rows,
            "errors": [],
        }

    def real_overrides(
        self, *, a: tuple[bool, ...], b: tuple[bool, ...]
    ) -> dict[tuple[str, str], bool]:
        values: dict[tuple[str, str], bool] = {}
        for index, task in enumerate(TASKS):
            for label in ("A1", "A2"):
                values[label, task] = a[index]
            for label in ("B1", "B2"):
                values[label, task] = b[index]
        return values

    def test_design_freezes_bindings_environment_and_qualification(self) -> None:
        self.assertEqual(set(self.design["bindings"]), {"C1", "C2", "H", "A1", "A2", "B1", "B2"})
        self.assertEqual(
            self.design["bindings"]["C1"]["sha256"],
            self.design["bindings"]["A2"]["sha256"],
        )
        self.assertNotEqual(
            self.design["bindings"]["H"]["sha256"],
            self.design["bindings"]["C1"]["sha256"],
        )
        self.assertNotIn("live_authorization", self.design)
        self.assertNotIn("implementation_paths", self.design)
        self.assertEqual(self.design["environment"]["authentication_mode"], "chatgpt_oauth")
        self.assertEqual(self.design["environment"]["max_wall_seconds"], 10800)
        self.assertEqual(self.design["qualification"]["repeats_per_case"], 3)

    def test_task_packet_metadata_hashes_and_exact_ids_are_enforced(self) -> None:
        packet = self.design["task_pack"]
        packet_root = ROOT / packet["path"]
        self.assertEqual(tree_sha256(packet_root), packet["tree_sha256"])
        self.assertEqual(tuple(packet["task_ids"]), TASKS)
        for repository, metadata in packet["repositories"].items():
            entries = json.loads((ROOT / metadata["tasks_path"]).read_text())
            self.assertEqual([item["id"] for item in entries], metadata["task_ids"])
            self.assertTrue(all(item["category"] == packet["categories"][item["id"]] for item in entries))
            self.assertEqual(tree_sha256(ROOT / metadata["fixture_path"]), metadata["fixture_sha256"])
            self.assertEqual(hashlib.sha256((ROOT / metadata["checker_path"]).read_bytes()).hexdigest(), metadata["checker_sha256"])
            self.assertEqual(repository + ".py", metadata["subject_file"])
        with self.assertRaisesRegex(ValueError, "eight unique task IDs"):
            build_schedule(self.design, tuple(f"wrong-{index}" for index in range(8)))

    def test_qualify_executes_120_cases_and_only_authoritative_mode_issues_receipt(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            provisional = qualify(DESIGN, root / "provisional")
            self.assertTrue(provisional["passed"])
            self.assertEqual(provisional["execution_count"], 120)
            self.assertFalse((root / "provisional/qualification-receipt.json").exists())
            outcomes = iter(expected for _task in TASKS for _case, _kind, expected in CASE_SPECS for _repeat in range(3))
            checker = lambda *_args: {"valid": True, "resolved": next(outcomes), "integrity": True, "stdout": "", "stderr": ""}
            authoritative = qualify(DESIGN, root / "authoritative", authoritative=True, checker=checker,
                                    observed_environment=self.environment())
            self.assertTrue(authoritative["passed"])
            receipt = json.loads((root / "authoritative/qualification-receipt.json").read_text())
            self.assertEqual((receipt["status"], len(receipt["results"])), ("PASS", 120))
            with self.assertRaises(FileExistsError):
                qualify(DESIGN, root / "authoritative", checker=checker)

    def test_checker_uses_captured_public_test_bytes(self) -> None:
        metadata = self.design["task_pack"]["repositories"]["ledger"]
        with tempfile.TemporaryDirectory() as temporary:
            fixture = Path(temporary) / "fixture"
            shutil.copytree(ROOT / metadata["fixture_path"], fixture)
            public = fixture / "test_public.py"
            original = public.read_bytes()
            (fixture / "ledger.py").write_text(
                '''from decimal import Decimal
import atexit
from pathlib import Path

public = Path(__file__).with_name("test_public.py")
saved = public.read_bytes()
public.write_text("import unittest\\n")
atexit.register(public.write_bytes, saved)

def running_balances(opening, entries):
    balance, result, seen = Decimal(opening), [], set()
    for entry in entries:
        if entry["id"] not in seen:
            seen.add(entry["id"])
            amount = Decimal(entry["amount"])
            balance += amount if entry["kind"] == "credit" else -amount
        result.append(format(balance, ".2f"))
    return result
''',
                encoding="utf-8",
            )
            process = subprocess.run(
                [sys.executable, "-B", str(ROOT / metadata["checker_path"]),
                 "deduplicate-running-balances", str(fixture)],
                text=True, capture_output=True, timeout=10,
            )
            self.assertEqual(process.returncode, 1)
            self.assertEqual(process.stderr, "")
            self.assertEqual(
                json.loads(process.stdout),
                {"code": "PUBLIC_REGRESSION_FAILURE", "ok": False,
                 "task": "deduplicate-running-balances"},
            )
            self.assertEqual(public.read_bytes(), original)

    def test_schedule_is_deterministic_balanced_fresh_and_capped(self) -> None:
        first = build_schedule(self.design, reversed(TASKS))
        self.assertEqual(first, build_schedule(self.design, TASKS))
        self.assertEqual(len(first), 56)
        self.assertEqual([row["launch_index"] for row in first], list(range(1, 57)))
        for task in TASKS:
            controls = [row["label"] for row in first if row["task_id"] == task and row["wave"] == "controls"]
            real = [row["label"] for row in first if row["task_id"] == task and row["wave"] == "real"]
            self.assertEqual(set(controls), {"C1", "C2", "H"})
            self.assertEqual(set(real), {"A1", "A2", "B1", "B2"})
        self.assertEqual(len({row["slot_id"] for row in first}), 56)
        self.assertEqual(len(build_schedule(self.design, TASKS, retry=("controls", TASKS[0]))), 59)
        self.assertEqual(len(build_schedule(self.design, TASKS, retry=("real", TASKS[0]))), 60)

    def test_null_calibration_enumerates_every_pattern_and_stays_below_alpha(self) -> None:
        result = offline_null_calibration()
        self.assertTrue(result["passed"])
        self.assertEqual(result["magnitude_patterns"], 3**8)
        self.assertEqual(result["sign_assignments_per_pattern"], 2**8)
        self.assertEqual(
            result["maximum_winner_probability"],
            {"numerator": 3, "denominator": 64, "value": 0.046875},
        )

    def test_ceiling_replay_and_aa_use_ordinary_chooser_without_a_winner(self) -> None:
        report = analyze(self.design, self.evidence())
        self.assertEqual((report["run_status"], report["verdict"]), ("COMPLETE", "INCONCLUSIVE"))
        self.assertEqual(report["aa_comparison"]["outcome"], "INCONCLUSIVE")
        self.assertTrue(report["control_gates"]["aa"])
        self.assertEqual(
            report["real_comparison"]["macro_pass_at_1"], {"A": 1.0, "B": 1.0}
        )

    def test_known_better_gate_uses_six_favorable_zero_adverse_and_exact_test(self) -> None:
        report = analyze(self.design, self.evidence(phase="controls"))
        control = report["known_better_comparison"]
        self.assertEqual((report["run_status"], report["verdict"]), ("CONTROL_PASSED", "INCONCLUSIVE"))
        self.assertEqual(control["outcome"], "A_BETTER")
        self.assertEqual((control["favorable_tasks"], control["adverse_tasks"]), (6, 0))
        self.assertEqual(control["p_value"], {"numerator": 1, "denominator": 32, "value": 0.03125})

    def test_real_chooser_covers_better_worse_and_inconclusive(self) -> None:
        cases = (
            ("B_BETTER", (False,) * 6 + (True,) * 2, (True,) * 8),
            ("A_BETTER", (True,) * 8, (False,) * 6 + (True,) * 2),
            ("INCONCLUSIVE", (False, True) * 4, (True, False) * 4),
        )
        for expected, a, b in cases:
            with self.subTest(expected=expected):
                report = analyze(
                    self.design,
                    self.evidence(overrides=self.real_overrides(a=a, b=b)),
                )
                self.assertEqual(report["verdict"], expected)
                self.assertIn(report["real_comparison"]["outcome"], {"A_BETTER", "B_BETTER", "INCONCLUSIVE"})

    def test_repeats_are_nested_in_task_macro_pass_at_one(self) -> None:
        overrides: dict[tuple[str, str], bool] = {}
        for task in TASKS:
            overrides["A1", task] = True
            overrides["A2", task] = False
            overrides["B1", task] = False
            overrides["B2", task] = False
        report = analyze(self.design, self.evidence(overrides=overrides))
        real = report["real_comparison"]
        self.assertEqual(real["macro_pass_at_1"], {"A": 0.5, "B": 0.0})
        self.assertTrue(all(row["pass_at_1_a"] == 0.5 for row in real["tasks"]))
        self.assertEqual(report["verdict"], "A_BETTER")

    def test_one_complete_block_retry_supersedes_all_original_calls(self) -> None:
        retry = ("real", TASKS[0])
        report = analyze(
            self.design,
            self.evidence(retry=retry, invalid_base=True),
        )
        self.assertEqual(report["verdict"], "INCONCLUSIVE")
        self.assertEqual(report["efficiency"]["launched_calls"], 60)
        self.assertEqual(report["efficiency"]["superseded_calls"], 4)
        self.assertEqual(report["efficiency"]["total_tokens"], 60)

    def test_integrity_failure_in_superseded_base_block_invalidates_run(self) -> None:
        retry = ("real", TASKS[0])
        evidence = self.evidence(retry=retry, invalid_base=True)
        base = next(
            row for row in evidence["observations"]  # type: ignore[union-attr]
            if row["wave"] == retry[0] and row["task_id"] == retry[1]
            and row["block_attempt"] == 1
        )
        base["subject_integrity"] = False
        report = analyze(self.design, evidence)
        self.assertEqual((report["run_status"], report["verdict"]), ("INVALID", "INVALID"))
        self.assertIn("integrity", report["reasons"][0])

    def test_fake_single_call_preserves_reconstruction_and_missing_usage(self) -> None:
        class Runner:
            def run(self, fixture, artifact, timeout, redactor):
                (fixture.repo / "subject-change.txt").write_text("changed", encoding="utf-8")
                artifact.mkdir(exist_ok=True)
                (artifact / "events.jsonl").write_text('{"type":"turn.completed"}\n', encoding="utf-8")
                return RunResult("COMPLETED", 0, 0.01)
        checker = lambda *_args: {"valid": True, "resolved": True, "integrity": False, "stdout": "", "stderr": ""}
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            report = run_demonstration(DESIGN, root / "run", self.write_receipt(root), runner=Runner(), checker=checker,
                                       observed_environment=self.environment())
            evidence = json.loads((root / "run/raw-evidence.json").read_text())
            row = evidence["observations"][0]
            self.assertEqual(report["verdict"], "INVALID")
            self.assertEqual((row["usage_reported"], row["usage"]["total_tokens"]), (False, None))
            self.assertEqual((row["tool_events_reported"], row["tool_calls"]), (True, 0))
            self.assertIn("subject-change.txt", row["workspace_patch"]["files"])
            self.assertTrue((root / "run" / row["workspace_snapshot_path"]).is_dir())
            self.assertTrue((root / "run" / row["raw_capture_path"]).is_file())
            self.assertNotIn("git_integrity", row)

    def test_run_rejects_missing_failed_stale_or_hash_mismatched_receipts_and_environment(self) -> None:
        runner = mock.Mock()
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            with self.assertRaises(FileNotFoundError):
                run_demonstration(DESIGN, root / "missing-run", root / "missing.json", runner=runner,
                                  observed_environment=self.environment())
            for name, override in (("failed", {"status": "FAIL"}), ("stale", {"verified_commit": "b" * 40}),
                                   ("abbreviated", {"verified_commit": "a" * 12}),
                                   ("malformed", {"verified_commit": "g" * 40}),
                                   ("hash", {"evaluator_sha256": "b" * 64}), ("results", {"results_sha256": "b" * 64})):
                directory = root / name
                directory.mkdir()
                with self.subTest(name=name), self.assertRaises(RuntimeError):
                    run_demonstration(DESIGN, root / f"{name}-run", self.write_receipt(directory, **override), runner=runner,
                                      observed_environment=self.environment())
        for name, override in (("dirty", {"clean": False}), ("abbreviated_commit", {"verified_commit": "a" * 12}),
                               ("malformed_commit", {"verified_commit": "g" * 40}),
                               ("auth", {"authentication_mode": "api_key"}),
                               ("preflight", {"isolated_runner_preflight_passed": False})):
            with self.subTest(name=name), self.assertRaises(RuntimeError):
                require_environment(DESIGN, self.design, self.environment(**override))
        runner.run.assert_not_called()

    def test_missing_efficiency_evidence_is_nullable_and_zero_tools_is_observed(self) -> None:
        tokens = self.evidence()
        tokens["observations"][0]["usage_reported"] = False  # type: ignore[index]
        tokens["observations"][0]["usage"] = {field: None for field in TOKEN_FIELDS}  # type: ignore[index]
        token_report = analyze(self.design, tokens)
        self.assertEqual(token_report["verdict"], "INCONCLUSIVE")
        self.assertEqual((token_report["efficiency"]["token_evidence_complete"], token_report["efficiency"]["total_tokens"]), (False, None))
        tools = self.evidence()
        tools["observations"][0]["tool_events_reported"] = False  # type: ignore[index]
        tools["observations"][0]["tool_calls"] = None  # type: ignore[index]
        tool_report = analyze(self.design, tools)
        self.assertEqual((tool_report["verdict"], tool_report["efficiency"]["tool_evidence_complete"], tool_report["efficiency"]["tool_calls"]),
                         ("INCONCLUSIVE", False, None))
        observed_zero = analyze(self.design, self.evidence())
        self.assertEqual((observed_zero["efficiency"]["tool_evidence_complete"], observed_zero["efficiency"]["tool_calls"]), (True, 0))

    def test_hash_contract_reconstruction_and_obsolete_fields_fail_closed(self) -> None:
        for field in ("evaluator_sha256", "design_sha256", "analysis_sha256", "wrapper_sha256", "task_tree_sha256"):
            evidence = self.evidence()
            evidence["integrity_hashes"]["end"][field] = "f" * 64  # type: ignore[index]
            with self.subTest(field=field):
                self.assertEqual(analyze(self.design, evidence)["verdict"], "INVALID")
        for field in ("checker_hashes", "treatment_hashes"):
            evidence = self.evidence()
            evidence["integrity_hashes"]["end"][field] = {}  # type: ignore[index]
            with self.subTest(field=field):
                self.assertEqual(analyze(self.design, evidence)["verdict"], "INVALID")
        cases = []
        contract = self.evidence()
        contract["observations"][0]["workspace_contract_hashes"]["after"]["CODER.md"] = "f" * 64  # type: ignore[index]
        cases.append(contract)
        for field in ("workspace_patch", "workspace_snapshot_path", "raw_capture_path", "baseline_tree_sha256", "final_tree_sha256"):
            evidence = self.evidence()
            evidence["observations"][0].pop(field)  # type: ignore[index]
            cases.append(evidence)
        patch_hash = self.evidence()
        patch_hash["observations"][0]["workspace_patch"]["final_tree_sha256"] = "f" * 64  # type: ignore[index]
        cases.append(patch_hash)
        wave = self.evidence()
        wave["wave_hashes"] = {"controls": {"before": "bad", "after": "bad"}}
        cases.append(wave)
        git = self.evidence()
        git["observations"][0]["git_integrity"] = {}  # type: ignore[index]
        cases.append(git)
        for evidence in cases:
            self.assertEqual(analyze(self.design, evidence)["verdict"], "INVALID")

    def test_cli_help_is_truthful_and_removed_arguments_are_rejected(self) -> None:
        output = io.StringIO()
        with self.assertRaises(SystemExit), redirect_stdout(output):
            main(["--help"])
        help_text = output.getvalue()
        self.assertTrue(all(command in help_text for command in ("qualify", "run", "replay")))
        self.assertTrue(all(value not in help_text for value in ("dollar", "oracle-controls", "implementation_paths")))
        for argument in ("--dollar-ceiling", "--max-wall-seconds", "--oracle-controls-passed", "--implementation-paths"):
            with self.subTest(argument=argument), self.assertRaises(SystemExit), redirect_stderr(io.StringIO()):
                main(["run", "run-dir", "receipt.json", argument, "1"])

    def test_unbalanced_invalid_integrity_and_gate_failures_are_fail_closed(self) -> None:
        cases = []
        missing = self.evidence()
        missing["observations"].pop()  # type: ignore[union-attr]
        cases.append((missing, "complete-block schedule"))
        no_retry = self.evidence()
        row = no_retry["observations"][0]  # type: ignore[index]
        row["observation_valid"], row["objective_resolved"] = False, None
        cases.append((no_retry, "retried as one whole block"))
        integrity = self.evidence()
        integrity["observations"][0]["subject_integrity"] = False  # type: ignore[index]
        cases.append((integrity, "integrity"))
        duplicate = self.evidence()
        duplicate["observations"][1]["workspace_id"] = duplicate["observations"][0]["workspace_id"]  # type: ignore[index]
        cases.append((duplicate, "raw and snapshot paths must be unique"))
        for evidence, reason in cases:
            with self.subTest(reason=reason):
                report = analyze(self.design, evidence)
                self.assertEqual((report["run_status"], report["verdict"]), ("INVALID", "INVALID"))
                self.assertIn(reason, report["reasons"][0])
        oracle = analyze(self.design, self.evidence(oracle=False))
        self.assertEqual((oracle["run_status"], oracle["verdict"]), ("INVALID", "INVALID"))

    def test_second_or_incomplete_retry_and_absolute_cap_are_invalid(self) -> None:
        retried = self.evidence(
            phase="controls", retry=("controls", TASKS[0]), invalid_base=True
        )
        extra_slots = build_schedule(
            self.design, TASKS, waves=("controls",), retry=("controls", TASKS[1])
        )
        extras = [row for row in extra_slots if row["block_attempt"] == 2]
        template = retried["observations"][0]  # type: ignore[index]
        for slot in extras:
            clone = {**template, **slot, "session_id": f"extra-s-{slot['label']}",
                     "workspace_id": f"extra-w-{slot['label']}", "raw_artifact_path": f"extra/{slot['label']}",
                     "instruction_sha256": self.design["bindings"][slot["label"]]["sha256"],
                     "observation_valid": True, "objective_resolved": True}
            retried["observations"].append(clone)  # type: ignore[union-attr]
        report = analyze(self.design, retried)
        self.assertEqual(report["verdict"], "INVALID")
        self.assertIn("more than one", report["reasons"][0])
        over_cap = self.evidence(retry=("real", TASKS[0]), invalid_base=True)
        over_cap["observations"].append(dict(over_cap["observations"][-1]))  # type: ignore[index,union-attr]
        capped = analyze(self.design, over_cap)
        self.assertEqual(capped["verdict"], "INVALID")
        self.assertIn("absolute", capped["reasons"][0])

    def test_reports_and_replay_are_deterministic_and_offline(self) -> None:
        evidence = self.evidence()
        report = analyze(self.design, evidence)
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            first, second = root / "first", root / "second"
            write_reports(first, report)
            write_reports(second, report)
            for name in ("report.json", "report.md"):
                self.assertEqual((first / name).read_bytes(), (second / name).read_bytes())
            raw = root / "raw.json"
            raw.write_text(json.dumps(evidence), encoding="utf-8")
            output = io.StringIO()
            with redirect_stdout(output):
                code = main(
                    ["--experiment", str(DESIGN), "replay", str(raw), str(root / "replay")]
                )
            self.assertEqual(code, 0)
            self.assertIn("VERDICT: INCONCLUSIVE", output.getvalue())
            replayed = json.loads((root / "replay/report.json").read_text())
            self.assertEqual(replayed, report)
            markdown = (root / "replay/report.md").read_text()
            self.assertIn("exact two-sided p=", markdown)
            self.assertIn("Non-significance is not equivalence", markdown)


if __name__ == "__main__":
    unittest.main()
