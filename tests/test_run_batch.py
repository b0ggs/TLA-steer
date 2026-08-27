from __future__ import annotations
import contextlib
import hashlib
import io
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
    def runner(self, calls: list[tuple[str, bytes]], *, interrupt_first: bool = False,
               web_search_first: bool = False, expired_auth_first: bool = False):
        def fake(command, *, cwd, **_kwargs):
            md_name = next(item for item in ("ALT.md", "CODER.md") if (cwd / item).is_file())
            arm = (cwd / md_name).read_bytes()
            task_name = (cwd / ".issue-contract.md").read_text().split()[-1].rstrip(".\n")
            calls.append((task_name, arm))
            if expired_auth_first and len(calls) == 1:
                events = ('{"type":"thread.started"}\n{"type":"turn.started"}\n'
                          '{"type":"error","message":"error sending request for url"}\n'
                          '{"type":"turn.failed","error":{"message":"error sending request for url"}}\n')
                return ProcessOutcome(1, events, "401 Unauthorized: token_expired", False, False)
            if arm:
                (cwd / "solution.txt").write_text("done\n")
            Path(command[command.index("--output-last-message") + 1]).write_text("IMPLEMENTED\n")
            interrupted = interrupt_first and len(calls) == 1
            search = ('{"type":"item.started","item":{"id":"search-1","type":"web_search","query":"upstream fix"}}\n'
                      if web_search_first and len(calls) == 1 else "")
            return ProcessOutcome(0, search + '{"type":"turn.completed"}\n', "", False, interrupted)
        return fake
    def queued(self, task_names: list[str], *, same_arm: bool = False,
               md_filename: str = "ALT.md", seed: int = 7):
        tasks = [self.task(name) for name in task_names]
        arm_a = self.arm("a", b"")
        arm_b = arm_a if same_arm else self.arm("b", b"help\n")
        runs = self.root / "runs"
        with patch.object(batch, "ROOT", self.root.resolve()):
            request = batch.queue_request("fake-batch", tasks, [("a", arm_a), ("b", arm_b)],
                                          runs, md_filename=md_filename, task_order_seed=seed,
                                          require_auth=False)
        self.approve(request)
        return request, runs
    def test_fast_preflight_groups_pairs_is_hash_only_and_never_calls_subject(self):
        names = ["full-boltons-wraps-forwarding", "full-click-stream-lifecycle",
                 "full-flask-automatic-options", "full-starlette-websocket-denial"]
        tasks = [self.task(name) for name in names]
        arms = [("null", self.arm("null", b"")), ("probe", self.arm("probe", b"focus\n"))]
        images = {name: "sha256:" + digest * 64 for name, digest in zip(names, "aabc")}
        spec = {name: {"answer_bearing_modules": ["package.answer"],
                       "fix_signature_strings": ["a sufficiently long fix signature"],
                       "interpreter_pin": "3.11.5"} for name in names}
        spec_path = self.root / "contamination-spec.json"
        spec_path.write_bytes(batch._bytes(spec))
        container = {"image_digests": images,
                     "interpreter_pins": {name: "3.11.5" for name in names},
                     "spec_sha256": batch.sha256_file(spec_path), "web_search": "disabled"}
        values = batch.asdict(batch.RUNNER); values["timeout_seconds"] = 900
        auth = self.root / "auth"; auth.mkdir(); (auth / "auth.json").write_text("{}\n")
        calls = []
        def smoke(image, pin, task_ids, codex_home, deadline):
            calls.append((image, pin, task_ids, codex_home, deadline))
            return {"seal_schema": batch.sealed.FAST_SEAL_SCHEMA,
                    "image_digest": image, "interpreter_pin": pin,
                    "task_ids": task_ids, "spec_sha256": container["spec_sha256"],
                    "policy": "workspace-write-network-denied"}
        with patch.object(batch, "ROOT", self.root.resolve()), \
             patch.object(batch.sealed, "SPEC", spec_path), \
             patch.dict("os.environ", {"MDSEVAL_CODEX_HOME": str(auth)}, clear=False), \
             patch.object(batch.sealed, "subject", side_effect=AssertionError("model call")), \
             patch.object(batch.taskcheck, "run_checker", side_effect=AssertionError("checker called")):
            request = batch._request("cost-time-probe-v1", tasks, arms,
                                     task_order_seed=20260826,
                                     runner=batch.RunnerConfig(**values), container=container)
            result = batch.preflight_request(request, smoke=smoke)
        self.assertEqual((result["status"], result["failed_checks"]), ("PASS", []))
        self.assertEqual(len(calls), 3)
        self.assertEqual({task for call in calls for task in call[2]}, set(names))
        self.assertTrue(all(call[4] == calls[0][4] for call in calls))
        self.assertEqual(set(result["seals"]), set(names))

    def test_fast_preflight_failure_prevents_request_write(self):
        task, arm = self.task("task-1"), self.arm("a", b"")
        with patch.object(batch, "ROOT", self.root.resolve()):
            request = batch._request("failed-batch", [task], [("a", arm)], task_order_seed=1)
        failure = {"status": "FAIL", "duration_seconds": 0.1,
                   "failed_checks": ["runtime:image@pin"], "errors": {}, "seals": {}}
        runs = self.root / "runs"
        with patch.object(batch, "ROOT", self.root.resolve()), \
             patch.object(batch, "preflight_request", return_value=failure), \
             self.assertRaisesRegex(batch.BatchError, "runtime:image@pin"):
            batch.queue_request("failed-batch", [task], [("a", arm)], runs,
                                task_order_seed=1, require_auth=False)
        self.assertFalse((runs / "failed-batch" / "REQUEST.json").exists())

    def test_fast_preflight_uses_one_absolute_global_deadline(self):
        task, arm = self.task("task-1"), self.arm("a", b"")
        spec = {"task-1": {"answer_bearing_modules": ["package.answer"],
                            "fix_signature_strings": ["a sufficiently long fix signature"],
                            "interpreter_pin": "3.11.5"}}
        spec_path = self.root / "spec.json"; spec_path.write_bytes(batch._bytes(spec))
        image = "sha256:" + "a" * 64
        container = {"image_digests": {"task-1": image},
                     "interpreter_pins": {"task-1": "3.11.5"},
                     "spec_sha256": batch.sha256_file(spec_path), "web_search": "disabled"}
        auth = self.root / "auth"; auth.mkdir(); (auth / "auth.json").write_text("{}\n")
        clock = [0.0]; deadlines = []
        def smoke(_image, _pin, task_ids, _home, deadline):
            deadlines.append(deadline); clock[0] = 61.0
            return {"seal_schema": batch.sealed.FAST_SEAL_SCHEMA,
                    "image_digest": image, "interpreter_pin": "3.11.5",
                    "task_ids": task_ids, "spec_sha256": container["spec_sha256"]}
        with patch.object(batch, "ROOT", self.root.resolve()), \
             patch.object(batch.sealed, "SPEC", spec_path), \
             patch.dict("os.environ", {"MDSEVAL_CODEX_HOME": str(auth)}, clear=False):
            request = batch._request("deadline-batch", [task], [("a", arm)],
                                     task_order_seed=1, container=container)
            result = batch.preflight_request(request, monotonic=lambda: clock[0], smoke=smoke)
        self.assertEqual(deadlines, [60.0])
        self.assertEqual((result["status"], result["duration_seconds"]), ("FAIL", 61.0))
        self.assertIn("deadline", result["failed_checks"])

    def test_v3_run_preflights_once_and_reuses_task_seal(self):
        task = self.task("task-1")
        arm_a, arm_b = self.arm("a", b""), self.arm("b", b"focus\n")
        image = "sha256:" + "a" * 64
        container = {"image_digests": {task.name: image}, "spec_sha256": "b" * 64,
                     "interpreter_pins": {task.name: "3.11.5"}, "web_search": "disabled"}
        runs = self.root / "runs"
        with patch.object(batch, "ROOT", self.root.resolve()):
            request_path = batch.queue_request(
                "sealed-batch", [task], [("a", arm_a), ("b", arm_b)], runs,
                task_order_seed=1, container=container, require_auth=False)
        self.approve(request_path)
        seal = {"seal_schema": batch.sealed.FAST_SEAL_SCHEMA,
                "image_digest": image, "interpreter_pin": "3.11.5",
                "task_ids": [task.name], "spec_sha256": container["spec_sha256"]}
        result_lists = {}
        def state(base):
            values = result_lists.setdefault(str(base), [])
            return values, 0, len(values) + 1, len(values)
        def attempt(task_arg, request, arm, ordinal, batch_dir, _runner, _home, used_seal):
            path = batch_dir / task_arg.name / arm["name"] / f"attempt-{ordinal}" / "result.json"
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(batch._bytes({"ordinal": ordinal}))
            self.assertIs(used_seal, seal)
            return True
        preflight = {"status": "PASS", "duration_seconds": 1.0,
                     "failed_checks": [], "errors": {}, "seals": {task.name: seal}}
        with patch.object(batch, "ROOT", self.root.resolve()), \
             patch.object(batch, "preflight_request", return_value=preflight) as checked, \
             patch.object(batch, "_state", side_effect=state), \
             patch.object(batch, "_attempt", side_effect=attempt) as attempted, \
             patch.object(batch, "_launched_calls", return_value=0), \
             patch.object(batch, "_write_disposition"):
            batch.launch("sealed-batch", runs, require_auth=False)
        checked.assert_called_once()
        self.assertEqual(attempted.call_count, 6)

    def test_completed_sealed_v3_batch_verifies_without_runtime_preflight(self):
        task = self.task("task-1")
        arm_a, arm_b = self.arm("a", b""), self.arm("b", b"focus\n")
        image = "sha256:" + "a" * 64
        container = {"image_digests": {task.name: image}, "spec_sha256": "b" * 64,
                     "interpreter_pins": {task.name: "3.11.5"}, "web_search": "disabled"}
        runs = self.root / "runs"
        with patch.object(batch, "ROOT", self.root.resolve()):
            request_path = batch.queue_request(
                "sealed-batch", [task], [("a", arm_a), ("b", arm_b)], runs,
                task_order_seed=1, container=container, require_auth=False)
        self.approve(request_path)
        identity = {"image_digest": image, "canonical_executable": "/python/bin/python3.11"}
        seal = {"seal_schema": batch.sealed.FAST_SEAL_SCHEMA,
                "image_digest": image, "interpreter_pin": "3.11.5",
                "task_ids": [task.name], "spec_sha256": container["spec_sha256"],
                "identity": identity}
        preflight = {"status": "PASS", "duration_seconds": 1.0,
                     "failed_checks": [], "errors": {}, "seals": {task.name: seal}}
        def subject(_command, workspace, final_path, _stdin, _timeout, _home,
                    _image, _pin, _seal):
            if (workspace / "CODER.md").read_bytes():
                (workspace / "solution.txt").write_text("done\n")
            final_path.write_text("done\n")
            return ProcessOutcome(0, '{"type":"turn.completed"}\n', "", False, False)
        def checker(task_arg, workspace, _image, _pin, _home, expected):
            result, deterministic, duration = batch._checker(task_arg, workspace)
            return result, deterministic, duration, {"identity": expected, "runs": []}
        with patch.object(batch, "ROOT", self.root.resolve()), \
             patch.object(batch, "preflight_request", return_value=preflight) as checked, \
             patch.object(batch.sealed, "subject", side_effect=subject), \
             patch.object(batch.sealed, "checker", side_effect=checker):
            batch.launch("sealed-batch", runs, require_auth=False)
        checked.assert_called_once()
        with patch.object(batch, "ROOT", self.root.resolve()), \
             patch.object(batch, "_launch_record", side_effect=AssertionError("legacy evidence")), \
             patch.object(batch, "preflight_request", side_effect=AssertionError("runtime preflight")), \
             patch.object(batch.sealed, "fast_smoke", side_effect=AssertionError("Docker")), \
             patch.object(batch.sealed, "subject", side_effect=AssertionError("model call")):
            batch.verify_batch(request_path.parent)

    def test_preflight_cli_emits_exactly_one_final_json_object(self):
        argv = ["preflight", "cli-batch", "--task", "tasks/task-1",
                "--arm", "a", "controls/a.md"]
        passed = {"status": "PASS", "duration_seconds": 1.25,
                  "failed_checks": [], "errors": {}, "seals": {}}
        for expected, request_effect, result in ((0, None, passed),
                                                  (1, batch.BatchError("bad"), None)):
            output = io.StringIO()
            request_patch = ({"return_value": {}} if request_effect is None
                             else {"side_effect": request_effect})
            with patch.object(batch, "_request", **request_patch), \
                 patch.object(batch, "preflight_request", return_value=result), \
                 contextlib.redirect_stdout(output):
                code = batch.main(argv)
            rows = output.getvalue().splitlines()
            self.assertEqual((code, len(rows)), (expected, 1))
            record = json.loads(rows[0])
            self.assertEqual(record["status"], "PASS" if expected == 0 else "FAIL")
            self.assertIn("duration_seconds", record)
            self.assertIn("failed_checks", record)
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
        launch_command = " ".join(json.loads(next(request.parent.glob("task-*/b/attempt-1/launch.json")).read_text())["command"])
        self.assertIn('project_doc_fallback_filenames=["ALT.md"]', launch_command)
        self.assertIn('web_search="disabled"', launch_command)
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
    def test_expired_provider_token_is_replaced_without_altering_raw_events(self):
        request, runs = self.queued(["task-1"])
        calls: list[tuple[str, bytes]] = []
        with patch.object(batch, "ROOT", self.root.resolve()):
            batch.launch("fake-batch", runs, self.runner(calls, expired_auth_first=True), require_auth=False)
            batch.verify_batch(request.parent)
        attempt = request.parent / "task-1/a/attempt-1"
        self.assertEqual(len(calls), 7)
        self.assertTrue((attempt / "infra-invalid.json").is_file())
        self.assertFalse((attempt / "result.json").exists())
        self.assertNotIn("unauthorized token_expired", (attempt / "events.jsonl").read_text())
    def test_web_search_event_is_fatal_evidence_not_a_replacement(self):
        request, runs = self.queued(["task-1"])
        calls: list[tuple[str, bytes]] = []
        with patch.object(batch, "ROOT", self.root.resolve()):
            batch.launch("fake-batch", runs, self.runner(
                calls, interrupt_first=True, web_search_first=True), require_auth=False)
            batch.verify_batch(request.parent)
        result = json.loads((request.parent / "task-1/a/attempt-1/result.json").read_text())
        self.assertEqual((len(calls), result["valid"], result["invalid_reason"]),
                         (6, False, "fatal evidence defect: web_search tool item in events"))
        self.assertFalse((request.parent / "task-1/a/attempt-1/infra-invalid.json").exists())
        self.assertEqual(json.loads((request.parent / "task-1/a/disposition.json").read_text())["label"], "invalid")
    def test_v3_queue_uses_hash_only_verification_and_needs_no_preflight_directory(self):
        task, arm = self.task("task-1", alt_sensitive=True), self.arm("a", b"")
        container = {"image_digests": {task.name: "sha256:" + "a" * 64}, "spec_sha256": "b" * 64,
                     "interpreter_pins": {task.name: "3.11.5"}, "web_search": "disabled"}
        with patch.object(batch, "ROOT", self.root.resolve()), patch.object(
                batch, "_launch_record", side_effect=AssertionError("legacy preflight used")), patch.object(
                batch.taskcheck, "verify", wraps=taskcheck.verify) as verified:
            request_path = batch.queue_request(
                "sealed-batch", [task], [("a", arm)], self.root / "runs",
                md_filename="ALT.md", container=container, require_auth=False)
        self.assertTrue(all(call.kwargs["md_filename"] is None
                            for call in verified.call_args_list))
        self.assertEqual(json.loads(request_path.read_text())["schema_version"], 3)
        self.assertFalse((request_path.parent / "preflight").exists())
    def test_container_schema_is_exact_and_removed_before_runner_config(self):
        task_ids = {"task-1", "task-2"}
        digest = "sha256:" + "a" * 64
        container = {"image_digests": {task: digest for task in task_ids}, "spec_sha256": "b" * 64,
                     "interpreter_pins": {task: "3.11.5" for task in task_ids}}
        self.assertIs(batch._container(container, task_ids), container)
        with self.assertRaisesRegex(batch.BatchError, "container schema"):
            batch._container(container, task_ids, require_search_disabled=True)
        sealed_container = {**container, "web_search": "disabled"}
        self.assertIs(batch._container(sealed_container, task_ids, require_search_disabled=True), sealed_container)
        runner = batch.asdict(batch.RUNNER); runner["container"] = container
        self.assertEqual(batch._runner(runner), batch.RUNNER)
        invalid = dict(container); invalid["extra"] = True
        with self.assertRaisesRegex(batch.BatchError, "container schema"): batch._container(invalid, task_ids)
        missing = dict(container); missing["image_digests"] = {"task-1": digest}
        with self.assertRaisesRegex(batch.BatchError, "task binding"): batch._container(missing, task_ids)
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
    def test_v3_900_second_timeout_is_independent_and_v2_boundary_stays_read_only(self):
        task, arm = self.task("task-1"), self.arm("a", b"")
        values = batch.asdict(batch.RUNNER); values["timeout_seconds"] = 900; runner = batch.RunnerConfig(**values)
        with patch.object(batch, "ROOT", self.root.resolve()):
            request_path = batch.queue_request(
                "full-scale", [task], [("a", arm)], self.root / "runs",
                task_order_seed=1, runner=runner, require_auth=False)
        request = json.loads(request_path.read_text())
        self.assertEqual((request["schema_version"], request["runner"]["timeout_seconds"]), (3, 900))
        self.assertNotIn("comparability_note", request)
        taskcheck._validate_batch_request_v3(request, "full-scale", {1})
        legacy = dict(request); legacy.pop("schema_version")
        legacy["runner"] = {**legacy["runner"], "timeout_seconds": 600}
        legacy["comparability_note"] = taskcheck.COMPARABILITY_NOTE
        taskcheck._validate_batch_request(legacy, "full-scale", {1})
        legacy["comparability_note"] += " altered"
        with self.assertRaisesRegex(taskcheck.TaskError, "REQUEST schema"):
            taskcheck._validate_batch_request(legacy, "full-scale", {1})
    def test_section14_preflight_accepts_bound_host_na(self):
        ids = ["task-1", "task-2"]; image, spec, manifest = "sha256:" + "a" * 64, "b" * 64, "e" * 64
        container = {"image_digests": {key: image for key in ids}, "spec_sha256": spec,
                     "interpreter_pins": {key: "3.11.5" for key in ids}}
        common = {"task_id": ids[0], "image_digest": image, "spec_sha256": spec}; identity = {"canonical_executable": "/python/bin/python3.11"}
        host = {**common, "check": "summary", "status": "N/A", "reason": "fix absent on host",
                "absence_evidence": [{"target": "module.symbol", "status": "ABSENT"}],
                "contamination_count": 0, "failure_count": 0, "spec_task_ids": ids}
        probe = {**common, "check": "summary", "status": "ALL_GREEN", "runtime_security_sha256": "c" * 64,
                 "policy_sha256": "d" * 64, "spec_task_ids": ids}
        environment = {**common, "status": "ALL_GREEN", "task_manifest_sha256": manifest, "spec_task_ids": ids, "interpreter_pin": "3.11.5",
                       "runtime_security_sha256": "c" * 64, "identity": identity}
        root, run = self.root.resolve(), self.root / "runs" / "full-scale"
        for kind, suffix, rows in (("host", "jsonl", [host]), ("container", "jsonl", [
                {"check": "runtime_policy_identity", "status": "PASS", "identity": {"subject": identity}}, probe])):
            path = run / "preflight" / kind / f"{ids[0]}.{suffix}"; path.parent.mkdir(parents=True)
            path.write_text("".join(json.dumps(row) + "\n" for row in rows)); path.with_suffix(".jsonl.stderr").touch()
        path = run / "preflight" / "environment" / f"{ids[0]}.json"; path.parent.mkdir(parents=True); path.write_bytes(batch._bytes(environment)); path.with_suffix(".json.stderr").touch()
        with patch.object(batch, "ROOT", root), patch.object(batch, "run_git", return_value=""):
            seal = batch._launch_record(run, ids[0], container, manifest, True); self.assertEqual(seal["identity"], identity)
            host["spec_task_ids"] = [ids[0]]; (run / "preflight" / "host" / f"{ids[0]}.jsonl").write_text(json.dumps(host) + "\n")
            with self.assertRaisesRegex(batch.BatchError, "task-id set"): batch._launch_record(run, ids[0], container, manifest, True)
            host["spec_task_ids"], host["check"] = ids, "not-summary"; (run / "preflight" / "host" / f"{ids[0]}.jsonl").write_text(json.dumps(host) + "\n")
            with self.assertRaisesRegex(batch.BatchError, "event stream"): batch._launch_record(run, ids[0], container, manifest, True)
            (run / "preflight" / "host" / f"{ids[0]}.jsonl").write_text("{\n")
            with self.assertRaisesRegex(batch.BatchError, "malformed probe event stream"): batch._launch_record(run, ids[0], container, manifest, True)
            host["check"] = "summary"; (run / "preflight" / "host" / f"{ids[0]}.jsonl").write_text(json.dumps(host) + "\n"); environment["task_manifest_sha256"] = "f" * 64; path.write_bytes(batch._bytes(environment))
            with self.assertRaisesRegex(batch.BatchError, "binding mismatch"): batch._launch_record(run, ids[0], container, manifest, True)
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
        sealed = REPO / "runs" / "dev-v2" / "phase3-real-null-sealed-v1"; before = self.tree_digest(sealed)
        with patch.object(batch.taskcheck, "verify", wraps=taskcheck.verify) as verified: batch.verify_batch(sealed); batch.launch(sealed.name, sealed.parent, lambda *_a, **_k: self.fail("unexpected launch"), require_auth=False)
        self.assertEqual(self.tree_digest(sealed), before)
        self.assertEqual({call.kwargs["md_filename"] for call in verified.call_args_list}, {None})
    @staticmethod
    def tree_digest(root: Path) -> str:
        digest = hashlib.sha256()
        for path in sorted(item for item in root.rglob("*") if item.is_file()):
            digest.update(path.relative_to(root).as_posix().encode() + b"\0" + path.read_bytes())
        return digest.hexdigest()
if __name__ == "__main__":
    unittest.main()
