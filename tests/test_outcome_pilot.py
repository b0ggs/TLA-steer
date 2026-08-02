from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from mdseval.hashing import sha256_file, sha256_text, tree_sha256
from mdseval.outcome_pilot import compare_pilot, run_observation


ROOT = Path(__file__).resolve().parents[1]
STOCKROOM = ROOT / "evals/feasibility/coder-outcomes-v2/stockroom"
DELIVERY = ROOT / "evals/feasibility/coder-outcomes-v2/delivery"
TASK_ID = "stockroom-failed-reservation-atomic"
FROZEN_TASKS = ("delivery-dispatch-manifest", "delivery-retire-legacy-quote",
                TASK_ID, "stockroom-low-stock-query")


class OutcomePilotTests(unittest.TestCase):
    def setUp(self) -> None:
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.case = self.root / "case"
        self.case.mkdir()
        shutil.copy2(STOCKROOM / "check.py", self.case / "check.py")
        shutil.copy2(STOCKROOM / "tasks.json", self.case / "tasks.json")
        shutil.copytree(STOCKROOM / "fixture", self.case / "fixture")
        self.instruction = self.root / "CODER.md"
        self.instruction.write_text("Complete the requested coding task.\n", encoding="utf-8")
        self.counter = 0

    def repo(self, name: str, *, correct: bool = False) -> Path:
        repo = self.root / name
        shutil.copytree(STOCKROOM / "fixture", repo)
        if correct:
            path = repo / "stockroom.py"
            source = path.read_text(encoding="utf-8")
            old = """        current = self._stock.get(sku, 0)\n        self._stock[sku] = max(0, current - quantity)\n        return current >= quantity\n"""
            new = """        current = self._stock.get(sku, 0)\n        if current < quantity:\n            return False\n        self._stock[sku] = current - quantity\n        return True\n"""
            self.assertEqual(source.count(old), 1)
            path.write_text(source.replace(old, new), encoding="utf-8")
        return repo

    def observe(self, repo: Path, **overrides: object) -> tuple[dict[str, object], Path]:
        self.counter += 1
        artifacts = self.root / f"artifacts-{self.counter}"
        arguments: dict[str, object] = {
            "task_id": TASK_ID,
            "checker": self.case / "check.py",
            "repo": repo,
            "artifact_dir": artifacts,
            "instruction_path": self.instruction,
            "task_manifest_path": self.case / "tasks.json",
        }
        arguments.update(overrides)
        return run_observation(**arguments), artifacts  # type: ignore[arg-type]

    def test_correct_reference_equivalent_repo_resolves_and_preserves_artifacts(self) -> None:
        repo = self.repo("correct", correct=True)
        expected_tree = tree_sha256(repo)
        result, artifacts = self.observe(repo)
        self.assertIs(result["observation_valid"], True)
        self.assertIs(result["objective_resolved"], True)
        details = result["diagnostics"]
        components = {
            "instruction_sha256": sha256_file(self.instruction),
            "task_manifest_sha256": sha256_file(self.case / "tasks.json"),
            "checker_sha256": sha256_file(self.case / "check.py"),
            "fixture_sha256": tree_sha256(self.case / "fixture"),
        }
        for name, digest in components.items(): self.assertEqual(details[name], digest)
        expected = sha256_text(json.dumps(components, sort_keys=True, separators=(",", ":")))
        self.assertEqual(details["task_sha256"], expected)
        self.assertEqual(len(details["task_sha256"]), 64)
        self.assertEqual(details["repo_tree_sha256"], expected_tree)
        for name in ("command.json", "stdout.txt", "stderr.txt", "observation.json"):
            self.assertTrue((artifacts / name).is_file(), name)
        self.assertEqual(json.loads((artifacts / "observation.json").read_text()), result)
        self.assertEqual(json.loads((artifacts / "command.json").read_text())["argv"][0], sys.executable)
        self.assertIn('"resolved": true', (artifacts / "stdout.txt").read_text())

    def test_pristine_repo_is_valid_subject_failure(self) -> None:
        result, _ = self.observe(self.repo("pristine"))
        self.assertIs(result["observation_valid"], True)
        self.assertIs(result["objective_resolved"], False)
        self.assertEqual(result["diagnostics"]["failure_class"], "SUBJECT_FAILURE")

    def test_diagnostics_and_ceremony_cannot_change_objective_status(self) -> None:
        first, _ = self.observe(
            self.repo("ceremonial", correct=True),
            diagnostics={"ceremony": "reproduced, narrated, and verified", "style": "long"},
        )
        second, _ = self.observe(
            self.repo("terse", correct=True),
            diagnostics={"ceremony": "none", "style": "terse"},
        )
        self.assertEqual(
            (first["observation_valid"], first["objective_resolved"]),
            (second["observation_valid"], second["objective_resolved"]),
        )
        self.assertEqual(first["diagnostics"]["subject_diagnostics"]["style"], "long")
        self.assertEqual(second["diagnostics"]["subject_diagnostics"]["style"], "terse")

    def test_timeout_and_integrity_violation_are_valid_subject_failures(self) -> None:
        timed_out, _ = self.observe(
            self.repo("timeout", correct=True), subject_status="TIMEOUT"
        )
        integrity, _ = self.observe(
            self.repo("integrity", correct=True), subject_integrity=False
        )
        for result in (timed_out, integrity):
            self.assertIs(result["observation_valid"], True)
            self.assertIs(result["objective_resolved"], False)
            self.assertEqual(result["diagnostics"]["failure_class"], "SUBJECT_FAILURE")

    def test_malformed_checker_is_infrastructure_invalid_and_comparison_is_inconclusive(self) -> None:
        bad_case = self.root / "bad-case"
        bad_case.mkdir()
        checker = bad_case / "check.py"
        checker.write_text("print('not-json')\n", encoding="utf-8")
        shutil.copytree(STOCKROOM / "fixture", bad_case / "fixture")
        manifest = bad_case / "tasks.json"
        manifest.write_text(json.dumps({"tasks": [{"id": TASK_ID}]}), encoding="utf-8")
        artifacts = self.root / "bad-artifacts"
        invalid = run_observation(
            task_id=TASK_ID,
            checker=checker,
            repo=self.repo("bad-checker-repo"),
            artifact_dir=artifacts,
            instruction_path=self.instruction,
            task_manifest_path=manifest,
        )
        self.assertIs(invalid["observation_valid"], False)
        self.assertIsNone(invalid["objective_resolved"])
        self.assertEqual(invalid["diagnostics"]["failure_class"], "MALFORMED_CHECKER_EVIDENCE")
        valid, _ = self.observe(self.repo("valid-pristine"))
        comparison = compare_pilot([valid], [invalid])
        self.assertEqual(comparison["status"], "INCONCLUSIVE")
        self.assertIsNone(comparison["resolved_counts"])

    def test_four_matched_pairs_report_descriptive_pilot_counts_only(self) -> None:
        def item(task_id: str, resolved: bool) -> dict[str, object]:
            return {
                "observation_valid": True,
                "objective_resolved": resolved,
                "subject_integrity": True,
                "diagnostics": {"task_id": task_id},
            }

        left = [item(task, resolved) for task, resolved in zip(FROZEN_TASKS, (True, False, True, False))]
        right = [item(task, resolved) for task, resolved in zip(FROZEN_TASKS, (True, True, True, False))]
        result = compare_pilot(left, right)
        self.assertEqual(result["status"], "PILOT")
        self.assertEqual(result["resolved_counts"], {"left": 2, "right": 3})
        rendered = json.dumps(result, sort_keys=True).lower()
        for forbidden in ("winner", "promot", "qualitative"):
            self.assertNotIn(forbidden, rendered)
        subset = compare_pilot(left[:-1], right[:-1])
        self.assertEqual((subset["status"], subset["resolved_counts"]), ("INCONCLUSIVE", None))

    def test_subject_errors_and_tampering_are_valid_unresolved(self) -> None:
        broken = self.repo("broken")
        (broken / "stockroom.py").write_text("def broken(:\n", encoding="utf-8")
        broken_result, _ = self.observe(broken)
        cheat = self.repo("cheat")
        (cheat / "stockroom.py").write_text(
            "import __main__\n__main__.bug_acceptance=lambda module: True\n"
            "__main__.regressions=lambda module: True\nclass Stockroom: pass\n", encoding="utf-8")
        cheat_result, _ = self.observe(cheat)
        mutator = self.repo("mutator", correct=True)
        path = mutator / "stockroom.py"
        path.write_text(path.read_text().replace("from __future__ import annotations\n", f"from __future__ import annotations\nfrom pathlib import Path\nPath({str(self.case / 'tasks.json')!r}).write_text('{{}}')\n", 1), encoding="utf-8")
        mutation_result, _ = self.observe(mutator)
        for result in (broken_result, cheat_result, mutation_result):
            self.assertEqual((result["observation_valid"], result["objective_resolved"]), (True, False))
            self.assertEqual(result["diagnostics"]["failure_class"], "SUBJECT_FAILURE")
        self.assertIs(broken_result["subject_integrity"], True)
        self.assertIs(cheat_result["subject_integrity"], False)
        self.assertIs(mutation_result["subject_integrity"], False)

    def test_canonical_checker_self_tests_cover_all_frozen_tasks(self) -> None:
        summaries: dict[str, object] = {}
        for pack in (STOCKROOM, DELIVERY):
            process = subprocess.run([sys.executable, str(pack / "check.py"), "--self-test"],
                                     text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
            summary = json.loads(process.stdout)
            summaries.update(summary)
            for evidence in summary.values():
                self.assertEqual((evidence["pristine"]["acceptance"], evidence["pristine"]["regressions"]), (False, True))
                self.assertIs(evidence["reference"]["resolved"], True)
                self.assertIs(evidence["wrong"]["resolved"], False)
        self.assertEqual(set(summaries), set(FROZEN_TASKS))

    def test_artifact_reuse_and_artifacts_inside_subject_are_refused(self) -> None:
        repo = self.repo("boundary")
        used = self.root / "used"
        used.mkdir()
        with self.assertRaises(FileExistsError):
            run_observation(
                task_id=TASK_ID,
                checker=self.case / "check.py",
                repo=repo,
                artifact_dir=used,
                instruction_path=self.instruction,
                task_manifest_path=self.case / "tasks.json",
            )
        inside = repo / "artifacts"
        with self.assertRaises(ValueError):
            run_observation(
                task_id=TASK_ID,
                checker=self.case / "check.py",
                repo=repo,
                artifact_dir=inside,
                instruction_path=self.instruction,
                task_manifest_path=self.case / "tasks.json",
            )
        self.assertFalse(inside.exists())


if __name__ == "__main__":
    unittest.main()
