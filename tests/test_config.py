from __future__ import annotations

import json
import shutil
import tempfile
import unittest
from pathlib import Path

from mdseval.config import ConfigError, load_case, load_experiment, safe_relative_path

from tests.helpers import ROOT, experiment


class ConfigTests(unittest.TestCase):
    def test_locked_experiment_loads_all_cases(self) -> None:
        config = experiment()
        self.assertEqual(len(config.cases), 10)
        self.assertEqual(len(config.suites["dev"]), 8)
        self.assertEqual(len(config.suites["holdout"]), 2)

    def test_unknown_experiment_key_is_rejected(self) -> None:
        source = json.loads((ROOT / "experiments/coder-v1.json").read_text())
        source["surprise"] = True
        path = ROOT / "experiments" / ".test-invalid.json"
        try:
            path.write_text(json.dumps(source))
            with self.assertRaisesRegex(ConfigError, "unknown keys"):
                load_experiment(path)
        finally:
            path.unlink(missing_ok=True)

    def test_nonpositive_timeout_is_rejected(self) -> None:
        source = json.loads((ROOT / "experiments/coder-v1.json").read_text())
        source["runner"]["timeout_seconds"] = 0
        path = ROOT / "experiments" / ".test-invalid.json"
        try:
            path.write_text(json.dumps(source))
            with self.assertRaisesRegex(ConfigError, "positive"):
                load_experiment(path)
        finally:
            path.unlink(missing_ok=True)

    def test_duplicate_case_in_suite_is_rejected(self) -> None:
        source = json.loads((ROOT / "experiments/coder-v1.json").read_text())
        source["suites"]["dev"].append(source["suites"]["dev"][0])
        path = ROOT / "experiments" / ".test-invalid.json"
        try:
            path.write_text(json.dumps(source))
            with self.assertRaisesRegex(ConfigError, "duplicates"):
                load_experiment(path)
        finally:
            path.unlink(missing_ok=True)

    def test_absolute_and_parent_paths_are_rejected(self) -> None:
        for value in ("/tmp/x", "../x", "a/../../x"):
            with self.subTest(value=value), self.assertRaises(ConfigError):
                safe_relative_path(value)

    def test_case_unknown_field_and_disposition_are_rejected(self) -> None:
        source_dir = ROOT / "evals/dev/ambiguity-must-clarify"
        with tempfile.TemporaryDirectory() as temporary:
            case_dir = Path(temporary) / "case"
            import shutil

            shutil.copytree(source_dir, case_dir)
            data = json.loads((case_dir / "case.json").read_text())
            data["id"] = "case"
            data["unknown"] = 1
            (case_dir / "case.json").write_text(json.dumps(data))
            with self.assertRaisesRegex(ConfigError, "unknown"):
                load_case(case_dir)
            data.pop("unknown")
            data["expected_disposition"] = "DONE"
            (case_dir / "case.json").write_text(json.dumps(data))
            with self.assertRaisesRegex(ConfigError, "unsupported disposition"):
                load_case(case_dir)

    def test_fixture_symlink_escape_is_rejected(self) -> None:
        source_dir = ROOT / "evals/dev/ambiguity-must-clarify"
        with tempfile.TemporaryDirectory() as temporary:
            case_dir = Path(temporary) / "case"
            import shutil

            shutil.copytree(source_dir, case_dir)
            data = json.loads((case_dir / "case.json").read_text())
            data["id"] = "case"
            (case_dir / "case.json").write_text(json.dumps(data))
            (case_dir / "fixture/escape").symlink_to("/tmp")
            with self.assertRaisesRegex(ConfigError, "symlink"):
                load_case(case_dir)

    def test_missing_and_malformed_schema_documents_are_rejected(self) -> None:
        for schema_name in (
            "case.schema.json",
            "experiment.schema.json",
            "judge-output.schema.json",
        ):
            for mode in ("missing", "malformed"):
                with self.subTest(
                    schema=schema_name, mode=mode
                ), tempfile.TemporaryDirectory() as temporary:
                    copied = Path(temporary) / "repo"
                    shutil.copytree(
                        ROOT,
                        copied,
                        ignore=shutil.ignore_patterns(
                            ".git", "runs", "__pycache__", "*.pyc", "*.pyo"
                        ),
                    )
                    schema = copied / "schemas" / schema_name
                    if mode == "missing":
                        schema.unlink()
                    else:
                        schema.write_text("{malformed")
                    with self.assertRaisesRegex(
                        ConfigError, "schema|valid JSON"
                    ):
                        load_experiment(copied / "experiments/coder-v1.json")

    def test_missing_check_interpreter_is_rejected(self) -> None:
        source_dir = ROOT / "evals/dev/ambiguity-must-clarify"
        with tempfile.TemporaryDirectory() as temporary:
            case_dir = Path(temporary) / "ambiguity-must-clarify"
            shutil.copytree(source_dir, case_dir)
            data = json.loads((case_dir / "case.json").read_text())
            data["required_post_run_checks"][0][0] = (
                "mdseval-definitely-missing-interpreter"
            )
            (case_dir / "case.json").write_text(json.dumps(data))
            with self.assertRaisesRegex(ConfigError, "interpreter is unavailable"):
                load_case(case_dir)
