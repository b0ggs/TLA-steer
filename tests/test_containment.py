import contextlib
import errno
import io
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from scripts.contain import probe, runtime


SIGNATURE = "maximum difficulty synthetic fix signature"
IMAGE = "sha256:" + "a" * 64


def item(target="missing_package.answer"):
    return {"answer_bearing_modules": [target],
            "fix_signature_strings": [SIGNATURE], "interpreter_pin": "3.11.5"}


def spec(count=3):
    return {f"cohort-task-{number}": item() for number in range(count)}


class ContaminationSpecTests(unittest.TestCase):
    def load(self, value):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "spec.json"
            path.write_text(json.dumps(value), encoding="utf-8")
            with contextlib.redirect_stdout(io.StringIO()):
                return probe.load_spec(path)

    def test_dynamic_three_to_five_task_specs(self):
        for count in (3, 4, 5):
            loaded, digest, task_ids = self.load(spec(count))
            self.assertEqual(loaded, spec(count))
            self.assertEqual(task_ids, sorted(spec(count)))
            self.assertRegex(digest, r"^[0-9a-f]{64}$")
        for count in (2, 6):
            self.assertIsNone(self.load(spec(count))[0])

    def test_every_entry_requires_targets_signatures_and_pin(self):
        for key, value in (("answer_bearing_modules", []),
                           ("fix_signature_strings", []),
                           ("interpreter_pin", "3.11")):
            candidate = spec()
            candidate["cohort-task-0"][key] = value
            self.assertIsNone(self.load(candidate)[0])
        self.assertTrue(probe.valid_item(item("filesystem:pkg/answer.py")))
        self.assertFalse(probe.valid_item(item("filesystem:../answer.py")))


class ProbeSummaryTests(unittest.TestCase):
    def run_host(self, inspect_side_effect=None, exclusion_side_effect=None):
        value = spec()
        output = io.StringIO()
        inspect_effect = inspect_side_effect or (lambda unused: [{"source_available": False}])
        exclude_effect = exclusion_side_effect or (lambda *unused: ["/excluded"])
        with mock.patch.object(probe, "load_spec", return_value=(value, "b" * 64, sorted(value))), \
             mock.patch.object(probe, "exclusions", side_effect=exclude_effect), \
             mock.patch.object(probe, "inspect_targets", side_effect=inspect_effect), \
             mock.patch.object(probe, "scan", return_value={"file_count": 7}), \
             mock.patch.object(probe, "mount_check") as mounts, \
             mock.patch.object(probe, "environment_check") as environment, \
             mock.patch.object(probe.sys, "argv", ["probe.py", "host", "cohort-task-0", IMAGE, "spec.json"]), \
             contextlib.redirect_stdout(output):
            return_code = probe.main()
        mounts.assert_not_called()
        environment.assert_not_called()
        return return_code, json.loads(output.getvalue().splitlines()[-1])

    def test_clean_host_is_machine_readable_na(self):
        return_code, summary = self.run_host()
        self.assertEqual(return_code, 0)
        self.assertEqual(summary["status"], "N/A")
        self.assertEqual(summary["spec_task_ids"], sorted(spec()))
        self.assertEqual(summary["failure_count"], 0)
        self.assertEqual(summary["contamination_count"], 0)
        self.assertTrue(summary["reason"])
        self.assertTrue(summary["absence_evidence"])

    def test_clean_explicit_hit_is_expected_red(self):
        def contaminated(unused):
            probe.emit("UNDECODABLE_FIXTURE", "FINDING",
                       path="/Library/Frameworks/Python.framework/Lib/test/bad_coding.py",
                       error_class="SyntaxError")
            probe.hit("literal_target", target="installed.answer")
            return []
        return_code, summary = self.run_host(contaminated)
        self.assertEqual((return_code, summary["status"]), (0, "EXPECTED_RED"))
        self.assertEqual(summary["contamination_count"], 1)

    def test_structural_failure_is_neither_red_nor_na(self):
        def contaminated_and_bad(unused):
            probe.hit("literal_target", target="installed.answer")
            probe.mark("global_scan_errors", False, error="decode")
            return []
        return_code, summary = self.run_host(contaminated_and_bad)
        self.assertEqual((return_code, summary["status"]), (2, "CONTROL_FAILED"))
        self.assertEqual((summary["contamination_count"], summary["failure_count"]), (1, 1))

    def test_container_requires_every_leg_green(self):
        value = spec()
        def run(environment_effect=None):
            output = io.StringIO()
            with mock.patch.object(probe, "load_spec", return_value=(value, "b" * 64, sorted(value))), \
                 mock.patch.object(probe, "exclusions", return_value=[]), \
                 mock.patch.object(probe, "inspect_targets", return_value=[]), \
                 mock.patch.object(probe, "scan", return_value={"file_count": 1}), \
                 mock.patch.object(probe, "mount_check"), \
                 mock.patch.object(probe, "environment_check", side_effect=environment_effect), \
                 mock.patch.object(probe, "runtime_check", return_value=("c" * 64, "d" * 64)), \
                 mock.patch.object(probe.sys, "argv", ["probe.py", "container", "cohort-task-0", IMAGE, "spec.json", "runtime.json"]), \
                 contextlib.redirect_stdout(output):
                code = probe.main()
            return code, json.loads(output.getvalue().splitlines()[-1])
        self.assertEqual(run()[1]["status"], "ALL_GREEN")
        failed = run(lambda unused: probe.mark("sealed_deps", False, error="missing"))
        self.assertEqual((failed[0], failed[1]["status"]), (2, "BUILD_REJECTED"))


