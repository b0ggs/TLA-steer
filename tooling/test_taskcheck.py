import json
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

import taskcheck


CHECKER = '''import json, sys
from pathlib import Path
root = Path(sys.argv[1])
passed = (root / "solution.txt").is_file() and (root / "solution.txt").read_text() == "done\\n"
regression = {regression}
requirements = {{"R1": {requirement}}}
regressions = {{"G1": {regression_value}}}
print("checker detail")
print(json.dumps({{"requirements": requirements, "regressions": regressions,
                  "resolved": passed and regression}}, sort_keys=True))
'''


class TaskcheckTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.git("init", "-q")
        self.git("config", "user.name", "Taskcheck Test")
        self.git("config", "user.email", "taskcheck@example.invalid")

    def tearDown(self):
        self.temporary.cleanup()

    def git(self, *args):
        return subprocess.run(
            ["git", "-C", str(self.root), *args], check=True,
            capture_output=True, text=True,
        )

    def make_task(self, name="sample-task", *, legacy=False, arm_sensitive=False):
        task = self.root / "tasks" / name
        public = task / "public"
        reference = task / "reference"
        blind = task / "blind"
        for directory in (public, reference, blind):
            directory.mkdir(parents=True)
            (directory / ".issue-contract.md").write_text("Create solution.txt.\n")
        for directory in (reference, blind):
            (directory / "solution.txt").write_text("done\n")
        requirement = '{"passed": passed, "detail": "legacy"}' if legacy else "passed"
        regression_value = '{"passed": regression}' if legacy else "regression"
        regression = 'not (root / "CODER.md").exists()' if arm_sensitive else "True"
        (task / "check.py").write_text(CHECKER.format(
            requirement=requirement, regression=regression,
            regression_value=regression_value,
        ))
        requirements = {
            "R1": {
                "target_paths": ["solution.txt"],
                "omission_probe": {"type": "path_absent", "path": "solution.txt"},
            }
        }
        (task / "requirements.json").write_text(json.dumps(requirements))
        provenance = {
            "solver_agent": "synthetic-test",
            "timestamp": "2026-08-20T00:00:00+00:00",
            "input_tree_sha256": taskcheck.tree_sha256(public),
        }
        (task / "blind.provenance.json").write_text(json.dumps(provenance))
        return task

    def exposure(self, task):
        path = task.parent / "exposures.jsonl"
        row = {
            "task_id": task.name, "event": "exposed", "batch_id": "batch",
            "reason": None, "prev_sha256": "GENESIS",
        }
        path.write_text(taskcheck.canonical(row) + "\n")

    def test_admit_and_verify_normalize_legacy_results(self):
        task = self.make_task(legacy=True)
        manifest = taskcheck.admit(task)
        result = taskcheck.verify(task)
        self.assertEqual(manifest["task_id"], "sample-task")
        self.assertTrue(result["verified"])
        self.assertEqual(self.git("log", "-1", "--format=%s").stdout.strip(), "admit: sample-task")

    def test_admit_refuses_exposed_task(self):
        task = self.make_task()
        self.exposure(task)
        with self.assertRaisesRegex(taskcheck.TaskError, "frozen"):
            taskcheck.admit(task)

    def test_admit_rejects_malformed_exposure_schema(self):
        task = self.make_task()
        self.exposure(task)
        path = task.parent / "exposures.jsonl"
        row = json.loads(path.read_text()); row["extra"] = True
        path.write_text(taskcheck.canonical(row) + "\n")
        with self.assertRaisesRegex(taskcheck.TaskError, "exposures ledger schema"):
            taskcheck.admit(task)

    def test_admit_rejects_arm_sensitive_checker(self):
        task = self.make_task(arm_sensitive=True)
        with self.assertRaisesRegex(taskcheck.TaskError, "arm-neutral"):
            taskcheck.admit(task)

    def test_admit_rejects_probe_that_does_not_fire(self):
        task = self.make_task()
        requirements = json.loads((task / "requirements.json").read_text())
        requirements["R1"]["omission_probe"] = {
            "type": "text_absent", "path": ".issue-contract.md", "text": "Create",
        }
        (task / "requirements.json").write_text(json.dumps(requirements))
        with self.assertRaisesRegex(taskcheck.TaskError, "does not fire"):
            taskcheck.admit(task)

    def test_verify_detects_mutated_manifest(self):
        task = self.make_task()
        taskcheck.admit(task)
        manifest = json.loads((task / "manifest.json").read_text())
        manifest["salience"] = "pointer"
        (task / "manifest.json").write_text(taskcheck.canonical(manifest) + "\n")
        with self.assertRaisesRegex(taskcheck.TaskError, "not anchored"):
            taskcheck.verify(task)

    def test_verify_detects_broken_chain(self):
        task = self.make_task()
        taskcheck.admit(task)
        ledger = task.parent / "ledger.jsonl"
        row = json.loads(ledger.read_text())
        row["prev_sha256"] = "broken"
        ledger.write_text(taskcheck.canonical(row) + "\n")
        with self.assertRaisesRegex(taskcheck.TaskError, "broken task ledger chain"):
            taskcheck.verify(task)

    def test_verify_detects_deleted_ledger_task(self):
        first = self.make_task("first-task")
        second = self.make_task("second-task")
        taskcheck.admit(first)
        taskcheck.admit(second)
        shutil.rmtree(second)
        with self.assertRaisesRegex(taskcheck.TaskError, "missing from disk"):
            taskcheck.verify(first)

    def test_batch_discovers_any_child_with_checker(self):
        task = self.make_task("fac-07")
        rows = taskcheck.batch("admit", task.parent)
        self.assertEqual([row["task_id"] for row in rows], ["fac-07"])


if __name__ == "__main__":
    unittest.main()
