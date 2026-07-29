from __future__ import annotations

import io
import json
import tempfile
import unittest
from dataclasses import replace
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from unittest import mock

from mdseval.cli import _bad_control_winners, _evidence_path, _load_prior_dev, main
from mdseval.hashing import sha256_file
from mdseval.runner.codex_cli import DoctorResult

from tests.helpers import ROOT


class CLITests(unittest.TestCase):
    def test_validate(self) -> None:
        output = io.StringIO()
        with redirect_stdout(output):
            code = main(
                [
                    "validate",
                    "--experiment",
                    str(ROOT / "experiments/coder-v1.json"),
                ]
            )
        self.assertEqual(code, 0)
        self.assertIn("10 cases", output.getvalue())

    def test_doctor_unavailable_makes_no_live_call(self) -> None:
        result = DoctorResult(
            available=False,
            code="LIVE_RUNNER_UNAVAILABLE",
            checks={"codex_exists": False},
            command=("codex", "exec"),
        )
        output = io.StringIO()
        with mock.patch("mdseval.cli.doctor", return_value=result), mock.patch(
            "mdseval.cli.live_smoke"
        ) as live, redirect_stdout(output):
            code = main(
                [
                    "doctor",
                    "--experiment",
                    str(ROOT / "experiments/coder-v1.json"),
                    "--runner",
                    "codex",
                ]
            )
        self.assertEqual(code, 1)
        live.assert_not_called()
        self.assertIn('"model_call_made": false', output.getvalue())

    def test_candidate_compare_rejects_wrong_order_before_execution(self) -> None:
        error = io.StringIO()
        with mock.patch("mdseval.cli.execute_pair_experiment") as execute, redirect_stderr(
            error
        ):
            code = main(
                [
                    "compare",
                    "--experiment",
                    str(ROOT / "experiments/coder-v1.json"),
                    "--variant-a",
                    "karpathy-v1",
                    "--variant-b",
                    "champion",
                    "--suite",
                    "dev",
                ]
            )
        self.assertEqual(code, 2)
        execute.assert_not_called()

    def test_zero_repeats_is_rejected_not_defaulted(self) -> None:
        error = io.StringIO()
        with redirect_stderr(error):
            code = main(
                [
                    "calibrate",
                    "--experiment",
                    str(ROOT / "experiments/coder-v1.json"),
                    "--repeats",
                    "0",
                ]
            )
        self.assertEqual(code, 2)

    def test_bad_control_winner_is_mapped_at_integration_boundary(self) -> None:
        self.assertEqual(
            _bad_control_winners(
                [
                    {"qualitative_winner": "champion"},
                    {"qualitative_winner": "candidate"},
                    {"qualitative_winner": "TIE"},
                ]
            ),
            ["champion", "deliberately-bad", "TIE"],
        )

    def test_evidence_index_symlink_is_rejected(self) -> None:
        from tests.helpers import experiment

        config = experiment()
        link = config.root / "reports/evidence-index.json"
        self.assertFalse(link.exists())
        with tempfile.TemporaryDirectory() as temporary:
            target = Path(temporary) / "index.json"
            target.write_text("[]")
            link.symlink_to(target)
            try:
                with self.assertRaisesRegex(RuntimeError, "symlink"):
                    _evidence_path(config)
            finally:
                link.unlink()

    def test_sealed_development_lineage_loads_for_holdout_and_rejects_tamper(
        self,
    ) -> None:
        from tests.helpers import experiment, write_json

        base = experiment()
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "reports").mkdir()
            dev_run = root / "runs" / "dev-run"
            current_run = root / "runs" / "holdout-run"
            (dev_run / "comparisons").mkdir(parents=True)
            current_run.mkdir()
            config = replace(base, root=root)
            candidate_hash = "candidate-sha"
            binding_hash = "binding-sha"
            evaluator_hash = "evaluator-sha"
            comparisons = []
            for case_id in config.suites["dev"]:
                for replicate in range(1, config.default_repeats + 1):
                    comparisons.append(
                        {
                            "case_id": case_id,
                            "replicate": replicate,
                            "valid": True,
                            "qualitative_status": "COMPLETED",
                            "judge_output": {"winner": "TIE"},
                            "champion": {
                                "status": "COMPLETED",
                                "exit_code": 0,
                                "valid_event_stream": True,
                            },
                            "candidate": {
                                "status": "COMPLETED",
                                "exit_code": 0,
                                "valid_event_stream": True,
                            },
                            "evidence_path": f"comparisons/{case_id}-{replicate}.json",
                        }
                    )
            report = {
                "aa_calibration": "PASSED",
                "bad_control_validation": "PASSED",
                "variant_hashes": {"candidate": candidate_hash},
                "comparisons": comparisons,
            }
            manifest = {
                "variant_hashes": {"karpathy-v1": candidate_hash},
                "experiment_sha256": "experiment-sha",
                "control_binding_sha256": binding_hash,
                "evaluator_state_sha256": evaluator_hash,
            }
            report_path = dev_run / "report.json"
            manifest_path = dev_run / "experiment-manifest.json"
            write_json(report_path, report)
            write_json(manifest_path, manifest)
            entry = {
                "kind": "candidate_dev",
                "completed": True,
                "candidate_hash": candidate_hash,
                "invariant_hash": binding_hash,
                "evaluator_hash": evaluator_hash,
                "experiment_sha256": "experiment-sha",
                "suite": "dev",
                "repeats": config.default_repeats,
                "case_ids": list(config.suites["dev"]),
                "report_path": str(report_path),
                "report_sha256": sha256_file(report_path),
                "manifest_path": str(manifest_path),
                "manifest_sha256": sha256_file(manifest_path),
            }
            write_json(root / "reports/evidence-index.json", [entry])
            loaded, loaded_entry = _load_prior_dev(
                config, candidate_hash, binding_hash, current_run
            )
            self.assertEqual(loaded_entry, entry)
            self.assertEqual(len(loaded), len(comparisons))
            self.assertTrue(loaded[0]["evidence_path"].startswith("../dev-run/"))

            manifest["evaluator_state_sha256"] = "tampered"
            write_json(manifest_path, manifest)
            with self.assertRaisesRegex(RuntimeError, "hash mismatch"):
                _load_prior_dev(config, candidate_hash, binding_hash, current_run)
