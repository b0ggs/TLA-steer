from __future__ import annotations

import io
import json
import tempfile
import unittest
from dataclasses import replace
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from unittest import mock

from mdseval.cli import (
    _bad_control_activation_records,
    _bad_control_winners,
    _command_compare,
    _command_demo,
    _command_validate,
    _evidence_path,
    _load_prior_dev,
    _command_run,
    main,
)
from mdseval.hashing import sha256_file
from mdseval.runner.base import RunResult
from mdseval.runner.codex_cli import DoctorResult

from tests.helpers import ROOT


class CLITests(unittest.TestCase):
    def test_single_variant_holdout_stops_before_live_boundaries(self) -> None:
        from tests.helpers import experiment
        with mock.patch("mdseval.cli._require_live") as live, mock.patch("mdseval.cli.execute_variant_experiment") as execute, self.assertRaisesRegex(ValueError, "sealed comparison"):
            _command_run(experiment(), "champion", "holdout", 1, None)
        live.assert_not_called()
        execute.assert_not_called()

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
        self.assertIn("CANDIDATES:\n- karpathy-v1  candidates/coder/karpathy-v1.md  sha256=", output.getvalue())

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

    def test_doctor_failed_live_smoke_reports_unavailable(self) -> None:
        doctor_result = DoctorResult(
            available=True,
            code="LIVE_RUNNER_AVAILABLE",
            checks={"codex_exists": True},
            command=("codex", "exec"),
        )
        smoke_result = RunResult(
            status="COMPLETED",
            exit_code=17,
            duration_seconds=0.25,
        )
        output = io.StringIO()
        with mock.patch(
            "mdseval.cli.doctor", return_value=doctor_result
        ), mock.patch(
            "mdseval.cli.live_smoke", return_value=smoke_result
        ), redirect_stdout(
            output
        ):
            code = main(
                [
                    "doctor",
                    "--experiment",
                    str(ROOT / "experiments/coder-v1.json"),
                    "--runner",
                    "codex",
                    "--live-smoke",
                ]
            )
        payload = json.loads(output.getvalue())
        self.assertNotEqual(code, 0)
        self.assertEqual(payload["status"], "LIVE_RUNNER_UNAVAILABLE")
        self.assertTrue(payload["model_call_made"])
        self.assertEqual(payload["live_smoke"]["exit_code"], 17)

    def test_candidate_compare_rejects_wrong_order_before_execution(self) -> None:
        from tests.helpers import experiment
        for variant_a, variant_b in (("karpathy-v1", "champion"), ("champion", "unknown-v1")):
            with self.subTest(variant_b=variant_b), mock.patch("mdseval.cli._require_live") as live, self.assertRaisesRegex(ValueError, "validate"):
                _command_compare(experiment(), variant_a, variant_b, "dev", 2, False, None)
            live.assert_not_called()

    def test_demo_selection_and_generic_candidate_control_preflight(self) -> None:
        from tests.helpers import experiment
        base = experiment()
        variants = {**base.variants, "alpha-v2": base.variants["karpathy-v1"], "zeta-v3": base.variants["karpathy-v1"]}
        for ids, expected in ((("alpha-v2", "karpathy-v1", "zeta-v3"), "karpathy-v1"), (("alpha-v2", "zeta-v3"), "alpha-v2")):
            with self.subTest(ids=ids), mock.patch("mdseval.cli.execute_pair_experiment", return_value=(Path("demo"), [], {})) as execute:
                _command_demo(replace(base, variants=variants, candidate_ids=ids), None)
            self.assertEqual(execute.call_args.kwargs["variant_b"], expected)
        config = replace(base, variants=variants, candidate_ids=("alpha-v2", "karpathy-v1", "zeta-v3"))
        listing = io.StringIO()
        with redirect_stdout(listing): _command_validate(config)
        self.assertEqual([line.split()[1] for line in listing.getvalue().splitlines() if line.startswith("- ")], list(config.candidate_ids))
        with mock.patch("mdseval.cli.current_control_context", return_value=({}, "binding")), mock.patch("mdseval.cli._latest_evidence", return_value=None), mock.patch("mdseval.cli._require_live") as live, self.assertRaisesRegex(RuntimeError, "A/A"):
            _command_compare(config, "champion", "alpha-v2", "dev", 2, False, None)
        live.assert_not_called()
        side = {"status": "COMPLETED", "exit_code": 0, "valid_event_stream": True, "mechanical": {"hard_pass": True, "mechanical_score": 100}, "usage": {"total_tokens": 1}, "duration_seconds": 0.1}
        comparison = {"case_id": "scope-ttl-zero", "suite": "dev", "replicate": 1, "valid": True, "qualitative_status": "COMPLETED", "qualitative_winner": "TIE", "judge_output": {"winner": "TIE"}, "champion": side, "candidate": side}
        manifest = {"frozen_inputs_stable": True, "variant_hashes": {"champion": "champion-sha", "alpha-v2": "candidate-sha"}, "control_binding_sha256": "binding", "evaluator_state_sha256": "evaluator"}
        controls = {"passed": True}
        with mock.patch("mdseval.cli.current_control_context", return_value=({}, "binding")), mock.patch("mdseval.cli._latest_evidence", return_value=controls), mock.patch("mdseval.cli._require_live"), mock.patch("mdseval.cli.execute_pair_experiment", return_value=(Path("run"), [comparison], manifest)), mock.patch("mdseval.cli.manifest_matches_authoritative", return_value=True), mock.patch("mdseval.cli._comparison_controls", return_value=(controls, controls)), mock.patch("mdseval.cli.evaluate_promotion", return_value={"verdict": "INCONCLUSIVE"}), mock.patch("mdseval.cli.write_report"), mock.patch("mdseval.cli._report_entry", return_value={}) as entry, mock.patch("mdseval.cli._record_evidence"):
            self.assertEqual(_command_compare(config, "champion", "alpha-v2", "dev", 2, False, None), 0)
        self.assertEqual((entry.call_args.kwargs["candidate_id"], entry.call_args.kwargs["candidate_hash"]), ("alpha-v2", "candidate-sha"))

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

    def test_comparison_rows_become_ordered_activation_records(self) -> None:
        from tests.helpers import experiment

        comparisons = [
            {
                "case_id": "scope-ttl-zero",
                "replicate": 1,
                "candidate": {"diff": "+non_expiring_ttl\n+_expiration_for\n"},
            },
            {
                "case_id": "goal-status-422",
                "replicate": 1,
                "candidate": {"diff": "+non_expiring_ttl\n+_expiration_for\n"},
            },
            {
                "case_id": "feature-json-output",
                "replicate": 1,
                "candidate": {"diff": "+_GreetingRenderer\n"},
            },
        ]
        records = _bad_control_activation_records(comparisons, experiment())
        self.assertEqual(
            [(item["case_id"], item["target"], item["activated"]) for item in records],
            [
                ("scope-ttl-zero", True, True),
                ("goal-status-422", False, False),
                ("feature-json-output", True, False),
            ],
        )
        self.assertTrue(all(item["replicate"] == 1 for item in records))

    def test_evidence_index_symlink_is_rejected(self) -> None:
        from tests.helpers import temporary_evaluator_checkout

        with temporary_evaluator_checkout() as (root, config):
            link = root / "reports/evidence-index.json"
            target = root / "isolated-index.json"
            target.write_text("[]")
            link.symlink_to(target)
            with self.assertRaisesRegex(RuntimeError, "symlink"):
                _evidence_path(config)

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
            candidate_id = "karpathy-v1"
            candidate_hash = sha256_file(config.variants[candidate_id])
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
            for comparison in comparisons: comparison["champion"]["mechanical"] = {"hard_pass": True}; comparison["candidate"]["mechanical"] = {"hard_pass": True}
            report = {
                "candidate_id": candidate_id,
                "aa_calibration": "PASSED",
                "bad_control_validation": "PASSED",
                "variant_hashes": {"candidate": candidate_hash},
                "comparisons": comparisons,
            }
            manifest = {
                "variant_hashes": {candidate_id: candidate_hash},
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
                "candidate_id": candidate_id,
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
            other = {**entry, "candidate_id": "other-v2", "candidate_hash": "other-sha"}
            write_json(root / "reports/evidence-index.json", [entry, other])
            loaded, loaded_entry = _load_prior_dev(
                config, candidate_id, candidate_hash, binding_hash, current_run
            )
            self.assertEqual(loaded_entry, entry)
            self.assertEqual(len(loaded), len(comparisons))
            self.assertTrue(loaded[0]["evidence_path"].startswith("../dev-run/"))

            def persist(rehash: bool = True) -> None:
                write_json(report_path, report); write_json(manifest_path, manifest)
                if rehash: entry["report_sha256"] = sha256_file(report_path); entry["manifest_sha256"] = sha256_file(manifest_path)
                write_json(root / "reports/evidence-index.json", [entry])
            cases = (("report-file-hash", entry, "report_sha256", "other-sha"), ("legacy-index-id", entry, "candidate_id", None), ("index-id", entry, "candidate_id", "other-v2"), ("index-hash", entry, "candidate_hash", "other-sha"), ("binding", entry, "invariant_hash", "other-binding"), ("experiment", entry, "experiment_sha256", "other-experiment"), ("suite", entry, "suite", "holdout"), ("repeats", entry, "repeats", 99), ("case-ids", entry, "case_ids", []), ("escaped-report", entry, "report_path", str(root / "escaped-report.json")), ("escaped-manifest", entry, "manifest_path", str(root / "escaped-manifest.json")), ("report-id", report, "candidate_id", "other-v2"), ("report-hash", report["variant_hashes"], "candidate", "other-sha"), ("manifest-id", manifest, "variant_hashes", {"other-v2": candidate_hash}), ("manifest-hash", manifest, "variant_hashes", {candidate_id: "other-sha"}), ("evaluator", manifest, "evaluator_state_sha256", "other-evaluator"), ("coverage", report, "comparisons", comparisons[:-1]), ("subject", comparisons[0]["champion"], "status", "FAILED"), ("judge", comparisons[0], "judge_output", None))
            for name, target, key, value in cases:
                original = target[key]; target[key] = value; persist(name != "report-file-hash")
                with self.subTest(name=name), mock.patch("mdseval.cli.current_control_context", return_value=({}, binding_hash)), mock.patch("mdseval.cli._latest_evidence", return_value={"passed": True}), mock.patch("mdseval.cli._require_live") as live, self.assertRaises(RuntimeError):
                    _command_compare(config, "champion", candidate_id, "holdout", config.default_repeats, True, None)
                live.assert_not_called(); target[key] = original
            persist()
            holdout = {**comparisons[0], "suite": "holdout"}; run_manifest = {"frozen_inputs_stable": True, "variant_hashes": {"champion": "champion-sha", candidate_id: candidate_hash}, "control_binding_sha256": binding_hash, "evaluator_state_sha256": evaluator_hash}; controls = {"passed": True}
            with mock.patch("mdseval.cli.current_control_context", return_value=({}, binding_hash)), mock.patch("mdseval.cli._latest_evidence", return_value=controls), mock.patch("mdseval.cli._require_live"), mock.patch("mdseval.cli._load_prior_dev", wraps=_load_prior_dev) as lineage, mock.patch("mdseval.cli.execute_pair_experiment", return_value=(current_run, [holdout], run_manifest)) as execute, mock.patch("mdseval.cli.manifest_matches_authoritative", return_value=True), mock.patch("mdseval.cli._comparison_controls", return_value=(controls, controls)), mock.patch("mdseval.cli.evaluate_promotion", return_value={"verdict": "INCONCLUSIVE"}), mock.patch("mdseval.cli.build_report", return_value={}), mock.patch("mdseval.cli.write_report"):
                self.assertEqual(_command_compare(config, "champion", candidate_id, "holdout", config.default_repeats, True, None), 0)
            metadata = execute.call_args.kwargs["manifest_metadata"]; self.assertEqual((lineage.call_count, metadata["candidate_id"], metadata["candidate_sha256"], metadata["source_report_path"], metadata["source_report_sha256"], metadata["source_manifest_path"], metadata["source_manifest_sha256"]), (2, candidate_id, candidate_hash, entry["report_path"], entry["report_sha256"], entry["manifest_path"], entry["manifest_sha256"]))
            with mock.patch("mdseval.cli.current_control_context", return_value=({}, binding_hash)), mock.patch("mdseval.cli._latest_evidence", return_value=controls), mock.patch("mdseval.cli._require_live"), mock.patch("mdseval.cli._load_prior_dev", side_effect=[(comparisons, entry), (comparisons, {**entry, "report_sha256": "changed"})]), mock.patch("mdseval.cli.execute_pair_experiment", return_value=(current_run, [holdout], run_manifest)), mock.patch("mdseval.cli.manifest_matches_authoritative", return_value=True), self.assertRaisesRegex(RuntimeError, "changed during holdout"):
                _command_compare(config, "champion", candidate_id, "holdout", config.default_repeats, True, None)
            with mock.patch("mdseval.cli.current_control_context", return_value=({}, binding_hash)), mock.patch("mdseval.cli._latest_evidence", return_value=controls), mock.patch("mdseval.cli._require_live"), mock.patch("mdseval.cli._load_prior_dev", return_value=(comparisons, entry)), mock.patch("mdseval.cli.execute_pair_experiment", return_value=(current_run, [holdout], run_manifest)) as executed, mock.patch("mdseval.cli.manifest_matches_authoritative", return_value=True), mock.patch("mdseval.cli._comparison_controls", return_value=({**controls, "changed": True}, controls)), mock.patch("mdseval.cli.evaluate_promotion") as promote, self.assertRaisesRegex(RuntimeError, "control evidence changed during candidate comparison"):
                _command_compare(config, "champion", candidate_id, "holdout", config.default_repeats, True, None)
            executed.assert_called_once(); promote.assert_not_called(); variants = {**config.variants, "other-v2": config.variants[candidate_id]}
            cli_cases = ((replace(config, variants=variants, candidate_ids=(candidate_id, "other-v2")), "other-v2"), (replace(config, variants={**config.variants, candidate_id: config.variants["champion"]}), candidate_id))
            for trial, requested in cli_cases:
                with self.subTest(requested=requested), mock.patch("mdseval.cli.current_control_context", return_value=({}, binding_hash)), mock.patch("mdseval.cli._latest_evidence", return_value={"passed": True}), mock.patch("mdseval.cli._require_live") as live, self.assertRaises(RuntimeError):
                    _command_compare(trial, "champion", requested, "holdout", trial.default_repeats, True, None)
                live.assert_not_called()
            manifest["evaluator_state_sha256"] = "tampered"; write_json(manifest_path, manifest)
            with self.assertRaisesRegex(RuntimeError, "hash mismatch"):
                _load_prior_dev(config, candidate_id, candidate_hash, binding_hash, current_run)
