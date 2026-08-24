from __future__ import annotations

import importlib.util
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "phase3_real_issue", REPO / "scripts" / "import" / "phase3_real_issue.py")
assert SPEC and SPEC.loader
preflight = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(preflight)


class Section14PreflightTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        subprocess.run(["git", "-C", str(self.root), "init", "-q"], check=True)

    def tearDown(self):
        self.temporary.cleanup()

    def task(self, name: str = "full-fixture") -> Path:
        task = self.root / "tasks" / name
        for tree_name in ("public", "reference", "blind"):
            tree = task / tree_name
            (tree / "tests").mkdir(parents=True)
            (tree / ".issue-contract.md").write_text("The fix must preserve the full repository.\n")
            (tree / "LICENSE").write_text("MIT fixture\n")
            (tree / "pyproject.toml").write_text("[build-system]\nrequires=[]\n")
            (tree / "requirements-test.txt").write_text("pytest==8.4.2\n")
            (tree / "native.c").write_text("int answer(void) { return 42; }\n")
            (tree / "conftest.py").write_text("import pytest\n")
            (tree / "tests" / "test_network.py").write_text("import socket\n")
            (tree / "tests" / "test_changed.py").write_text("OLD = True\n")
            (tree / ".gitignore").write_text(".venv/\n")
            (tree / ".gitattributes").write_text("*.txt text\n")
        private = task / "private" / "tests"
        private.mkdir(parents=True)
        (private / "test_changed.py").write_text("NEW_REGRESSION = True\n")
        checker = "TemporaryDirectory copytree copy2 PYTHONDONTWRITEBYTECODE"
        (task / "check.py").write_text(f"# {checker}\n")
        (task / "task-meta.json").write_text(json.dumps(
            {"layout_version": 3, "parent_task_id": None, "salience": "enumerated"}))
        (task / "requirements.json").write_text(json.dumps({"R1": {}}))
        (task / "blind-calibration.json").write_text(json.dumps(
            {"seal_status": "UNSEALED", "use": "calibration-only"}))
        source = {
            "source_url": "https://example.invalid/repo", "issue_url": "https://example.invalid/issue/1",
            "base_sha": "a" * 40, "fix_sha": "b" * 40,
            "solution_patch_sha256": "c" * 64, "fix_test_patch_sha256": "d" * 64,
            "checker_command": "python3 check.py WORKSPACE", "spdx_id": "MIT",
            "license_paths": [{"path": "public/LICENSE", "sha256": preflight.sha256(task / "public" / "LICENSE")}],
            "removed_instruction_paths": [], "extraction_note": "complete upstream checkout",
            "issue_closed_at": "2026-03-02T12:48:18Z",
        }
        (task / "failure-source.json").write_text(json.dumps(source))
        return task

    def test_full_scale_mode_allows_real_repository_inputs_and_changed_test_overlay(self):
        task = self.task()
        result = preflight.preflight(task, finalize=True, section14=True)
        self.assertTrue(result["full_scale"])
        self.assertTrue(result["section14_mode"])
        self.assertTrue(result["source"]["extraction_note"].startswith(preflight.FULL_SCALE_NOTE))
        self.assertEqual(preflight.preflight(
            task, finalize=False, section14=True)["preflight"], "pass")

    def test_schema_switch_is_exact_and_requires_iso_close_date(self):
        task = self.task()
        source_path = task / "failure-source.json"
        source = json.loads(source_path.read_text())
        source["issue_closed_at"] = "2026-02-30"
        source_path.write_text(json.dumps(source))
        with self.assertRaisesRegex(preflight.PreflightError, "ISO-8601"):
            preflight.validate_source(task, finalize=True, section14=True)
        source.pop("issue_closed_at"); source["extraction_note"] = preflight.PREFLIGHT_NOTE
        source_path.write_text(json.dumps(source))
        self.assertEqual(set(preflight.validate_source(task, finalize=False)), preflight.SOURCE_KEYS)
        source["unexpected"] = True; source_path.write_text(json.dumps(source))
        with self.assertRaisesRegex(preflight.PreflightError, "keys differ"):
            preflight.validate_source(task, finalize=False)

    def test_full_scale_keeps_hygiene_and_gitignore_protections(self):
        mutations = {
            "instruction": lambda task: (task / "public" / "AGENTS.md").write_text("leak\n"),
            "cache": lambda task: (task / "public" / "__pycache__").mkdir(),
            "submodule": lambda task: (task / "public" / ".gitmodules").write_text("[submodule]\n"),
            "lfs": lambda task: (task / "public" / "asset.bin").write_text(
                "version https://git-lfs.github.com/spec/v1\n"),
            "private leak": lambda task: shutil.copy2(
                task / "private" / "tests" / "test_changed.py",
                task / "public" / "tests" / "test_changed.py"),
            "symlink": lambda task: (task / "public" / "linked.py").symlink_to("native.c"),
        }
        for index, (label, mutate) in enumerate(mutations.items()):
            with self.subTest(label=label):
                task = self.task(f"full-bad-{index}"); mutate(task)
                with self.assertRaises(preflight.PreflightError):
                    preflight.preflight(task, finalize=True, section14=True)
        task = self.task("full-hidden")
        for tree in ("public", "reference", "blind"):
            (task / tree / ".gitignore").write_text("hidden.py\n")
        (task / "public" / "hidden.py").write_text("included bytes\n")
        with self.assertRaisesRegex(preflight.PreflightError, "would omit task bytes"):
            preflight.preflight(task, finalize=True, section14=True)

    def test_explicit_mode_cannot_fall_back_when_close_date_is_absent(self):
        task = self.task()
        source_path = task / "failure-source.json"
        source = json.loads(source_path.read_text())
        source.pop("issue_closed_at")
        source["extraction_note"] = preflight.PREFLIGHT_NOTE
        source_path.write_text(json.dumps(source))
        before = source_path.read_bytes()
        with self.assertRaisesRegex(preflight.PreflightError, "issue_closed_at"):
            preflight.validate_source(task, finalize=True, section14=True)
        self.assertEqual(source_path.read_bytes(), before)
        self.assertEqual(set(preflight.validate_source(
            task, finalize=False)), preflight.SOURCE_KEYS)
        source["issue_closed_at"] = "2026-03-02T12:48:18Z"
        source["unexpected"] = True
        source["extraction_note"] = preflight.FULL_SCALE_NOTE
        source_path.write_text(json.dumps(source))
        with self.assertRaisesRegex(preflight.PreflightError, "unexpected"):
            preflight.validate_source(task, finalize=False, section14=True)

    def test_explicit_mode_requires_exact_blind_calibration(self):
        task = self.task()
        (task / "blind-calibration.json").write_text(json.dumps(
            {"seal_status": "SEALED", "use": "evidence"}))
        with self.assertRaisesRegex(preflight.PreflightError, "blind-calibration"):
            preflight.preflight(task, finalize=True, section14=True)

    def test_cli_section14_mode_is_recorded_and_scan_fails_closed(self):
        task = self.task()
        script = REPO / "scripts" / "import" / "phase3_real_issue.py"
        command = [sys.executable, str(script), "preflight", str(task),
                   "--section14", "--finalize"]
        completed = subprocess.run(command, capture_output=True, text=True, check=False)
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertTrue(json.loads(completed.stdout)["section14_mode"])
        scanned = subprocess.run(
            [sys.executable, str(script), "scan", str(task), "--section14"],
            capture_output=True, text=True, check=False)
        self.assertEqual(scanned.returncode, 0, scanned.stderr)
        self.assertTrue(json.loads(scanned.stdout)["section14_mode"])
        source_path = task / "failure-source.json"
        source = json.loads(source_path.read_text()); source.pop("issue_closed_at")
        source["extraction_note"] = preflight.PREFLIGHT_NOTE
        source_path.write_text(json.dumps(source))
        scanned = subprocess.run(
            [sys.executable, str(script), "scan", str(task), "--section14"],
            capture_output=True, text=True, check=False)
        self.assertEqual(scanned.returncode, 1)
        self.assertIn("issue_closed_at", scanned.stderr)


if __name__ == "__main__":
    unittest.main()