class ScanAndRuntimeTests(unittest.TestCase):
    def test_resolved_web_search_requires_effective_session_flag(self):
        result = {"config": {"web_search": "disabled"},
                  "origins": {"web_search": {"name": {"type": "sessionFlags"}}},
                  "layers": [{"name": {"type": "sessionFlags"},
                              "config": {"web_search": "disabled"}}]}
        self.assertEqual(runtime._resolved_web_search({"result": result}),
                         runtime.WEB_SEARCH_DISABLED_EVIDENCE)
        for key, value in (("config", {"web_search": "cached"}),
                           ("origins", {}), ("layers", [])):
            bad = {name: item.copy() if isinstance(item, dict) else list(item)
                   for name, item in result.items()}
            bad[key] = value
            with self.assertRaisesRegex(RuntimeError, "web search"):
                runtime._resolved_web_search({"result": bad})

    def test_host_and_container_use_asymmetric_recorded_scan_roots(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve()
            (root / "clean.py").write_text("clean = True\n", encoding="utf-8")
            output = io.StringIO()
            probe.BAD.clear(); probe.CONTAM.clear()
            with mock.patch.object(probe, "host_roots", return_value=[str(root)]), \
                 contextlib.redirect_stdout(output):
                host = probe.scan(item(), "/workspace", [], "host")
            rows = [json.loads(line) for line in output.getvalue().splitlines()]
            roots = next(row for row in rows if row["check"] == "global_scan_roots")
            self.assertEqual((host["scan_roots"], roots["scan_roots"]),
                             ([str(root)], [str(root)]))
            self.assertEqual(roots["mode"], "host")

            real_walk = os.walk
            with mock.patch.object(probe, "host_roots") as discovery, \
                 mock.patch.object(probe.os, "walk",
                                   side_effect=lambda path, **kwargs: real_walk(root, **kwargs)), \
                 contextlib.redirect_stdout(io.StringIO()):
                probe.BAD.clear(); probe.CONTAM.clear()
                container = probe.scan(item(), "/workspace", [], "container")
            discovery.assert_not_called()
            self.assertEqual(container["scan_roots"], ["/"])

    def test_host_root_discovery_records_every_prefix_and_site_package(self):
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary).resolve()
            binary = base / "bin"
            binary.mkdir()
            discovered = binary / "python3.12"
            discovered.write_text("", encoding="utf-8")
            discovered.chmod(0o755)
            current_prefix = base / "current"
            current_site = current_prefix / "lib/python3.11/site-packages"
            user_site = base / "user/python3.11/site-packages"
            missing_site = base / "missing/python3.11/site-packages"
            other_prefix = base / "other"
            other_site = other_prefix / "lib/python3.12/site-packages"
            for directory in (current_site, user_site, other_site):
                directory.mkdir(parents=True)
            rows = {
                "/current/python": {
                    "prefix": str(current_prefix),
                    "site_packages": [str(current_site), str(user_site), str(missing_site)],
                },
                str(discovered.resolve()): {
                    "prefix": str(other_prefix),
                    "site_packages": [str(other_site)],
                },
            }

            def query(command, **unused):
                return probe.subprocess.CompletedProcess(
                    command, 0, json.dumps(rows[command[0]]) + "\n", "")

            output = io.StringIO()
            probe.BAD.clear(); probe.CONTAM.clear()
            with mock.patch.object(probe.sys, "executable", "/current/python"), \
                 mock.patch.dict(probe.os.environ, {"PATH": str(binary)}), \
                 mock.patch.object(probe.subprocess, "run", side_effect=query), \
                 contextlib.redirect_stdout(output):
                roots = probe.host_roots()
            record = json.loads(output.getvalue().splitlines()[-1])
            self.assertEqual(record["check"], "host_root_discovery")
            self.assertEqual(record["status"], "PASS")
            self.assertIn("/Library/Frameworks", record["reported_roots"])
            self.assertIn(str(current_prefix), roots)
            self.assertIn(str(user_site), roots)
            self.assertIn(str(missing_site), record["missing_reported_roots"])
            self.assertNotIn(str(missing_site), roots)
            for value in rows.values():
                self.assertIn(value["prefix"], record["required_roots"])
                for package in value["site_packages"]:
                    self.assertIn(package, record["reported_roots"])
                    if Path(package).is_dir():
                        self.assertIn(package, record["required_roots"])

    def test_undecodable_fixture_is_host_finding_but_container_failure(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve()
            bad = root / "bad_coding.py"
            bad.write_bytes(b"# coding: uft-8\nvalue = 1\n")
            output = io.StringIO()
            probe.BAD.clear(); probe.CONTAM.clear()
            with mock.patch.object(probe, "host_roots", return_value=[str(root)]), \
                 contextlib.redirect_stdout(output):
                host = probe.scan(item(), "/workspace", [], "host")
            findings = [json.loads(line) for line in output.getvalue().splitlines()
                        if '"check":"UNDECODABLE_FIXTURE"' in line]
            self.assertEqual(findings, [{"check": "UNDECODABLE_FIXTURE",
                                         "error_class": "SyntaxError",
                                         "path": str(bad), "status": "FINDING"}])
            self.assertEqual((probe.BAD, probe.CONTAM), ([], []))
            self.assertEqual(host["undecodable_fixtures"],
                             [{"path": str(bad), "error_class": "SyntaxError"}])

            real_walk = os.walk
            with mock.patch.object(probe.os, "walk",
                                   side_effect=lambda unused, **kwargs: real_walk(root, **kwargs)), \
                 contextlib.redirect_stdout(io.StringIO()):
                probe.BAD.clear(); probe.CONTAM.clear()
                container = probe.scan(item(), "/workspace", [], "container")
            self.assertIn("global_scan_errors", probe.BAD)
            self.assertEqual(container["undecodable_fixtures"], [])

    def test_scan_excludes_task_and_evidence_but_detects_build_copy(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve()
            task, evidence, build = (root / name for name in ("cohort-task-0", "evidence", "build"))
            for directory in (task / "public", task / "reference", evidence, build):
                directory.mkdir(parents=True)
            for path in (task / "reference/answer.py", evidence / "answer.py"):
                path.write_text(SIGNATURE, encoding="utf-8")
            answer = build / "answer.py"
            answer.write_text("visible_but_clean = True\n", encoding="utf-8")
            real_walk = os.walk
            with mock.patch.object(probe.os, "walk", side_effect=lambda unused, **kwargs: real_walk(root, **kwargs)), \
                 contextlib.redirect_stdout(io.StringIO()):
                probe.BAD.clear(); probe.CONTAM.clear()
                evidence_row = probe.scan(item("filesystem:answer.py"), str(task / "public"), [str(task), str(evidence)])
                self.assertEqual((probe.BAD, probe.CONTAM), ([], []))
                self.assertGreaterEqual(evidence_row["file_count"], 1)
                self.assertEqual(evidence_row["scan_roots"], ["/"])
                answer.write_text(SIGNATURE, encoding="utf-8")
                probe.BAD.clear(); probe.CONTAM.clear()
                probe.scan(item("filesystem:answer.py"), str(task / "public"), [str(task), str(evidence)])
                self.assertIn("global_signature_scan", probe.CONTAM)

    def test_permission_and_other_walk_errors_fail_closed(self):
        def walk_with(error):
            def fake(unused, *, onerror, **kwargs):
                onerror(error)
                return iter([])
            return fake
        with contextlib.redirect_stdout(io.StringIO()):
            probe.BAD.clear(); probe.CONTAM.clear()
            with mock.patch.object(probe.os, "walk", side_effect=walk_with(PermissionError(errno.EACCES, "denied", "/closed"))):
                probe.scan(item(), "/workspace", [])
            self.assertIn("global_scan_errors", probe.BAD)
            with mock.patch.object(probe.os, "walk", side_effect=walk_with(OSError(errno.EIO, "broken", "/broken"))):
                probe.BAD.clear(); probe.scan(item(), "/workspace", [])
            self.assertIn("global_scan_errors", probe.BAD)

    def test_sealed_dependencies_are_image_owned_and_host_roots_are_exact(self):
        dockerfile = (runtime.ROOT / "scripts/contain/Dockerfile").read_text(encoding="utf-8")
        self.assertIn("COPY sealed-deps /sealed-deps", dockerfile)
        self.assertIn("install -y --no-install-recommends git tinyproxy", dockerfile)
        self.assertIn("PYTHONPATH=/sealed-deps", runtime.FIXED_ENV)
        self.assertNotIn("sealed-deps", " ".join(value for value in runtime.security_args(IMAGE, "3.11.5") if value.endswith(":ro") or value.endswith(":rw")))
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve()
            (root / "tasks/cohort-task-0/public").mkdir(parents=True)
            output = root / "runs/batch/preflight/host/cohort-task-0.jsonl"
            with mock.patch.object(runtime, "ROOT", root):
                environment = runtime.host_env("cohort-task-0", output)
            roots = json.loads(environment["MDSEVAL_PROBE_EXCLUSIONS"])
            self.assertEqual(set(roots), {"task", "evidence"})
            self.assertEqual(roots["evidence"], str(root / "runs/batch"))
            self.assertEqual(environment["MDSEVAL_WORKSPACE"], str(root / "tasks/cohort-task-0/public"))

    def test_environment_binds_canonical_taskcheck_manifest_digest(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            task = root / "source-tasks/cohort-task-0"
            (task / "public").mkdir(parents=True)
            (task / "reference").mkdir()
            spec_path = root / "contamination-spec.json"
            spec_path.write_text(json.dumps(spec()), encoding="utf-8")
            identity = {"executable": "/python/bin/python3"}
            public = ({"resolved": False, "regressions": {"baseline": True}}, True,
                      0.1, {"identity": identity})
            reference = ({"resolved": True, "regressions": {"baseline": True}}, True,
                         0.1, {"identity": identity})
            digest = "e" * 64
            row = {"task_id": task.name, "verified": True,
                   "manifest_sha256": digest}

            def run(stdout):
                verify = runtime.ProcessOutcome(0, stdout, "", False, False)
                with mock.patch.object(runtime, "SPEC", spec_path), \
                     mock.patch.object(runtime, "image_id"), \
                     mock.patch.object(runtime, "_run", return_value=(verify, [])), \
                     mock.patch.object(runtime, "checker", side_effect=[public, reference]):
                    return runtime.environment(task, IMAGE, "3.11.5", root)

            accepted = run(runtime.canonical(row) + "\n")
            self.assertEqual(accepted["status"], "ALL_GREEN")
            self.assertEqual(accepted["task_manifest_sha256"], digest)

            noncanonical = run(json.dumps(row) + "\n")
            self.assertEqual(noncanonical["status"], "EXCLUDED")
            self.assertEqual(noncanonical["task_manifest_sha256"], digest)

            row["manifest_sha256"] = "not-a-digest"
            invalid = run(runtime.canonical(row) + "\n")
            self.assertEqual(invalid["status"], "EXCLUDED")
            self.assertIsNone(invalid["task_manifest_sha256"])


class FastRuntimeSmokeTests(unittest.TestCase):
    def identity(self, image=IMAGE):
        return {"canonical_executable": "/python/bin/python3.11",
                "version": "3.11.5 (sealed)", "executable_sha256": "1" * 64,
                "image_digest": image, "path_resolution": "/python/bin/python3"}

    def inspection(self, value, image=IMAGE):
        checks = []
        for task_id in sorted(value):
            for target in value[task_id]["answer_bearing_modules"]:
                checks.append({"task_id": task_id, "target": target,
                               "source_available": False, "source_sha256": [],
                               "checked_signature_sha256": sorted(
                                   runtime.sha(signature.encode())
                                   for signature in value[task_id]["fix_signature_strings"])})
        return {"status": "PASS", "identity": self.identity(image),
                "mounts": runtime.FAST_MOUNTS, "auth": "isolated-readable",
                "bare_connect": True, "target_checks": checks}

    @contextlib.contextmanager
    def network(self, unused_image, **unused):
        yield "isolated-network", "172.20.0.2"

    def test_fast_smoke_returns_compact_deterministic_pair_seal(self):
        value = spec()
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            spec_path = root / "spec.json"
            spec_path.write_text(json.dumps(value), encoding="utf-8")
            selected = {key: value[key] for key in ("cohort-task-1", "cohort-task-0")}
            inspection = self.inspection(selected)
            policy = {"identity": self.identity(), "policy_sha256": "2" * 64,
                      "web_search": runtime.WEB_SEARCH_DISABLED_EVIDENCE}
            deadline = runtime.time.monotonic() + 60
            with mock.patch.object(runtime, "SPEC", spec_path), \
                 mock.patch.object(runtime, "_pin_path", return_value=root), \
                 mock.patch.object(runtime, "image_id", return_value=IMAGE) as image_check, \
                 mock.patch.object(runtime, "_network", side_effect=self.network) as network, \
                 mock.patch.object(runtime, "_targeted_smoke", return_value=inspection) as targeted, \
                 mock.patch.object(runtime, "_fast_policy", return_value=policy) as policy_check, \
                 mock.patch.object(runtime, "probe") as legacy_probe, \
                 mock.patch.object(runtime, "environment") as legacy_environment, \
                 mock.patch.object(runtime, "checker") as checker:
                first = runtime.fast_smoke(
                    IMAGE, "3.11.5", ["cohort-task-1", "cohort-task-0"], root, deadline)
                second = runtime.fast_smoke(
                    IMAGE, "3.11.5", ["cohort-task-1", "cohort-task-0"], root, deadline)
            self.assertEqual(first, second)
            self.assertEqual(set(first), runtime._FAST_SEAL_KEYS)
            self.assertEqual(first["seal_schema"], runtime.FAST_SEAL_SCHEMA)
            self.assertEqual(first["task_ids"], ["cohort-task-0", "cohort-task-1"])
            self.assertEqual((image_check.call_count, network.call_count,
                              targeted.call_count, policy_check.call_count), (2, 2, 2, 2))
            legacy_probe.assert_not_called()
            legacy_environment.assert_not_called()
            checker.assert_not_called()

    def test_fast_smoke_rejects_expired_deadline_before_external_work(self):
        with mock.patch.object(runtime, "image_id") as image_check, \
             mock.patch.object(runtime, "_network") as network, \
             mock.patch.object(runtime, "_targeted_smoke") as targeted:
            with self.assertRaisesRegex(TimeoutError, "global preflight deadline"):
                runtime.fast_smoke(IMAGE, "3.11.5", ["cohort-task-0"], Path("auth"),
                                   runtime.time.monotonic() - 1)
        image_check.assert_not_called()
        network.assert_not_called()
        targeted.assert_not_called()

    def test_fast_smoke_rejects_bad_pin_and_symlink_pin_source(self):
        value = spec()
        value["cohort-task-0"]["interpreter_pin"] = "3.10.14"
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            spec_path = root / "spec.json"
            spec_path.write_text(json.dumps(value), encoding="utf-8")
            with mock.patch.object(runtime, "SPEC", spec_path):
                with self.assertRaisesRegex(RuntimeError, "pin differs"):
                    runtime._smoke_spec(["cohort-task-0"], "3.11.5")

            pins = root / "pins"
            real = pins / "3.11.5"
            real.mkdir(parents=True)
            (pins / "3.11.6").symlink_to(real, target_is_directory=True)
            with mock.patch.object(runtime, "PINS", pins):
                self.assertEqual(runtime._pin_path("3.11.5"), real.resolve())
                with self.assertRaisesRegex(RuntimeError, "unsafe interpreter pin source"):
                    runtime._pin_path("3.11.6")
                with self.assertRaisesRegex(RuntimeError, "unsafe interpreter pin"):
                    runtime._pin_path("../3.11.5")

    def test_targeted_smoke_fails_closed_on_incomplete_proof(self):
        value = spec(3)
        selected = {"cohort-task-0": value["cohort-task-0"]}
        good = self.inspection(selected)

        def run(row):
            outcome = runtime.ProcessOutcome(0, runtime.canonical(row) + "\n", "", False, False)
            with mock.patch.object(runtime, "_run", return_value=(outcome, [])):
                return runtime._targeted_smoke(
                    IMAGE, "3.11.5", selected, Path("workspace"), Path("auth"),
                    "network", "172.20.0.2", runtime.time.monotonic() + 60)

        self.assertEqual(run(good)["target_checks"], good["target_checks"])
        bad_mount = {**good, "mounts": {"/workspace": "ro"}}
        with self.assertRaisesRegex(RuntimeError, "proof is incomplete"):
            run(bad_mount)
        bad_targets = {**good, "target_checks": []}
        with self.assertRaisesRegex(RuntimeError, "coverage is incomplete"):
            run(bad_targets)
        failed = {"status": "FAIL", "error": "fix signature present"}
        outcome = runtime.ProcessOutcome(2, runtime.canonical(failed) + "\n", "", False, False)
        with mock.patch.object(runtime, "_run", return_value=(outcome, [])), \
             self.assertRaisesRegex(RuntimeError, "fix signature present"):
            runtime._targeted_smoke(
                IMAGE, "3.11.5", selected, Path("workspace"), Path("auth"),
                "network", "172.20.0.2", runtime.time.monotonic() + 60)

    def test_fast_policy_requires_network_denial_and_effective_disabled_search(self):
        identity = self.identity()
        source = {"status": "DENIED", "identity": identity,
                  "permission_profile": {"type": "managed"},
                  "policy_sha256": "2" * 64, "socket_target": ["172.20.0.2", 8888],
                  "denial": "PermissionError: [Errno 1] Operation not permitted",
                  "exit_status": errno.EPERM}
        config = {"id": 2, "result": {
            "config": {"web_search": "disabled"},
            "origins": {"web_search": {"name": {"type": "sessionFlags"}}},
            "layers": [{"name": {"type": "sessionFlags"},
                        "config": {"web_search": "disabled"}}]}}

        def run(source_row, config_row=config):
            reply = {"id": 3, "result": {"stdout": runtime.canonical(source_row) + "\n"}}
            stdout = runtime.canonical(config_row) + "\n" + runtime.canonical(reply) + "\n"
            outcome = runtime.ProcessOutcome(0, stdout, "", False, False)
            with mock.patch.object(runtime, "_run", return_value=(outcome, [])):
                return runtime._fast_policy(
                    IMAGE, "3.11.5", Path("workspace"), Path("auth"), "network",
                    "172.20.0.2", runtime.time.monotonic() + 60)

        self.assertEqual(run(source)["web_search"], runtime.WEB_SEARCH_DISABLED_EVIDENCE)
        allowed = {**source, "status": "FAIL", "denial": None, "exit_status": 0}
        with self.assertRaisesRegex(RuntimeError, "network-denied"):
            run(allowed)
        enabled = json.loads(json.dumps(config))
        enabled["result"]["config"]["web_search"] = "live"
        with self.assertRaisesRegex(RuntimeError, "web search"):
            run(source, enabled)

    def test_fast_scripts_are_targeted_and_make_no_model_request(self):
        compile(runtime._TARGETED_SMOKE_SCRIPT, "<targeted-smoke>", "exec")
        compile(runtime._POLICY_CHILD_SCRIPT, "<policy-child>", "exec")
        self.assertNotIn("os.walk", runtime._TARGETED_SMOKE_SCRIPT)
        self.assertNotIn("rglob", runtime._TARGETED_SMOKE_SCRIPT)
        messages = runtime._fast_policy_messages("172.20.0.2", IMAGE)
        self.assertEqual([row["method"] for row in messages],
                         ["initialize", "initialized", "config/read", "command/exec"])
        rendered = runtime.canonical(messages).lower()
        for forbidden in ("turn/start", "thread/start", "model/request", "responses"):
            self.assertNotIn(forbidden, rendered)
        child = messages[-1]["params"]["command"]
        self.assertNotIn("probe.py", child)

    def test_subject_reuses_fast_seal_without_policy_probe(self):
        task_id = "full-boltons-wraps-forwarding"
        identity = self.identity()
        core = {"seal_schema": runtime.FAST_SEAL_SCHEMA, "image_digest": IMAGE,
                "interpreter_pin": "3.11.5", "task_ids": [task_id],
                "spec_sha256": runtime.sha(runtime.SPEC.read_bytes()),
                "runtime_security_sha256": runtime.security_sha256(IMAGE, "3.11.5"),
                "policy_sha256": "2" * 64, "identity": identity,
                "web_search": runtime.WEB_SEARCH_DISABLED_EVIDENCE,
                "mounts": runtime.FAST_MOUNTS, "sandbox": runtime.FAST_SANDBOX,
                "auth": "isolated-readable", "target_checks_sha256": "3" * 64}
        seal = runtime._seal(core)
        outcome = runtime.ProcessOutcome(0, "", "", False, False)
        with tempfile.TemporaryDirectory() as temporary:
            workspace = Path(temporary)
            command = ["codex", "--config", runtime.WEB_SEARCH_DISABLED_CONFIG,
                       "--cd", str(workspace), "--output-last-message", str(workspace / "final")]
            with mock.patch.object(runtime, "_network", side_effect=self.network), \
                 mock.patch.object(runtime, "_run", return_value=(outcome, [])) as run, \
                 mock.patch.object(runtime, "_policy") as policy, \
                 mock.patch.object(runtime, "image_id") as image_check:
                result = runtime.subject(command, workspace, workspace / "last.txt", "prompt", 900,
                                         workspace, IMAGE, "3.11.5", seal)
        self.assertIs(result, outcome)
        policy.assert_not_called()
        image_check.assert_not_called()
        self.assertEqual(run.call_count, 1)

    def test_subject_preserves_legacy_policy_revalidation(self):
        identity = self.identity()
        seal = {"runtime_security_sha256": runtime.security_sha256(IMAGE, "3.11.5"),
                "policy_sha256": "2" * 64, "identity": identity,
                "web_search": runtime.WEB_SEARCH_DISABLED_EVIDENCE}
        policy_row = {"source_sha256": "2" * 64, "identity": identity,
                      "web_search": runtime.WEB_SEARCH_DISABLED_EVIDENCE}
        outcome = runtime.ProcessOutcome(0, "", "", False, False)
        with tempfile.TemporaryDirectory() as temporary:
            workspace = Path(temporary)
            command = ["codex", "--config", runtime.WEB_SEARCH_DISABLED_CONFIG,
                       "--cd", str(workspace), "--output-last-message", str(workspace / "final")]
            with mock.patch.object(runtime, "_network", side_effect=self.network), \
                 mock.patch.object(runtime, "_run", return_value=(outcome, [])), \
                 mock.patch.object(runtime, "_policy", return_value=policy_row) as policy, \
                 mock.patch.object(runtime, "image_id", return_value=IMAGE) as image_check:
                runtime.subject(command, workspace, workspace / "last.txt", "prompt", 900,
                                workspace, IMAGE, "3.11.5", seal)
        policy.assert_called_once()
        image_check.assert_called_once_with(IMAGE)


if __name__ == "__main__":
    unittest.main()
