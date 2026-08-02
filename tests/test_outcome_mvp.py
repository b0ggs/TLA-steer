from __future__ import annotations

import hashlib
import importlib.util
import io
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest import mock

from mdseval.outcome_mvp import (
    analyze,
    build_schedule,
    load_design,
    main,
    offline_null_calibration,
    require_live_authorization,
    run_demonstration,
    write_reports,
)
from mdseval.hashing import tree_sha256
from mdseval.runner.base import RunResult
from mdseval.runner.fake import FakeAdapter, FakePlan

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


class OutcomeMVPTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.design = load_design(DESIGN)

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
                }
            )
        return {
            "schema_version": 1,
            "task_ids": list(reversed(TASKS)),
            "oracle_controls_passed": oracle,
            "observations": rows,
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

    def test_design_freezes_bindings_settings_and_live_authorization(self) -> None:
        self.assertEqual(set(self.design["bindings"]), {"C1", "C2", "H", "A1", "A2", "B1", "B2"})
        self.assertEqual(
            self.design["bindings"]["C1"]["sha256"],
            self.design["bindings"]["A2"]["sha256"],
        )
        self.assertNotEqual(
            self.design["bindings"]["H"]["sha256"],
            self.design["bindings"]["C1"]["sha256"],
        )
        with self.assertRaisesRegex(RuntimeError, "positive dollar ceiling"):
            require_live_authorization(self.design)
        self.assertEqual(
            require_live_authorization(self.design, 25.0, 300.0),
            {"dollar_ceiling": 25.0, "max_wall_seconds": 300.0},
        )

    def test_task_packet_metadata_hashes_and_exact_ids_are_enforced(self) -> None:
        packet = self.design["task_pack"]
        packet_root = ROOT / packet["path"]
        self.assertEqual(tree_sha256(packet_root), packet["tree_sha256"])
        self.assertEqual(tuple(packet["task_ids"]), TASKS)
        self.assertEqual(len(self.design["implementation_paths"]), 20)
        for repository, metadata in packet["repositories"].items():
            entries = json.loads((ROOT / metadata["tasks_path"]).read_text())
            self.assertEqual([item["id"] for item in entries], metadata["task_ids"])
            self.assertTrue(all(item["category"] == packet["categories"][item["id"]] for item in entries))
            self.assertEqual(tree_sha256(ROOT / metadata["fixture_path"]), metadata["fixture_sha256"])
            self.assertEqual(hashlib.sha256((ROOT / metadata["checker_path"]).read_bytes()).hexdigest(), metadata["checker_sha256"])
            self.assertEqual(repository + ".py", metadata["subject_file"])
        with self.assertRaisesRegex(ValueError, "eight unique task IDs"):
            build_schedule(self.design, tuple(f"wrong-{index}" for index in range(8)))

    def test_manifest_byte_drift_is_rejected_without_mutating_frozen_packet(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            required = set(self.design["implementation_paths"])
            required.update(binding["path"] for binding in self.design["bindings"].values())
            for relative in required:
                destination = root / relative
                destination.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(ROOT / relative, destination)
            manifest = root / "evals/mvp/coder-outcomes-v2/ledger/tasks.json"
            manifest.write_bytes(manifest.read_bytes() + b"\n")
            copied_design = root / "experiments/coder-outcomes-v2-mvp.json"
            value = json.loads(copied_design.read_text())
            value["task_pack"]["tree_sha256"] = tree_sha256(
                root / value["task_pack"]["path"]
            )
            copied_design.write_text(json.dumps(value), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "task packet hash drift for ledger"):
                load_design(copied_design)

    def test_all_checkers_emit_stable_timeout_results(self) -> None:
        for repository, metadata in self.design["task_pack"]["repositories"].items():
            with self.subTest(repository=repository):
                path = ROOT / metadata["checker_path"]
                spec = importlib.util.spec_from_file_location(f"mvp_checker_{repository}", path)
                self.assertIsNotNone(spec and spec.loader)
                checker = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(checker)  # type: ignore[union-attr]
                fixture = ROOT / metadata["fixture_path"]
                with mock.patch.object(
                    checker.subprocess, "run",
                    side_effect=subprocess.TimeoutExpired([sys.executable], 15),
                ):
                    self.assertEqual(checker.run("pass", fixture), "TIMEOUT")
                output = io.StringIO()
                with mock.patch.object(checker, "run", return_value="TIMEOUT"), redirect_stdout(output):
                    code = checker.main(["check.py", metadata["task_ids"][0], str(fixture)])
                self.assertEqual(code, 1)
                self.assertEqual(
                    json.loads(output.getvalue()),
                    {"code": "SUBJECT_TIMEOUT", "ok": False, "task": metadata["task_ids"][0]},
                )

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

    def test_fake_live_run_gates_retries_and_preserves_manifest_bound_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            class Runner:
                def __init__(self, fault=None, at=0, drift=None):
                    self.fault, self.at, self.drift, self.calls = fault, at, drift, []
                def run(self, fixture, artifact, timeout, redactor):
                    index = len(self.calls); self.calls.append((fixture.case.id, hashlib.sha256((fixture.repo / "CODER.md").read_bytes()).hexdigest(), artifact, timeout))
                    if self.drift is not None and index == self.at: self.drift.write_bytes(b"drift\n")
                    if self.fault == "exception" and index == self.at: raise RuntimeError("transport")
                    plan = FakePlan(timed_out=self.fault == "timeout" and index == self.at,
                                    interrupted=self.fault == "interrupted" and index == self.at,
                                    malformed_event_line="{" if self.fault == "malformed" and index == self.at else None)
                    return FakeAdapter({fixture.case.id: plan}).run(fixture, artifact, timeout, redactor)
            def checking(*, fail_controls=False, integrity_at=None):
                calls = []
                def check(_path, task, workspace, _timeout):
                    index = len(calls); calls.append(task); digest = hashlib.sha256((workspace / "CODER.md").read_bytes()).hexdigest()
                    harmful = digest == self.design["bindings"]["H"]["sha256"]
                    resolved = True if fail_controls else not harmful or TASKS.index(task) >= 6
                    return {"valid": True, "resolved": resolved, "integrity": index != integrity_at, "stdout": "PASS" if resolved else "FAIL", "stderr": ""}
                return check, calls
            counter = 0
            def execute(name, runner, check=None, design=DESIGN):
                nonlocal counter
                counter += 1; check = check or checking()[0]
                return run_demonstration(design, root / f"{counter}-{name}", 1.0, 60.0, True, runner=runner, checker=check)
            live_patcher = mock.patch("mdseval.outcome_mvp.CodexCLI", side_effect=AssertionError("live"))
            network_patcher = mock.patch("mdseval.outcome_mvp.subprocess.run", side_effect=AssertionError("network"))
            judge_patcher = mock.patch("mdseval.runner.codex_cli.build_judge_command", side_effect=AssertionError("judge"))
            with live_patcher as live, network_patcher as network, judge_patcher as judge:
                missing = Runner()
                with self.assertRaisesRegex(RuntimeError, "LIVE_AUTHORIZATION_REQUIRED"):
                    run_demonstration(DESIGN, root / "missing", 0, 10, True, runner=missing, checker=checking()[0])
                false = Runner(); report = run_demonstration(DESIGN, root / "false", 1, 10, False, runner=false, checker=checking()[0])
                self.assertEqual((len(missing.calls), len(false.calls), report["verdict"]), (0, 0, "INVALID"))
                failed = Runner(); failed_check, _ = checking(fail_controls=True); failed_report = execute("failed", failed, failed_check)
                self.assertEqual((len(failed.calls), failed_report["run_status"]), (24, "STOP/REDESIGN"))
                success = Runner(); success_report = execute("success", success); success_raw = json.loads((root / f"{counter}-success/raw-evidence.json").read_text())
                self.assertEqual((len(success.calls), success_report["run_status"]), (56, "COMPLETE"))
                self.assertEqual([row["wave"] for row in success_raw["observations"][:24]], ["controls"] * 24)
                self.assertEqual([row["wave"] for row in success_raw["observations"][24:]], ["real"] * 32)
                for key in ("slot_id", "session_id", "workspace_id", "raw_artifact_path"):
                    self.assertEqual(len({row[key] for row in success_raw["observations"]}), 56)
                self.assertTrue(all((root / f"{counter}-success" / row["raw_artifact_path"] / "slot.json").is_file() for row in success_raw["observations"]))
                first = success_raw["observations"][0]; binding = self.design["bindings"][first["label"]]
                self.assertEqual(first["instruction_sha256"], hashlib.sha256((ROOT / binding["path"]).read_bytes()).hexdigest())
                metadata = next(value for value in self.design["task_pack"]["repositories"].values() if first["task_id"] in value["task_ids"])
                entry = next(item for item in json.loads((ROOT / metadata["tasks_path"]).read_text()) if item["id"] == first["task_id"])
                task_bytes = (json.dumps({"task": entry, **{key: metadata[key] for key in ("tasks_sha256", "checker_sha256", "fixture_sha256")}}, sort_keys=True, separators=(",", ":")) + "\n").encode()
                self.assertEqual(first["task_sha256"], hashlib.sha256(task_bytes).hexdigest())
                malformed = Runner("malformed", 0); execute("malformed", malformed); self.assertEqual(len(malformed.calls), 59)
                interrupted = Runner("interrupted", 24); execute("interrupted", interrupted); self.assertEqual(len(interrupted.calls), 60)
                timeout = Runner("timeout", 24); execute("timeout", timeout); timeout_raw = json.loads((root / f"{counter}-timeout/raw-evidence.json").read_text())
                self.assertEqual((len(timeout.calls), timeout_raw["observations"][24]["objective_resolved"]), (56, False))
                self.assertFalse(any(row["block_attempt"] == 2 for row in timeout_raw["observations"]))
                integrity = Runner(); integrity_check, _ = checking(integrity_at=0); integrity_report = execute("integrity", integrity, integrity_check)
                self.assertEqual((len(integrity.calls), integrity_report["verdict"]), (1, "INVALID"))
                exception = Runner("exception", 0); execute("exception", exception); exception_dir = root / f"{counter}-exception/raw/slot-01/runner"
                self.assertEqual(len(exception.calls), 59); self.assertTrue(all((exception_dir / name).is_file() for name in ("events.jsonl", "stderr.txt", "final.txt")))
                success_dir = root / "2-success/raw/slot-01/runner"; timeout_dir = root / "5-timeout/raw/slot-25/runner"
                self.assertTrue(all((directory / name).is_file() for directory in (success_dir, timeout_dir) for name in ("events.jsonl", "stderr.txt", "final.txt")))
                copied = root / "copied"; required = set(self.design["implementation_paths"]) | {value["path"] for value in self.design["bindings"].values()}
                for relative in required:
                    destination = copied / relative; destination.parent.mkdir(parents=True, exist_ok=True); shutil.copy2(ROOT / relative, destination)
                copied_design = copied / "experiments/coder-outcomes-v2-mvp.json"; drift_path = copied / self.design["bindings"]["C1"]["path"]
                drift = Runner(drift=drift_path); drift_report = execute("drift", drift, design=copied_design)
                self.assertEqual((len(drift.calls), drift_report["verdict"]), (1, "INVALID"))
                self.assertTrue(drift_path.read_bytes() == b"drift\n")
                live.assert_not_called(); network.assert_not_called(); judge.assert_not_called()

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
        cases.append((duplicate, "unique workspace_id"))
        for evidence, reason in cases:
            with self.subTest(reason=reason):
                report = analyze(self.design, evidence)
                self.assertEqual((report["run_status"], report["verdict"]), ("INVALID", "INVALID"))
                self.assertIn(reason, report["reasons"][0])
        oracle = analyze(self.design, self.evidence(oracle=False))
        self.assertEqual((oracle["run_status"], oracle["verdict"]), ("STOP/REDESIGN", "INVALID"))

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
        self.assertIn("cap exceeded", capped["reasons"][0])

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
