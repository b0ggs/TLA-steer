import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import blindsolve
import taskcheck
import taskgen


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

    def test_explicit_v2_metadata_is_copied(self):
        task = self.make_task()
        (task / "task-meta.json").write_text(json.dumps({"layout_version": 2, "salience": "pointer", "parent_task_id": None}))
        manifest = taskcheck.admit(task)
        self.assertEqual(manifest["layout_version"], 2)
        self.assertTrue(taskcheck.verify(task)["verified"])

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
        with self.assertRaisesRegex(taskcheck.TaskError, "invalid|not anchored"):
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

    def test_v3_factory_blindsolve_admit_and_master_list_rejection(self):
        author = self.root / "author.py"
        author.write_text('''import json, pathlib, shutil, sys
root = pathlib.Path.cwd(); prompt = sys.argv[1]
assert "ALT.md" not in prompt
recipe = json.loads(prompt.split("recipe:", 1)[1].lstrip().splitlines()[0])
public = root / "public"; reference = root / "reference"
for base in (public, reference):
    base.mkdir(); (base / ".issue-contract.md").write_text("Implement the documented outputs.\\n")
requirements = {}
for index in range(8):
    name = f"doc-{index // 2}.md"; quote = f"Requirement {index + 1} must create output-{index + 1}.txt."
    for base in (public, reference):
        with (base / name).open("a") as stream: stream.write(quote + "\\n")
    (reference / f"output-{index + 1}.txt").write_text("done\\n")
    requirements[f"R{index + 1}"] = {"target_paths":[f"output-{index + 1}.txt"], "omission_probe":{"type":"path_absent","path":f"output-{index + 1}.txt"}, "stated_in":{"path":name,"quote":quote}}
(root / "requirements.json").write_text(json.dumps(requirements))
(root / "task-meta.json").write_text(json.dumps({"layout_version":3,"salience":recipe["salience"],"parent_task_id":None}))
(root / "check.py").write_text("import json,sys\\nfrom pathlib import Path\\nr=Path(sys.argv[1]); q={f'R{i}':(r/f'output-{i}.txt').read_text()=='done\\\\n' if (r/f'output-{i}.txt').is_file() else False for i in range(1,9)}; print(json.dumps({'requirements':q,'regressions':{'G1':True},'resolved':all(q.values())},sort_keys=True))\\n")
if len(sys.argv) > 2: (root / "blind").mkdir()
''')
        solver = self.root / "solver.py"
        solver.write_text('''from pathlib import Path
for index in range(1, 9): Path(f"output-{index}.txt").write_text("done\\n")
''')
        recipe = self.root / "recipe.json"
        value = {"task_id": "factory-task", "family": "feature", "theme": "outputs",
                 "requirement_count": 8, "salience": "pointer", "md_filename": "ALT.md"}
        recipe.write_text(json.dumps(value))
        task = taskgen.generate(recipe, self.root / "tasks", [sys.executable, str(author), "{prompt}"])
        blindsolve.solve(task, [sys.executable, str(solver), "{prompt}"], "fake-solver",
                         ["no-network", "workspace-only"])
        manifest = taskcheck.admit(task, md_filename="ALT.md")
        self.assertEqual((manifest["layout_version"], manifest["salience"]), (3, "pointer"))
        provenance_path = task / "blind.provenance.json"
        provenance = json.loads(provenance_path.read_text())
        provenance["sandbox_flags"] = []
        provenance_path.write_text(taskcheck.canonical(provenance) + "\n")
        with self.assertRaisesRegex(taskcheck.TaskError, "nonempty strings"):
            taskcheck.admit(task, md_filename="ALT.md")
        provenance["sandbox_flags"] = ["no-network", "workspace-only"]
        provenance_path.write_text(taskcheck.canonical(provenance) + "\n")
        quotes = [row["stated_in"]["quote"] for row in manifest["requirements"].values()]
        (task / "public" / "extra.md").write_text("\n".join(quotes[:4]) + "\n")
        with self.assertRaisesRegex(taskcheck.TaskError, "quote cap"):
            taskcheck.admit(task, md_filename="ALT.md")
        (task / "public" / "extra.md").unlink()
        requirements = json.loads((task / "requirements.json").read_text())
        shared = "Shared contract sentence."
        requirements["R1"]["stated_in"]["quote"] = quotes[0] + " " + shared
        requirements["R2"]["stated_in"]["quote"] = shared + " " + quotes[1]
        (task / "requirements.json").write_text(json.dumps(requirements))
        (task / "public" / "doc-0.md").write_text(f"{quotes[0]} {shared} {quotes[1]}\n")
        with self.assertRaisesRegex(taskcheck.TaskError, "non-overlapping"):
            taskcheck.admit(task, md_filename="ALT.md")
        value["task_id"] = "forbidden-task"; recipe.write_text(json.dumps(value))
        with self.assertRaisesRegex(taskgen.TaskgenError, "forbidden output"):
            taskgen.generate(recipe, self.root / "tasks",
                             [sys.executable, str(author), "{prompt}", "forbidden"])
        self.assertFalse((self.root / "tasks" / "forbidden-task").exists())

    def test_taskgen_rejects_nonstring_recipe_fields_cleanly(self):
        recipe = self.root / "recipe.json"
        base = {"task_id": "bad-recipe", "family": "feature", "theme": "theme", "requirement_count": 8, "salience": "pointer", "md_filename": "CODER.md"}
        for key in ("task_id", "family", "salience", "md_filename"):
            value = dict(base); value[key] = []
            recipe.write_text(json.dumps(value))
            with self.subTest(key=key), self.assertRaisesRegex(taskgen.TaskgenError, "values"):
                taskgen.generate(recipe, self.root / "tasks", ["unused", "{prompt}"])


if __name__ == "__main__":
    unittest.main()
