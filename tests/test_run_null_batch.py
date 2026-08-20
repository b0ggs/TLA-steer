import json
import tempfile
import unittest
from dataclasses import asdict
from pathlib import Path
from unittest.mock import patch

from mdseval.processutils import ProcessOutcome
from scripts import run_null_batch as batch
from tooling import taskcheck


class NullBatchTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)

    def tearDown(self):
        self.temporary.cleanup()

    def fake_runner(self, calls):
        def run(command, **kwargs):
            calls.append((command, kwargs))
            return ProcessOutcome(0, "", "", False, False)
        return run

    def request(self):
        target = self.root / "batch" / "REQUEST.json"
        target.parent.mkdir()
        value = {
            "batch_id": "batch", "tasks": [],
            "arm": {"name": "null", "path": "controls/coder/null-m2.md", "sha256": "0" * 64},
            "call_count": 0, "contingent_replacement_call_cap": 0,
            "runner": asdict(batch.RUNNER),
        }
        target.write_bytes(batch._bytes(value))
        return target

    def admitted_task(self):
        task = self.root / "tasks" / "fake-task"
        for name in ("public", "reference", "blind"):
            tree = task / name
            tree.mkdir(parents=True)
            (tree / ".issue-contract.md").write_text("Create solution.txt containing done.\n")
        for name in ("reference", "blind"):
            (task / name / "solution.txt").write_text("done\n")
        checker = '''import json, sys
from pathlib import Path
root = Path(sys.argv[1]); passed = (root / "solution.txt").is_file() and (root / "solution.txt").read_text() == "done\\n"
print(json.dumps({"requirements":{"R1":passed},"regressions":{"G1":True},"resolved":passed}, sort_keys=True))
'''
        (task / "check.py").write_text(checker)
        requirements = {"R1": {"target_paths": ["solution.txt"],
                                "omission_probe": {"type": "path_absent", "path": "solution.txt"}}}
        (task / "requirements.json").write_text(json.dumps(requirements))
        provenance = {"solver_agent": "fake", "timestamp": "2026-08-20T00:00:00+00:00",
                      "input_tree_sha256": taskcheck.tree_sha256(task / "public")}
        (task / "blind.provenance.json").write_text(json.dumps(provenance))
        for command in (("init", "-q"), ("config", "user.name", "Test"),
                        ("config", "user.email", "test@example.invalid")):
            __import__("subprocess").run(["git", "-C", str(self.root), *command], check=True,
                                         capture_output=True)
        taskcheck.admit(task)
        return task

    def test_missing_and_hash_mismatched_approval_refuse_fake_runner(self):
        calls = []
        request = self.request()
        with self.assertRaisesRegex(batch.BatchError, "missing or unsafe"):
            batch.launch("batch", self.root, self.fake_runner(calls), require_auth=False)
        (request.parent / "APPROVED.json").write_text(json.dumps({"request_sha256": "bad"}))
        with self.assertRaisesRegex(batch.BatchError, "hash mismatch"):
            batch.launch("batch", self.root, self.fake_runner(calls), require_auth=False)
        self.assertEqual(calls, [])
        self.assertFalse(any(request.parent.glob("attempt-*")))

    def test_attempt_directory_is_exclusive_create(self):
        attempt = self.root / "attempt-1"
        attempt.mkdir()
        sentinel = attempt / "sentinel"
        sentinel.write_text("preserved")
        with self.assertRaisesRegex(batch.BatchError, "exclusive-create collision"):
            batch._reserve(attempt, {"task": "t", "arm": "null", "ordinal": 1})
        self.assertEqual(sentinel.read_text(), "preserved")
        self.assertEqual(list(attempt.iterdir()), [sentinel])

    def test_retired_exposure_refuses_launch(self):
        task = self.root / "tasks" / "fac-07"
        task.mkdir(parents=True)
        exposure = {
            "task_id": "fac-07", "event": "retired", "batch_id": "old",
            "reason": "defect", "prev_sha256": "GENESIS",
        }
        (task.parent / "exposures.jsonl").write_text(taskcheck.canonical(exposure) + "\n")
        with self.assertRaisesRegex(batch.BatchError, "retired task"):
            batch._expose(task, "new")

    def test_evidence_ledger_rejects_extra_keys_and_duplicate_attempts(self):
        ledger = self.root / "evidence-ledger.jsonl"
        bad = {"attempt": "fake/null/attempt-1", "manifest_sha256": "0" * 64,
               "prev_sha256": "GENESIS", "extra": True}
        ledger.write_text(taskcheck.canonical(bad) + "\n")
        with self.assertRaisesRegex(batch.BatchError, "schema"):
            batch._ledger(self.root, required=True)
        ledger.unlink()
        row = {key: bad[key] for key in ("attempt", "manifest_sha256")}
        taskcheck._append_chain(ledger, row, "evidence ledger")
        taskcheck._append_chain(ledger, row, "evidence ledger")
        with self.assertRaisesRegex(batch.BatchError, "schema"):
            batch._ledger(self.root, required=True)

    def test_orphan_finalized_attempt_refuses_resume(self):
        base = self.root / "batch/fake/null"
        attempt = base / "attempt-1"
        attempt.mkdir(parents=True)
        (attempt / "attempt-manifest.json").write_bytes(batch._bytes({"files": {}, "created": 1}))
        with self.assertRaisesRegex(batch.BatchError, "unanchored"):
            batch._state(base)

    def test_omission_and_incorrect_failure_classify_differently(self):
        probe = {"type": "path_absent", "path": "deliverable.txt"}
        omission = taskcheck._probe_fires(self.root, probe, "R1")
        base = {"requirements": {"R1": False}, "regressions": {"G1": True},
                "resolved": False, "valid": True, "invalid_reason": ""}
        omitted = [{**base, "omission_only": omission} for _ in range(3)]
        self.assertEqual(batch.classify(omitted, 1)["label"], "floor")
        (self.root / "deliverable.txt").write_text("wrong")
        incorrect = taskcheck._probe_fires(self.root, probe, "R1")
        wrong = [{**base, "omission_only": incorrect} for _ in range(3)]
        self.assertEqual(batch.classify(wrong, 1)["label"], "wrong-failure-mode")

    def test_approved_fake_runner_finalizes_verifies_and_resumes(self):
        task = self.admitted_task()
        arm = self.root / "controls" / "null.md"
        arm.parent.mkdir(); arm.write_bytes(b"")
        runs = self.root / "runs"
        calls = []
        def fake(command, *, cwd, **kwargs):
            calls.append(command)
            (cwd / "solution.txt").write_text("done\n")
            Path(command[command.index("--output-last-message") + 1]).write_text("IMPLEMENTED\n")
            return ProcessOutcome(0, '{"type":"turn.completed"}\n', "", False, False)
        with patch.object(batch, "ROOT", self.root.resolve()):
            request = batch.queue_request("fake-batch", [task], "null", arm, runs)
            approval = {"request_sha256": batch.sha256_file(request)}
            (request.parent / "APPROVED.json").write_text(json.dumps(approval))
            batch.launch("fake-batch", runs, fake, require_auth=False)
            batch.verify_batch(request.parent)
            batch.launch("fake-batch", runs, fake, require_auth=False)
        disposition = json.loads((runs / "fake-batch/fake-task/null/disposition.json").read_text())
        self.assertEqual((len(calls), disposition["label"], disposition["s"]), (3, "ceiling", 3))

    def test_interrupted_attempt_is_replaced_not_finalized(self):
        task = self.admitted_task()
        arm = self.root / "controls/null.md"; arm.parent.mkdir(); arm.write_bytes(b"")
        runs = self.root / "runs"; calls = []
        def fake(command, *, cwd, **kwargs):
            calls.append(command); (cwd / "solution.txt").write_text("done\n")
            Path(command[command.index("--output-last-message") + 1]).write_text("IMPLEMENTED\n")
            return ProcessOutcome(0, '{"type":"turn.completed"}\n', "", False, len(calls) == 1)
        with patch.object(batch, "ROOT", self.root.resolve()):
            request = batch.queue_request("fake-batch", [task], "null", arm, runs)
            (request.parent / "APPROVED.json").write_text(json.dumps({"request_sha256": batch.sha256_file(request)}))
            batch.launch("fake-batch", runs, fake, require_auth=False)
        base = runs / "fake-batch/fake-task/null"
        self.assertEqual(len(calls), 4)
        self.assertTrue((base / "attempt-1/infra-invalid.json").is_file())
        self.assertFalse((base / "attempt-1/attempt-manifest.json").exists())

    def test_subject_contract_edit_marks_attempts_invalid(self):
        task = self.admitted_task()
        arm = self.root / "controls/null.md"; arm.parent.mkdir(); arm.write_bytes(b"")
        runs = self.root / "runs"
        def fake(command, *, cwd, **kwargs):
            (cwd / "solution.txt").write_text("done\n")
            (cwd / ".issue-contract.md").write_text("changed\n")
            Path(command[command.index("--output-last-message") + 1]).write_text("IMPLEMENTED\n")
            return ProcessOutcome(0, '{"type":"turn.completed"}\n', "", False, False)
        with patch.object(batch, "ROOT", self.root.resolve()):
            request = batch.queue_request("fake-batch", [task], "null", arm, runs)
            (request.parent / "APPROVED.json").write_text(json.dumps({"request_sha256": batch.sha256_file(request)}))
            batch.launch("fake-batch", runs, fake, require_auth=False)
        base = runs / "fake-batch/fake-task/null"
        results = [json.loads(path.read_text()) for path in base.glob("attempt-*/result.json")]
        self.assertEqual(len(results), 3)
        self.assertTrue(all(not row["valid"] and "protected input" in row["invalid_reason"] for row in results))


if __name__ == "__main__":
    unittest.main()
