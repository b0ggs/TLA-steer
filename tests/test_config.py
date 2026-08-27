from __future__ import annotations

import json
import shutil
import tempfile
import unittest
from pathlib import Path

from mdseval.config import ConfigError, load_case, load_experiment, safe_relative_path

from tests.helpers import ROOT, experiment


class ConfigTests(unittest.TestCase):
    def _candidate_file(self, candidate_id: str, content: bytes) -> None:
        path = ROOT / f"candidates/coder/{candidate_id}.md"
        path.write_bytes(content)
        self.addCleanup(path.unlink, missing_ok=True)

    def _candidate_experiment(self, updates=None, remove=()) -> Path:
        source = json.loads((ROOT / "experiments/coder-v1.json").read_text())
        source["variants"].update(updates or {})
        for variant_id in remove: source["variants"].pop(variant_id)
        path = ROOT / "experiments/.test-candidates.json"
        path.write_text(json.dumps(source))
        self.addCleanup(path.unlink, missing_ok=True)
        return path

    def test_candidate_registry_accepts_sorted_versions_and_schema_is_open(self) -> None:
        baseline = load_experiment(ROOT / "experiments/coder-v1.json")
        occupied = set(baseline.candidate_ids) | {
            path.stem for path in (ROOT / "candidates/coder").iterdir()
        }
        probe_ids: list[str] = []
        sequence = 1
        while len(probe_ids) < 2:
            candidate_id = f"registry-probe{sequence}-v1"
            if candidate_id not in occupied:
                probe_ids.append(candidate_id)
                occupied.add(candidate_id)
            sequence += 1
        updates = {}
        for index, candidate_id in enumerate(probe_ids, start=1):
            self._candidate_file(candidate_id, f"probe {index}\n".encode())
            updates[candidate_id] = f"candidates/coder/{candidate_id}.md"
        config = load_experiment(self._candidate_experiment(updates))
        expected_ids = tuple(sorted(set(baseline.candidate_ids) | set(probe_ids)))
        self.assertEqual(config.candidate_ids, expected_ids)
        variants = json.loads((ROOT / "schemas/experiment.schema.json").read_text())["properties"]["variants"]
        self.assertEqual((variants["required"], variants["minProperties"]), (["champion", "deliberately-bad"], 3))
        self.assertIn("^[a-z0-9]+(?:-[a-z0-9]+)*-v[1-9][0-9]*$", variants["patternProperties"])

    def test_reserved_roles_and_at_least_one_candidate_are_required(self) -> None:
        baseline = load_experiment(ROOT / "experiments/coder-v1.json")
        for variant_id in ("champion", "deliberately-bad"):
            with self.subTest(variant_id=variant_id), self.assertRaises(ConfigError):
                load_experiment(self._candidate_experiment(remove=(variant_id,)))
        with self.assertRaises(ConfigError):
            load_experiment(self._candidate_experiment(remove=baseline.candidate_ids))

    def test_candidate_ids_and_lexical_paths_are_exact(self) -> None:
        cases = {"champion": "candidates/coder/champion.md", "deliberately-bad": "candidates/coder/deliberately-bad.md", "Upper-v1": "candidates/coder/Upper-v1.md", "plain": "candidates/coder/plain.md", "zero-v0": "candidates/coder/zero-v0.md", "leading-v01": "candidates/coder/leading-v01.md", "nested-v1": "candidates/coder/nested/nested-v1.md", "outside-v1": "../outside-v1.md", "mismatch-v1": "candidates/coder/other-v1.md", "wrong-role-v1": "candidates/other/wrong-role-v1.md", "not-md-v1": "candidates/coder/not-md-v1.txt", "missing-v1": "candidates/coder/missing-v1.md"}
        for candidate_id, relative in cases.items():
            with self.subTest(candidate_id=candidate_id), self.assertRaises(ConfigError):
                load_experiment(self._candidate_experiment({candidate_id: relative}))

    def test_candidate_symlink_is_rejected_before_resolution(self) -> None:
        path = ROOT / "candidates/coder/symlink-v1.md"
        path.symlink_to(ROOT / "candidates/coder/karpathy-v1.md")
        self.addCleanup(path.unlink, missing_ok=True)
        with self.assertRaisesRegex(ConfigError, "symlink"):
            load_experiment(self._candidate_experiment({"symlink-v1": "candidates/coder/symlink-v1.md"}))

    def test_candidate_content_rejections(self) -> None:
        cases = {"empty-v1": b"", "space-v1": b" \n\t", "binary-v1": b"\xff", "champion-copy-v1": (ROOT / "targets/coder/champion.md").read_bytes(), "control-copy-v1": (ROOT / "controls/coder/deliberately-bad.md").read_bytes()}
        for candidate_id, content in cases.items():
            self._candidate_file(candidate_id, content)
            with self.subTest(candidate_id=candidate_id), self.assertRaises(ConfigError):
                load_experiment(self._candidate_experiment({candidate_id: f"candidates/coder/{candidate_id}.md"}))

    def test_duplicate_candidate_bytes_are_rejected(self) -> None:
        for candidate_id in ("copy-a-v1", "copy-b-v2"): self._candidate_file(candidate_id, b"duplicate\n")
        with self.assertRaisesRegex(ConfigError, "duplicates"):
            load_experiment(self._candidate_experiment({candidate_id: f"candidates/coder/{candidate_id}.md" for candidate_id in ("copy-a-v1", "copy-b-v2")}))

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
                            ".git", "runs", ".mdseval-codex-home",
                            "__pycache__", "*.pyc", "*.pyo"
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
