from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from mdseval.processutils import ProcessOutcome
from scripts import run_batch as batch
from tooling import compare, taskcheck

REPO = Path(__file__).resolve().parents[1]


class BatchTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        for command in (("init", "-q"), ("config", "user.name", "Test"),
                        ("config", "user.email", "test@example.invalid")):
            subprocess.run(["git", "-C", str(self.root), *command], check=True, capture_output=True)

    def tearDown(self):
        self.temporary.cleanup()

    def task(self, name: str, *, alt_sensitive: bool = False) -> Path:
        task = self.root / "tasks" / name
        for tree_name in ("public", "reference", "blind"):
            tree = task / tree_name
            tree.mkdir(parents=True)
            (tree / ".issue-contract.md").write_text(f"Implement solution.txt for {name}.\n")
        for tree_name in ("reference", "blind"):
            (task / tree_name / "solution.txt").write_text("done\n")
        checker = '''import json,sys
from pathlib import Path
root=Path(sys.argv[1]); ok=(root/"solution.txt").is_file() and (root/"solution.txt").read_text()=="done\\n"; regression=True
print(json.dumps({"requirements":{"R1":ok},"regressions":{"G1":regression},"resolved":ok and regression},sort_keys=True))
'''
        if alt_sensitive:
            checker = checker.replace("regression=True", 'regression=not (root/"ALT.md").exists()')
        (task / "check.py").write_text(checker)
        (task / "requirements.json").write_text(json.dumps({
            "R1": {"target_paths": ["solution.txt"],
                   "omission_probe": {"type": "path_absent", "path": "solution.txt"}}}))
        (task / "blind.provenance.json").write_text(json.dumps({
            "solver_agent": "fake", "timestamp": "2026-08-20T00:00:00+00:00",
            "input_tree_sha256": taskcheck.tree_sha256(task / "public")}))
        taskcheck.admit(task)
        return task

    def arm(self, name: str, data: bytes) -> Path:
        path = self.root / "controls" / f"{name}.md"
        path.parent.mkdir(exist_ok=True)
        path.write_bytes(data)
        return path

    def approve(self, request: Path) -> None:
        (request.parent / "APPROVED.json").write_text(json.dumps({
            "request_sha256": batch.sha256_file(request)}))

    def runner(self, calls: list[tuple[str, bytes]], *, interrupt_first: bool = False):
        def fake(command, *, cwd, **_kwargs):
            md_name = next(item for item in ("ALT.md", "CODER.md") if (cwd / item).is_file())
            arm = (cwd / md_name).read_bytes()
            task_name = (cwd / ".issue-contract.md").read_text().split()[-1].rstrip(".\n")
            calls.append((task_name, arm))
            if arm:
                (cwd / "solution.txt").write_text("done\n")
            Path(command[command.index("--output-last-message") + 1]).write_text("IMPLEMENTED\n")
            interrupted = interrupt_first and len(calls) == 1
            return ProcessOutcome(0, '{"type":"turn.completed"}\n', "", False, interrupted)
        return fake

    def queued(self, task_names: list[str], *, same_arm: bool = False,
               md_filename: str = "ALT.md", seed: int = 7):
        tasks = [self.task(name) for name in task_names]
        arm_a = self.arm("a", b"")
        arm_b = arm_a if same_arm else self.arm("b", b"help\n")
        runs = self.root / "runs"
        with patch.object(batch, "ROOT", self.root.resolve()):
            request = batch.queue_request("fake-batch", tasks, [("a", arm_a), ("b", arm_b)],
                                          runs, md_filename=md_filename, task_order_seed=seed)
        self.approve(request)
        return request, runs

    def test_approval_and_exclusive_create_refusals(self):
        request, runs = self.queued(["task-1"])
        calls = []
        request.parent.joinpath("APPROVED.json").unlink()
        with patch.object(batch, "ROOT", self.root.resolve()), self.assertRaisesRegex(batch.BatchError, "missing"):
            batch.launch("fake-batch", runs, self.runner(calls), require_auth=False)
        request.parent.joinpath("APPROVED.json").write_text(json.dumps({"request_sha256": "bad"}))
        with patch.object(batch, "ROOT", self.root.resolve()), self.assertRaisesRegex(batch.BatchError, "hash mismatch"):
            batch.launch("fake-batch", runs, self.runner(calls), require_auth=False)
        attempt = self.root / "attempt-1"
        attempt.mkdir(); (attempt / "sentinel").write_text("preserved")
        with self.assertRaisesRegex(batch.BatchError, "exclusive-create"):
            batch._reserve(attempt, {"task": "x"})
        self.assertEqual((calls, (attempt / "sentinel").read_text()), ([], "preserved"))

    def test_two_arm_known_b_winner_verifies_and_compares(self):
        names = [f"task-{index}" for index in range(1, 7)]
        request, runs = self.queued(names)
        calls: list[tuple[str, bytes]] = []
        with patch.object(batch, "ROOT", self.root.resolve()):
            batch.launch("fake-batch", runs, self.runner(calls), require_auth=False)
            batch.verify_batch(request.parent)
            batch.launch("fake-batch", runs, self.runner(calls), require_auth=False)
        verdict = compare.compare_batch(request.parent)
        self.assertEqual((len(calls), verdict["verdict"], verdict["n_effective"],
                          verdict["p_value"]["exact"], verdict["effect"]["exact"]),
                         (36, "B_BETTER", 6, "1/32", "1"))
        self.assertTrue(verdict["development_only"])
        self.assertEqual(len(verdict["tasks"]), 6)
        report = (request.parent / "report.md").read_text()
        for field in ("Alpha: 0.05", "Effect threshold: 0.20", "Excluded tasks: none",
                      "Unbalanced tasks: none", "## Runner"):
            self.assertIn(field, report)
        sample = json.loads(next(request.parent.glob("task-*/b/attempt-1/result.json")).read_text())
        self.assertEqual(sample["md_filename"], "ALT.md")
        self.assertIn('project_doc_fallback_filenames=["ALT.md"]',
                      " ".join(json.loads(next(request.parent.glob("task-*/b/attempt-1/launch.json")).read_text())["command"]))
        first_task = json.loads(request.read_text())["tasks"][0]["id"]
        first = [arm for task_name, arm in calls if task_name == first_task]
        self.assertEqual(first, [b"", b"help\n", b"help\n", b"", b"", b"help\n"])

    def test_aa_is_inconclusive_and_orphan_disposition_row_recovers(self):
        request, runs = self.queued(["task-1"], same_arm=True)
        calls: list[tuple[str, bytes]] = []
        with patch.object(batch, "ROOT", self.root.resolve()):
            batch.launch("fake-batch", runs, self.runner(calls), require_auth=False)
        ledger = request.parent / "evidence-ledger.jsonl"
        rows = ledger.read_text().splitlines()
        removed = json.loads(rows[-1])
        ledger.write_text("\n".join(rows[:-1]) + "\n")
        self.assertEqual(removed["type"], "disposition")
        with patch.object(batch, "ROOT", self.root.resolve()):
            batch.launch("fake-batch", runs, self.runner(calls), require_auth=False)
            batch.verify_batch(request.parent)
        verdict = compare.compare_batch(request.parent)
        self.assertEqual((len(calls), verdict["verdict"], verdict["n_effective"]),
                         (6, "INCONCLUSIVE", 0))

    def test_infrastructure_attempt_is_replaced_and_bounded(self):
        request, runs = self.queued(["task-1"])
        calls: list[tuple[str, bytes]] = []
        with patch.object(batch, "ROOT", self.root.resolve()):
            batch.launch("fake-batch", runs, self.runner(calls, interrupt_first=True), require_auth=False)
            batch.verify_batch(request.parent)
        self.assertEqual(len(calls), 7)
        self.assertTrue(any(request.parent.glob("task-1/a/attempt-*/infra-invalid.json")))

    def test_queue_rechecks_request_filename_neutrality(self):
        task = self.task("task-1", alt_sensitive=True)
        arm = self.arm("a", b"")
        with patch.object(batch, "ROOT", self.root.resolve()), self.assertRaisesRegex(
                taskcheck.TaskError, "arm-neutral"):
            batch.queue_request("fake-batch", [task], [("a", arm)], self.root / "runs", md_filename="ALT.md")

    def test_container_schema_is_exact_and_removed_before_runner_config(self):
        task_ids = {"task-1", "task-2"}
        digest = "sha256:" + "a" * 64
        container = {"image_digests": {task: digest for task in task_ids},
                     "spec_sha256": "b" * 64,
                     "interpreter_pins": {task: "3.11.5" for task in task_ids}}
        self.assertIs(batch._container(container, task_ids), container)
        runner = batch.asdict(batch.RUNNER); runner["container"] = container
        self.assertEqual(batch._runner(runner), batch.RUNNER)
        invalid = dict(container); invalid["extra"] = True
        with self.assertRaisesRegex(batch.BatchError, "container schema"):
            batch._container(invalid, task_ids)
        missing = dict(container); missing["image_digests"] = {"task-1": digest}
        with self.assertRaisesRegex(batch.BatchError, "task binding"):
            batch._container(missing, task_ids)
        request = {"runner": {**batch.asdict(batch.RUNNER), "container": container}}
        base = self.root / "runs" / "task-1" / "a"; attempt = base / "attempt-1"; attempt.mkdir(parents=True)
        evidence = {"container": container, "runner": request["runner"]}
        for name in ("intent.json", "launch.json", "result.json"):
            (attempt / name).write_bytes(batch._bytes(evidence))
        self.assertTrue(batch._container_echo(attempt, request))
        (attempt / "launch.json").write_bytes(batch._bytes({**evidence, "container": {}}))
        self.assertFalse(batch._container_echo(attempt, request))
        (attempt / "build-rejected.json").write_text("{}\n")
        with self.assertRaisesRegex(batch.BatchError, "BUILD_REJECTED"):
            batch._state(base)

    def test_checker_ignores_subject_bytecode(self):
        task = self.task("task-1")
        workspace = self.root / "workspace"
        shutil.copytree(task / "reference", workspace)
        cache = workspace / "__pycache__"
        cache.mkdir()
        (cache / "module.cpython-311.pyc").write_bytes(b"bytecode")
        (workspace / "orphan.pyc").write_bytes(b"bytecode")
        result, deterministic, _ = batch._checker(task, workspace)
        self.assertTrue(result["resolved"])
        self.assertTrue(deterministic)

    def test_sealed_disposition_surfaces_per_attempt_metrics(self):
        task = self.task("task-1"); arm_path = self.arm("a", b""); arm = {"name": "a", "path": "controls/a.md", "sha256": batch.sha256_file(arm_path)}
        container = {"image_digests": {task.name: "sha256:" + "a" * 64}, "spec_sha256": "b" * 64, "interpreter_pins": {task.name: "3.11.5"}}
        runner = {**batch.asdict(batch.RUNNER), "container": container}; wrapper = batch.WRAPPER_PATH.read_text().replace("{md_filename}", "CODER.md")
        tokens = {"input_tokens": 1, "cached_input_tokens": 2, "output_tokens": 3, "reasoning_tokens": 4, "total_tokens": 10, "usage_reported": True}
        row = {"runner": runner, "container": container, "arm": "a", "arm_sha256": arm["sha256"], "md_filename": "CODER.md", "wrapper_sha256": taskcheck.sha256_bytes(wrapper.encode()), "requirements": {"R1": True}, "resolved": True, "valid": True, "omission_only": False, "invalid_reason": "", "ordinal": 1, "duration_seconds": 2.5, "token_totals": tokens}
        with patch.object(batch, "ROOT", self.root.resolve()):
            disposition = batch._disposition(task, arm, [row], 0, {"runner": runner, "md_filename": "CODER.md"})
        self.assertEqual(disposition["attempt_metrics"], [{"ordinal": 1, "duration_seconds": 2.5, "token_totals": tokens}])

    def test_sealed_wrapper_records_fail_closed_exceptions(self):
        for mode, function, status, suffix in (("probe", "probe", "BUILD_REJECTED", "jsonl"), ("environment", "environment", "EXCLUDED", "json")):
            with self.subTest(mode=mode):
                output = self.root / f"{mode}.{suffix}"
                argv = ["runtime.py", mode, "task-1", "sha256:" + "a" * 64, "3.11.5", str(self.root), str(output)]
                with patch.object(batch.sealed, function, side_effect=RuntimeError("simulated failure")), patch.object(batch.sealed.sys, "argv", argv):
                    self.assertEqual(batch.sealed.main(), 2)
                self.assertEqual(json.loads(output.read_text())["status"], status)
                self.assertIn("simulated failure", output.with_suffix(output.suffix + ".stderr").read_text())

    def test_unfinished_launched_attempt_consumes_replacement(self):
        request, runs = self.queued(["task-1"]); calls = []
        def crash(*_args, **_kwargs):
            raise RuntimeError("simulated process crash")
        with patch.object(batch, "ROOT", self.root.resolve()):
            with self.assertRaisesRegex(RuntimeError, "simulated"):
                batch.launch("fake-batch", runs, crash, require_auth=False)
            batch.launch("fake-batch", runs, self.runner(calls), require_auth=False)
            batch.verify_batch(request.parent)
        self.assertEqual((len(calls), len(list(request.parent.glob("task-1/a/attempt-*/launch.json")))), (6, 4))

    def test_orphan_attempt_manifest_recovers_ledger_anchor(self):
        request, runs = self.queued(["task-1"]); calls = []; failed = [False]
        original = batch.taskcheck._append_chain
        def flaky(path, row, kind):
            if "attempt" in row and not failed[0]:
                failed[0] = True
                raise RuntimeError("simulated ledger crash")
            return original(path, row, kind)
        with patch.object(batch, "ROOT", self.root.resolve()), patch.object(batch.taskcheck, "_append_chain", flaky):
            with self.assertRaisesRegex(RuntimeError, "ledger crash"):
                batch.launch("fake-batch", runs, self.runner(calls), require_auth=False)
        with patch.object(batch, "ROOT", self.root.resolve()):
            batch.launch("fake-batch", runs, self.runner(calls), require_auth=False); batch.verify_batch(request.parent)
        self.assertEqual(len(calls), 6)

    def test_disposition_tamper_yields_invalid_verdict(self):
        request, runs = self.queued(["task-1"], same_arm=True)
        with patch.object(batch, "ROOT", self.root.resolve()):
            batch.launch("fake-batch", runs, self.runner([]), require_auth=False)
        path = request.parent / "task-1/a/disposition.json"
        value = json.loads(path.read_text()); value["s"] = 2
        path.write_bytes(batch._bytes(value))
        verdict = compare.compare_batch(request.parent)
        self.assertEqual(verdict["verdict"], "INVALID")
        self.assertIn("disposition", verdict["integrity_error"])
        self.assertEqual((verdict["tasks"][0]["task_id"], verdict["evidence_ledger_head"] == "UNVERIFIED"), ("task-1", False))

    def test_frozen_v1_batch_still_verifies_read_only(self):
        frozen = REPO / "runs" / "dev-v2" / "salience-probe-v2"
        before = self.tree_digest(frozen)
        batch.verify_batch(frozen)
        self.assertEqual(self.tree_digest(frozen), before)

    @staticmethod
    def tree_digest(root: Path) -> str:
        digest = hashlib.sha256()
        for path in sorted(item for item in root.rglob("*") if item.is_file()):
            digest.update(path.relative_to(root).as_posix().encode() + b"\0" + path.read_bytes())
        return digest.hexdigest()


if __name__ == "__main__":
    unittest.main()
