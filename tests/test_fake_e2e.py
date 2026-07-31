from __future__ import annotations

import json
import tempfile
import unittest
import uuid
from pathlib import Path
from unittest import mock

from mdseval.execution import execute_pair_experiment
from mdseval.execution import create_run_directory
from mdseval.runner.fake import FakeAdapter, FakePlan

from tests.helpers import ROOT, git, no_ignore_inventory, temporary_evaluator_checkout


class TemporaryCheckoutTests(unittest.TestCase):
    def test_ignored_secret_cache_and_unknown_local_state_are_not_copied(self) -> None:
        cache_root = ROOT / "src/mdseval/__pycache__"
        cache_root.mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(
            prefix="checkout-secret-", dir=cache_root
        ) as temporary:
            ignored = Path(temporary)
            secret = ignored / "auth.json"
            unknown = ignored / "unknown-local-file"
            secret.write_text("test-only secret sentinel\n", encoding="utf-8")
            unknown.write_text("test-only unknown sentinel\n", encoding="utf-8")
            with temporary_evaluator_checkout() as (checkout, _):
                self.assertFalse((checkout / ignored.relative_to(ROOT)).exists())
                self.assertFalse((checkout / ".mdseval-codex-home").exists())
                self.assertFalse((checkout / "auth.json").exists())
                executable = Path(
                    "evals/holdout/goal-real-entrypoint/fixture/bin/sample-export"
                )
                self.assertEqual(
                    (checkout / executable).stat().st_mode & 0o777,
                    (ROOT / executable).stat().st_mode & 0o777,
                )


class FakeEndToEndTests(unittest.TestCase):
    def setUp(self) -> None:
        self.real_evidence_before = no_ignore_inventory(ROOT, ("runs", "reports"))
        self.checkout_context = temporary_evaluator_checkout()
        self.checkout_root, self.config = self.checkout_context.__enter__()

    def tearDown(self) -> None:
        self.checkout_context.__exit__(None, None, None)
        self.assertEqual(
            no_ignore_inventory(ROOT, ("runs", "reports")),
            self.real_evidence_before,
            "an offline fake test mutated real run/report evidence",
        )

    def test_fake_demo_emits_complete_artifact_contract(self) -> None:
        run_id = f"test-fake-{uuid.uuid4().hex}"
        run_dir, comparisons, _ = execute_pair_experiment(
            experiment=self.config,
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
        run_manifest = json.loads((run_dir / "experiment-manifest.json").read_text())
        self.assertTrue(run_manifest["frozen_inputs_stable"])
        self.assertEqual(
            git(self.checkout_root, "status", "--porcelain", "--untracked-files=all"),
            "",
        )
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

    def test_nonempty_run_directory_is_rejected(self) -> None:
        run_id = f"test-reuse-{uuid.uuid4().hex}"
        path = self.config.root / "runs" / run_id
        path.mkdir()
        (path / "existing").write_text("do not overwrite")
        with self.assertRaises(FileExistsError):
            execute_pair_experiment(
                experiment=self.config,
                runner=FakeAdapter(),
                variant_a="champion",
                variant_b="karpathy-v1",
                suite="smoke",
                repeats=1,
                fake=True,
                run_id=run_id,
            )

    def test_run_directory_symlink_escape_is_rejected(self) -> None:
        run_id = f"test-link-{uuid.uuid4().hex}"
        link = self.config.root / "runs" / run_id
        with tempfile.TemporaryDirectory() as external:
            link.symlink_to(external, target_is_directory=True)
            with self.assertRaisesRegex(ValueError, "symlink"):
                create_run_directory(self.config.root, run_id)

    def test_timeout_and_forbidden_change_modes_retain_artifacts(self) -> None:
        from dataclasses import replace

        one_case = replace(
            self.config, suites={"one": ("ambiguity-must-clarify",)}
        )
        run_id = f"test-timeout-{uuid.uuid4().hex}"
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

    def test_capture_failure_is_fail_closed_and_retains_evidence(self) -> None:
        from dataclasses import replace

        one_case = replace(
            self.config, suites={"one": ("ambiguity-must-clarify",)}
        )
        run_id = f"test-capture-failure-{uuid.uuid4().hex}"
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
