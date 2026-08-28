from __future__ import annotations

from contextlib import redirect_stderr, redirect_stdout
import hashlib
import io
import json
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts import analyze_cost_time_probe as analyzer


class CostTimeProbeAnalysisTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.batch = self.root / "runs" / "dev-v2" / "cost-time-probe-v1"
        self.analysis_output = self.root / "out" / "analysis.json"
        self.summary_output = self.root / "out" / "COST_TIME_PROBE_RESULT.md"

    def tearDown(self) -> None:
        self.temporary.cleanup()

    @staticmethod
    def _write_json(path: Path, value: object) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(value, sort_keys=True) + "\n", encoding="utf-8")

    @staticmethod
    def _digest(path: Path) -> str:
        return hashlib.sha256(path.read_bytes()).hexdigest()

    def request(
        self,
        task_ids: list[str],
        *,
        arm_names: tuple[str, str] = ("null", "probe"),
        reverse_arms: bool = False,
        probe_path: str = analyzer.PROBE_ARM_PATH,
    ) -> None:
        null_name, probe_name = arm_names
        arms = [
            {
                "name": null_name,
                "path": analyzer.NULL_ARM_PATH,
                "sha256": analyzer.EMPTY_SHA256,
            },
            {
                "name": probe_name,
                "path": probe_path,
                "sha256": "a" * 64,
            },
        ]
        if reverse_arms:
            arms.reverse()
        self._write_json(
            self.batch / "REQUEST.json",
            {
                "schema_version": 3,
                "batch_id": "cost-time-probe-v1",
                "tasks": [
                    {"id": task_id, "manifest_sha256": "b" * 64}
                    for task_id in task_ids
                ],
                "arms": arms,
                "call_count": len(task_ids) * 6,
                "max_total_calls": len(task_ids) * 8,
                "runner": {
                    "type": "codex-cli",
                    "model": "gpt-5.6-sol",
                    "reasoning_effort": "high",
                    "sandbox": "workspace-write",
                    "approval_policy": "never",
                    "subagents_enabled": False,
                    "network_for_agent_commands": False,
                    "max_parallel_runs": 1,
                    "timeout_seconds": 900,
                    "container": {
                        "image_digests": {
                            task_id: "sha256:" + "c" * 64 for task_id in task_ids
                        },
                        "interpreter_pins": {task_id: "3.11.5" for task_id in task_ids},
                        "spec_sha256": "d" * 64,
                        "web_search": "disabled",
                    },
                },
            },
        )
        for task_id in task_ids:
            for arm in arm_names:
                (self.batch / task_id / arm).mkdir(parents=True)

    def attempt(
        self,
        task_id: str,
        arm: str,
        ordinal: int,
        *,
        primary_tokens: int,
        duration: float,
        trajectory: int,
        usage_reported: bool = True,
        valid: bool = True,
        resolved: bool = True,
        timed_out: bool = False,
        changed_paths: list[str] | None = None,
    ) -> Path:
        attempt = self.batch / task_id / arm / f"attempt-{ordinal}"
        attempt.mkdir(parents=True)
        checker = {
            "requirements": {"R1": resolved},
            "regressions": {"G1": True},
            "resolved": resolved,
        }
        result = {
            "task_id": task_id,
            "arm": arm,
            "ordinal": ordinal,
            "valid": valid,
            "invalid_reason": "synthetic invalid attempt" if not valid else "",
            "timed_out": timed_out,
            "duration_seconds": duration,
            "requirements": checker["requirements"],
            "regressions": checker["regressions"],
            "resolved": resolved,
            "token_totals": {
                "input_tokens": primary_tokens + 15,
                "cached_input_tokens": 20,
                "output_tokens": 5,
                "usage_reported": usage_reported,
            },
        }
        events: list[dict[str, object]] = [
            {"type": "item.completed", "item": {"id": "message", "type": "agent_message"}}
        ]
        for index in range(trajectory):
            category = "command_execution" if index % 2 == 0 else "file_change"
            item = {"id": f"trajectory-{index}", "type": category}
            events.extend(
                [
                    {"type": "item.started", "item": item},
                    {"type": "item.completed", "item": item},
                ]
            )
            if index == 0:
                events.append({"type": "item.completed", "item": item})
        mcp = {"id": "mcp-1", "type": "mcp_tool_call"}
        events.extend(
            [
                {"type": "item.started", "item": mcp},
                {"type": "item.completed", "item": mcp},
            ]
        )
        self._write_json(attempt / "result.json", result)
        self._write_json(attempt / "checker.json", checker)
        self._write_json(
            attempt / "capture.json",
            {"changed_paths": changed_paths if changed_paths is not None else ["src/fix.py"]},
        )
        (attempt / "events.jsonl").write_text(
            "".join(json.dumps(event, sort_keys=True) + "\n" for event in events),
            encoding="utf-8",
        )
        files = {
            name: self._digest(attempt / name)
            for name in ("result.json", "checker.json", "capture.json", "events.jsonl")
        }
        self._write_json(attempt / "attempt-manifest.json", {"files": files})
        return attempt

    def unfinished_attempt(self, task_id: str, arm: str, ordinal: int) -> None:
        attempt = self.batch / task_id / arm / f"attempt-{ordinal}"
        attempt.mkdir(parents=True)
        self._write_json(attempt / "infra-invalid.json", {"error": "runner infrastructure failure"})
        self._write_json(attempt / "capture.json", {"changed_paths": ["diagnostics.log"]})
        item = {"id": "infra-command", "type": "command_execution"}
        (attempt / "events.jsonl").write_text(
            json.dumps({"type": "item.started", "item": item})
            + "\n"
            + json.dumps({"type": "item.completed", "item": item})
            + "\n",
            encoding="utf-8",
        )

    def fill_directional_batch(self, task_ids: list[str]) -> None:
        self.request(task_ids)
        for task_index, task_id in enumerate(task_ids):
            for ordinal in range(1, 4):
                self.attempt(
                    task_id,
                    "null",
                    ordinal,
                    primary_tokens=90 + ordinal * 10,
                    duration=9 + ordinal,
                    trajectory=ordinal,
                )
                probe_trajectory = ordinal + 4 if task_index < 3 else ordinal
                self.attempt(
                    task_id,
                    "probe",
                    ordinal,
                    primary_tokens=140 + ordinal * 10,
                    duration=19 + ordinal,
                    trajectory=probe_trajectory,
                    timed_out=task_index == 0 and ordinal == 3,
                    changed_paths=["src/fix.py", f"tests/test_{task_index}.py"],
                )

    def cli_args(self) -> list[str]:
        return [
            "--batch-dir",
            str(self.batch),
            "--analysis-output",
            str(self.analysis_output),
            "--summary-output",
            str(self.summary_output),
        ]

    def test_cli_reports_attempts_medians_censoring_and_trajectory_offline(self) -> None:
        task_ids = [f"task-{index}" for index in range(1, 5)]
        self.fill_directional_batch(task_ids)
        self.unfinished_attempt(task_ids[0], "null", 4)

        with (
            patch.object(subprocess, "run") as run,
            patch.object(subprocess, "Popen") as popen,
            redirect_stdout(io.StringIO()),
        ):
            self.assertEqual(analyzer.main(self.cli_args()), 0)
        run.assert_not_called()
        popen.assert_not_called()

        analysis = json.loads(self.analysis_output.read_text(encoding="utf-8"))
        first = analysis["tasks"][0]
        null = first["arms"]["null"]
        probe = first["arms"]["probe"]
        self.assertEqual(null["attempt_count"], 4)
        self.assertEqual(null["metrics"]["primary_token_cost"]["values"], [100, 110, 120])
        self.assertEqual(null["metrics"]["primary_token_cost"]["median"], 110)
        self.assertFalse(null["attempts"][3]["finalized"])
        self.assertEqual(
            null["attempts"][3]["exclusion_reason"],
            "not finalized: runner infrastructure failure",
        )
        self.assertEqual(null["attempts"][3]["trajectory_length"], 1)
        self.assertEqual(
            null["attempts"][3]["ordered_tool_call_categories"], ["command_execution"]
        )
        self.assertEqual(null["attempts"][3]["changed_paths"], ["diagnostics.log"])
        self.assertEqual(probe["attempts"][2]["recorded_duration_seconds"], 22)
        self.assertEqual(probe["attempts"][2]["wall_time_seconds"], 900)
        self.assertTrue(probe["attempts"][2]["wall_time_censored"])
        self.assertEqual(probe["attempts"][1]["trajectory_length"], 6)
        self.assertEqual(
            probe["attempts"][1]["ordered_tool_call_categories"],
            [
                "command_execution",
                "file_change",
                "command_execution",
                "file_change",
                "command_execution",
                "file_change",
            ],
        )
        self.assertEqual(
            probe["attempts"][0]["changed_paths"], ["src/fix.py", "tests/test_0.py"]
        )
        self.assertTrue(null["usage_completeness"]["complete"])
        self.assertEqual(null["usage_completeness"]["finalized_attempts"], 3)
        self.assertFalse(analysis["correctness_regression_risk"])
        for metric in analyzer.METRICS:
            self.assertEqual(
                analysis["classifications"][metric]["classification"],
                "DIRECTIONAL SIGNAL",
            )

        summary = self.summary_output.read_text(encoding="utf-8")
        self.assertIn("CORRECTNESS REGRESSION RISK: NO", summary)
        self.assertIn(">=900 (censored)", summary)
        self.assertIn("command_execution", summary)
        self.assertIn("`tests/test_0.py`", summary)
        self.assertNotIn("$", summary)
        self.assertNotIn("time_to_first", json.dumps(analysis))

    def test_metric_classifications_are_independent_of_usage_and_correctness(self) -> None:
        task_ids = [f"task-{index}" for index in range(1, 5)]
        self.request(task_ids)
        for task_index, task_id in enumerate(task_ids):
            for ordinal in range(1, 4):
                self.attempt(
                    task_id,
                    "null",
                    ordinal,
                    primary_tokens=90 + ordinal * 10,
                    duration=9 + ordinal,
                    trajectory=ordinal,
                )
                missing_usage = task_index >= 2 and ordinal >= 2
                invalid = task_index == 3 and ordinal == 3
                self.attempt(
                    task_id,
                    "probe",
                    ordinal,
                    primary_tokens=140 + ordinal * 10,
                    duration=19 + ordinal,
                    trajectory=ordinal + 4,
                    usage_reported=not missing_usage,
                    valid=not invalid,
                    resolved=not invalid,
                )

        analysis = analyzer.analyze_batch(self.batch)
        self.assertEqual(
            analysis["classifications"]["primary_token_cost"]["classification"],
            "NOT MEASURABLE",
        )
        self.assertEqual(
            analysis["classifications"]["primary_token_cost"]["measurable_task_count"],
            2,
        )
        for metric in ("wall_time_seconds", "trajectory_length"):
            self.assertEqual(
                analysis["classifications"][metric]["classification"],
                "DIRECTIONAL SIGNAL",
            )
        self.assertTrue(analysis["correctness_regression_risk"])
        risk = next(
            row
            for row in analysis["regression_risks"]
            if row["task_id"] == "task-4" and row["arm"] == "probe"
        )
        self.assertEqual(risk["score"], "2/3")
        summary = analyzer.render_summary(analysis)
        self.assertIn("| `null` | 12/12 |", summary)
        self.assertIn("| `probe` | 11/12 |", summary)
        self.assertIn("Quality gate failed", summary)
        invalid = analysis["tasks"][3]["arms"]["probe"]["attempts"][2]
        self.assertFalse(invalid["usable"])
        self.assertIn("synthetic invalid attempt", invalid["exclusion_reason"])
        self.assertFalse(invalid["metric_usable"]["wall_time_seconds"])

    def test_arm_roles_come_from_fixed_paths_not_labels_or_request_order(self) -> None:
        self.request(
            ["task-1"],
            arm_names=("zero-byte-control", "workflow-guidance"),
            reverse_arms=True,
        )

        analysis = analyzer.analyze_batch(self.batch)
        self.assertEqual(
            analysis["arm_roles"],
            {"null": "zero-byte-control", "probe": "workflow-guidance"},
        )
        self.assertEqual(
            analysis["arm_bindings"]["null"]["path"], analyzer.NULL_ARM_PATH
        )
        self.assertEqual(
            analysis["arm_bindings"]["probe"]["path"], analyzer.PROBE_ARM_PATH
        )
        with self.assertRaisesRegex(analyzer.AnalysisError, "conflicts"):
            analyzer.analyze_batch(self.batch, null_arm="workflow-guidance")

    def test_explicit_probe_path_binds_a_different_candidate(self) -> None:
        candidate_path = "controls/coder/evidence-bounded-v1.md"
        self.request(
            ["task-1"],
            arm_names=("zero-byte-control", "candidate"),
            probe_path=candidate_path,
        )

        with self.assertRaisesRegex(analyzer.AnalysisError, "must bind"):
            analyzer.analyze_batch(self.batch)
        analysis = analyzer.analyze_batch(self.batch, probe_path=candidate_path)
        self.assertEqual(
            analysis["arm_roles"],
            {"null": "zero-byte-control", "probe": "candidate"},
        )
        self.assertEqual(analysis["arm_bindings"]["probe"]["path"], candidate_path)

    def test_equal_to_null_range_is_not_a_directional_signal(self) -> None:
        task_ids = [f"task-{index}" for index in range(1, 4)]
        self.request(task_ids)
        for task_id in task_ids:
            for ordinal, null_tokens in enumerate((100, 110, 120), 1):
                self.attempt(
                    task_id,
                    "null",
                    ordinal,
                    primary_tokens=null_tokens,
                    duration=10 + ordinal,
                    trajectory=ordinal,
                )
            for ordinal, probe_tokens in enumerate((120, 130, 140), 1):
                self.attempt(
                    task_id,
                    "probe",
                    ordinal,
                    primary_tokens=probe_tokens,
                    duration=10 + ordinal,
                    trajectory=ordinal,
                )

        analysis = analyzer.analyze_batch(self.batch)
        classification = analysis["classifications"]["primary_token_cost"]
        self.assertEqual(classification["measurable_task_count"], 3)
        self.assertEqual(classification["classification"], "NO DIRECTIONAL SIGNAL")
        for task in analysis["tasks"]:
            comparison = task["comparisons"]["primary_token_cost"]
            self.assertEqual(comparison["probe_minus_null_median"], 20)
            self.assertEqual(comparison["null_arm_range"], 20)
            self.assertFalse(comparison["qualifies"])

    def test_negative_directional_signal_reports_probe_lower(self) -> None:
        task_ids = [f"task-{index}" for index in range(1, 4)]
        self.request(task_ids)
        for task_id in task_ids:
            for ordinal, null_tokens in enumerate((100, 110, 120), 1):
                self.attempt(
                    task_id,
                    "null",
                    ordinal,
                    primary_tokens=null_tokens,
                    duration=10,
                    trajectory=1,
                )
            for ordinal, probe_tokens in enumerate((40, 50, 60), 1):
                self.attempt(
                    task_id,
                    "probe",
                    ordinal,
                    primary_tokens=probe_tokens,
                    duration=10,
                    trajectory=1,
                )

        row = analyzer.analyze_batch(self.batch)["classifications"]["primary_token_cost"]
        self.assertEqual(row["classification"], "DIRECTIONAL SIGNAL")
        self.assertEqual(row["direction"], "probe lower than null")
        self.assertEqual(len(row["negative_qualifying_tasks"]), 3)

    def test_malformed_finalized_evidence_preserves_both_existing_outputs(self) -> None:
        self.request(["task-1"])
        for arm in ("null", "probe"):
            for ordinal in range(1, 4):
                self.attempt(
                    "task-1",
                    arm,
                    ordinal,
                    primary_tokens=100,
                    duration=10,
                    trajectory=1,
                )
        events = self.batch / "task-1" / "probe" / "attempt-2" / "events.jsonl"
        events.write_text("{malformed\n", encoding="utf-8")
        manifest_path = events.parent / "attempt-manifest.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        manifest["files"]["events.jsonl"] = self._digest(events)
        self._write_json(manifest_path, manifest)
        self.analysis_output.parent.mkdir(parents=True)
        self.analysis_output.write_text("old analysis\n", encoding="utf-8")
        self.summary_output.write_text("old summary\n", encoding="utf-8")

        stderr = io.StringIO()
        with redirect_stderr(stderr):
            self.assertEqual(analyzer.main(self.cli_args()), 2)
        self.assertIn("malformed event JSON", stderr.getvalue())
        self.assertEqual(self.analysis_output.read_text(encoding="utf-8"), "old analysis\n")
        self.assertEqual(self.summary_output.read_text(encoding="utf-8"), "old summary\n")


if __name__ == "__main__":
    unittest.main()
