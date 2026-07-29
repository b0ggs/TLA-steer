from __future__ import annotations

import json
import shutil
import tempfile
import unittest
import uuid
from unittest import mock

from mdseval.execution import execute_pair_experiment
from mdseval.execution import create_run_directory
from mdseval.runner.fake import FakeAdapter, FakePlan

from tests.helpers import experiment


class FakeEndToEndTests(unittest.TestCase):
    def test_fake_demo_emits_complete_artifact_contract(self) -> None:
        config = experiment()
        run_id = f"test-fake-{uuid.uuid4().hex}"
        run_dir = None
        try:
            run_dir, comparisons, _ = execute_pair_experiment(
                experiment=config,
                runner=FakeAdapter(
                    {
                        "ambiguity-must-clarify": FakePlan(
                            final_text="NEEDS_CLARIFICATION\nWhich format is approved?\n"
                        )
                    }
                ),
                variant_a="champion",
                variant_b="karpathy-v1",
                suite="smoke",
                repeats=1,
                fake=True,
                run_id=run_id,
                run_judge=False,
            )
            report = json.loads((run_dir / "report.json").read_text())
            self.assertEqual(report["verdict"], "NOT_RUN")
            self.assertFalse(report["quality_claim_established"])
            required = {
                "manifest.json",
                "events.jsonl",
                "stderr.txt",
                "final.txt",
                "git-status.txt",
                "diff.patch",
                "untracked.json",
                "commands.json",
                "checks.json",
                "mechanical-score.json",
                "run-summary.json",
            }
            for directory in (run_dir / "variants").glob("*/*/*"):
                self.assertFalse(required - {path.name for path in directory.iterdir()})
            self.assertEqual(len(comparisons), 4)
            markdown = (run_dir / "report.md").read_text()
            self.assertIn("## Raw run artifacts", markdown)
            self.assertIn("[events.jsonl](", markdown)
            for comparison in report["comparisons"]:
                for paths in comparison["raw_artifact_paths"].values():
                    self.assertEqual(set(paths), required | {"historical-diff.patch"})
                    for relative in paths.values():
                        self.assertTrue((run_dir / relative).is_file())
        finally:
            if run_dir is not None:
                shutil.rmtree(run_dir)

    def test_nonempty_run_directory_is_rejected(self) -> None:
        config = experiment()
        run_id = f"test-reuse-{uuid.uuid4().hex}"
        path = config.root / "runs" / run_id
        path.mkdir()
        (path / "existing").write_text("do not overwrite")
        try:
            with self.assertRaises(FileExistsError):
                execute_pair_experiment(
                    experiment=config,
                    runner=FakeAdapter(),
                    variant_a="champion",
                    variant_b="karpathy-v1",
                    suite="smoke",
                    repeats=1,
                    fake=True,
                    run_id=run_id,
                )
        finally:
            shutil.rmtree(path)

    def test_run_directory_symlink_escape_is_rejected(self) -> None:
        config = experiment()
        run_id = f"test-link-{uuid.uuid4().hex}"
        link = config.root / "runs" / run_id
        with tempfile.TemporaryDirectory() as external:
            link.symlink_to(external, target_is_directory=True)
            try:
                with self.assertRaisesRegex(ValueError, "symlink"):
                    create_run_directory(config.root, run_id)
            finally:
                link.unlink()

    def test_timeout_and_forbidden_change_modes_retain_artifacts(self) -> None:
        from dataclasses import replace

        config = experiment()
        one_case = replace(config, suites={"one": ("ambiguity-must-clarify",)})
        run_id = f"test-timeout-{uuid.uuid4().hex}"
        run_dir = None
        try:
            run_dir, comparisons, _ = execute_pair_experiment(
                experiment=one_case,
                runner=FakeAdapter(
                    {
                        "ambiguity-must-clarify": FakePlan(
                            timed_out=True,
                            changes={"CODER.md": "forbidden\n"},
                        )
                    }
                ),
                variant_a="champion",
                variant_b="karpathy-v1",
                suite="one",
                repeats=1,
                fake=True,
                run_id=run_id,
                run_judge=False,
            )
            for side in ("champion", "candidate"):
                summary = comparisons[0][side]
                self.assertEqual(summary["status"], "TIMEOUT")
                self.assertFalse(
                    summary["mechanical"]["fields"]["forbidden_paths_untouched"]
                )
                self.assertTrue(
                    (
                        run_dir
                        / "variants"
                        / ("champion" if side == "champion" else "karpathy-v1")
                        / "ambiguity-must-clarify"
                        / "1"
                        / "run-summary.json"
                    ).is_file()
                )
        finally:
            if run_dir:
                shutil.rmtree(run_dir)

    def test_capture_failure_is_fail_closed_and_retains_evidence(self) -> None:
        from dataclasses import replace

        config = experiment()
        one_case = replace(config, suites={"one": ("ambiguity-must-clarify",)})
        run_id = f"test-capture-failure-{uuid.uuid4().hex}"
        run_dir = None
        try:
            with mock.patch(
                "mdseval.execution.capture_git",
                side_effect=RuntimeError("capture canary"),
            ):
                run_dir, comparisons, _ = execute_pair_experiment(
                    experiment=one_case,
                    runner=FakeAdapter(),
                    variant_a="champion",
                    variant_b="karpathy-v1",
                    suite="one",
                    repeats=1,
                    fake=True,
                    run_id=run_id,
                    run_judge=False,
                )
            for side in ("champion", "candidate"):
                summary = comparisons[0][side]
                self.assertEqual(summary["status"], "INTERRUPTED")
                self.assertFalse(summary["mechanical"]["hard_pass"])
                for field in (
                    "allowed_paths_only",
                    "forbidden_paths_untouched",
                    "required_unchanged_regions_preserved",
                    "no_unauthorized_commit",
                    "no_unrequested_artifacts",
                ):
                    self.assertFalse(summary["mechanical"]["fields"][field])
                artifact_id = "champion" if side == "champion" else "karpathy-v1"
                artifact = (
                    run_dir
                    / "variants"
                    / artifact_id
                    / "ambiguity-must-clarify"
                    / "1"
                )
                self.assertIn(
                    "git capture: RuntimeError: capture canary",
                    (artifact / "manifest.json").read_text(),
                )
                self.assertTrue((artifact / "run-summary.json").is_file())
        finally:
            if run_dir:
                shutil.rmtree(run_dir)
