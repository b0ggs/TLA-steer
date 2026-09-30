from __future__ import annotations

import ast
import contextlib
import hashlib
import io
import json
import shutil
import subprocess
import sys
import tempfile
import threading
import unittest
from pathlib import Path
from unittest import mock

from mdseval.capture import Redactor
from mdseval.processutils import ProcessOutcome
from tla_steer import cli, pipeline
from tla_steer.contract import CONTROLLER_SCHEMA_VERSION, PROPOSAL_SCHEMA_VERSION
from tla_steer.evidence import write_run_report
from tla_steer.oracle import ACTION_SYMBOLS, INITIAL, iter_type_correct_states, oracle_successor
from tla_steer.verifier import verify_candidate
from tla_steer.worker import (
    PROTOTYPE_LOCAL,
    PROTOTYPE_LOCAL_WARNING,
    ROLE_POLICIES,
    WorkerRequest,
    run_worker,
)


_CODE_MODE_DISABLED_WARNING = (
    "Code Mode is unavailable because code-mode host is disabled. Code mode "
    "will fail closed; enable `features.code_mode_host` and install "
    "`codex-code-mode-host`."
)


def _events(
    *,
    model: str = "gpt-returned",
    secret: str | None = None,
    code_mode_warning: str | None = None,
) -> str:
    rows: list[dict[str, object]] = [
        {"type": "thread.started", "model": model},
    ]
    if code_mode_warning is not None:
        rows.append(
            {
                "type": "item.completed",
                "item": {
                    "id": "item_0",
                    "type": "error",
                    "message": code_mode_warning,
                },
            }
        )
    rows.append({"type": "turn.started"})
    if secret is not None:
        rows.append(
            {
                "type": "item.completed",
                "item": {
                    "id": "item-1",
                    "type": "agent_message",
                    "text": f"message {secret}",
                },
            }
        )
    rows.append(
        {
            "type": "turn.completed",
            "usage": {
                "input_tokens": 101,
                "cached_input_tokens": 41,
                "cache_write_input_tokens": 7,
                "output_tokens": 23,
                "reasoning_output_tokens": 11,
            },
        }
    )
    return "".join(json.dumps(row) + "\n" for row in rows)


def _fake_git_init(workspace: Path) -> None:
    (workspace / ".git").mkdir()


class WorkerFakeTests(unittest.TestCase):
    def _request(
        self,
        root: Path,
        *,
        role: str = "direct",
        call_id: str = "call-1",
        output_schema: dict[str, object] | None = None,
    ) -> WorkerRequest:
        return WorkerRequest(
            call_id=call_id,
            role=role,
            prompt="Create the requested artifact.",
            input_files={"TwoLights.tla": "---- MODULE TwoLights ----\n"},
            artifact_path="candidate.py",
            spool_dir=root / call_id,
            codex_home=root / "oauth-home",
            timeout_seconds=17,
            output_schema=output_schema,
        )

    def test_each_role_uses_locked_model_effort_and_capability_shutdown(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            observed_workspaces: list[Path] = []

            for role in ("direct", "planner", "follower"):
                captured: dict[str, object] = {}

                def fake_process(command, **kwargs):
                    captured["command"] = list(command)
                    captured.update(kwargs)
                    workspace = kwargs["cwd"]
                    observed_workspaces.append(workspace)
                    self.assertTrue((workspace / "TwoLights.tla").is_file())
                    self.assertTrue((workspace / ".git").is_dir())
                    (workspace / "candidate.py").write_text(
                        f"ROLE = {role!r}\n", encoding="utf-8"
                    )
                    final_index = command.index("--output-last-message") + 1
                    Path(command[final_index]).write_text("done\n", encoding="utf-8")
                    return ProcessOutcome(0, _events(), "", False, False)

                request = self._request(root, role=role, call_id=f"call-{role}")
                with mock.patch("tla_steer.worker.init_repository", _fake_git_init):
                    result = run_worker(request, process_runner=fake_process)

                command = captured["command"]
                assert isinstance(command, list)
                joined = " ".join(command)
                policy = ROLE_POLICIES[role]
                self.assertEqual(result.requested_model, policy.model)
                self.assertEqual(result.reasoning_effort, policy.reasoning_effort)
                self.assertEqual(command[command.index("--model") + 1], policy.model)
                self.assertIn(
                    f'model_reasoning_effort="{policy.reasoning_effort}"', command
                )
                for flag in (
                    "--strict-config",
                    "--ephemeral",
                    "--json",
                    "--ignore-user-config",
                    "--ignore-rules",
                ):
                    self.assertIn(flag, command)
                self.assertIn("--ask-for-approval never", joined)
                for setting in (
                    'web_search="disabled"',
                    "agents.enabled=false",
                    "features.multi_agent=false",
                    "features.apps=false",
                    "features.enable_mcp_apps=false",
                    "features.plugins=false",
                    "sandbox_workspace_write.network_access=false",
                ):
                    self.assertIn(setting, command)
                environment = captured["environment"]
                assert isinstance(environment, dict)
                self.assertEqual(environment["CODEX_HOME"], str(request.codex_home))
                self.assertEqual(result.status, "COMPLETED")
                self.assertEqual(result.containment_mode, PROTOTYPE_LOCAL)
                self.assertEqual(result.containment_warning, PROTOTYPE_LOCAL_WARNING)

            self.assertTrue(observed_workspaces)
            self.assertTrue(all(not workspace.exists() for workspace in observed_workspaces))

    def test_structured_schema_usage_redaction_and_artifact_are_persisted(self) -> None:
        secret = "CANARY-SECRET"
        schema = {
            "type": "object",
            "properties": {"answer": {"type": "string"}},
            "required": ["answer"],
            "additionalProperties": False,
        }
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            captured: dict[str, object] = {}

            def fake_process(command, **kwargs):
                captured["command"] = list(command)
                workspace = kwargs["cwd"]
                (workspace / "candidate.py").write_text(
                    "VALUE = 42\n", encoding="utf-8"
                )
                schema_path = Path(command[command.index("--output-schema") + 1])
                self.assertTrue(schema_path.is_relative_to(workspace))
                self.assertEqual(json.loads(schema_path.read_text()), schema)
                Path(command[command.index("--output-last-message") + 1]).write_text(
                    json.dumps({"answer": f"safe {secret}"}), encoding="utf-8"
                )
                return ProcessOutcome(
                    0,
                    _events(model="gpt-5.6-luna", secret=secret),
                    f"stderr {secret}",
                    False,
                    False,
                )

            request = self._request(
                root, role="follower", call_id="structured", output_schema=schema
            )
            with mock.patch("tla_steer.worker.init_repository", _fake_git_init):
                result = run_worker(
                    request,
                    process_runner=fake_process,
                    redactor=Redactor([secret]),
                )

            command = captured["command"]
            assert isinstance(command, list)
            self.assertLess(command.index("--output-schema"), len(command) - 1)
            self.assertEqual(command[-1], "-")
            self.assertEqual(result.status, "COMPLETED")
            self.assertEqual(result.returned_model, "gpt-5.6-luna")
            self.assertEqual(
                result.usage,
                {
                    "input_tokens": 101,
                    "cached_input_tokens": 41,
                    "cache_write_input_tokens": 7,
                    "output_tokens": 23,
                    "reasoning_output_tokens": 11,
                    "usage_reported": True,
                },
            )
            artifact = request.spool_dir / "candidate.py"
            artifact_bytes = artifact.read_bytes()
            self.assertEqual(artifact_bytes, b"VALUE = 42\n")
            self.assertEqual(result.artifact_path, "candidate.py")
            self.assertEqual(
                result.artifact_sha256, hashlib.sha256(artifact_bytes).hexdigest()
            )
            for name in ("events.jsonl", "stderr.txt", "final.txt"):
                text = (request.spool_dir / name).read_text(encoding="utf-8")
                self.assertNotIn(secret, text)
                self.assertIn("[REDACTED]", text)

            result_json = json.loads(
                (request.spool_dir / "result.json").read_text(encoding="utf-8")
            )
            for field in (
                "call_id",
                "role",
                "requested_model",
                "returned_model",
                "reasoning_effort",
                "status",
                "exit_code",
                "duration_seconds",
                "queue_duration_seconds",
                "usage",
                "error",
            ):
                self.assertIn(field, result_json)
            self.assertEqual(result_json["usage"], result.usage)
            intent = json.loads(
                (request.spool_dir / "intent.json").read_text(encoding="utf-8")
            )
            self.assertEqual(intent["output_schema"]["value"], schema)
            self.assertEqual(intent["containment_mode"], PROTOTYPE_LOCAL)

    def test_timeout_is_preserved_as_data_with_zero_complete_usage(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)

            def fake_timeout(_command, **_kwargs):
                return ProcessOutcome(None, "", "timed out", True, False)

            request = self._request(root, call_id="timeout")
            ticks = iter((10.0, 12.5))
            with mock.patch("tla_steer.worker.init_repository", _fake_git_init):
                result = run_worker(
                    request,
                    process_runner=fake_timeout,
                    monotonic=lambda: next(ticks),
                )

            self.assertEqual(result.status, "TIMEOUT")
            self.assertEqual(result.duration_seconds, 2.5)
            self.assertEqual(result.exit_code, None)
            self.assertFalse(result.usage["usage_reported"])
            self.assertEqual(result.usage["cache_write_input_tokens"], 0)
            self.assertIsNone(result.artifact_path)
            persisted = json.loads(
                (request.spool_dir / "result.json").read_text(encoding="utf-8")
            )
            self.assertEqual(persisted["status"], "TIMEOUT")
            self.assertIn("empty_event_stream", persisted["event_fatal_defects"])

    def test_only_exact_fail_closed_code_mode_warning_is_compatible(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)

            def run_with(events: str, call_id: str):
                request = self._request(root, call_id=call_id)

                def fake_process(command, **kwargs):
                    (kwargs["cwd"] / "candidate.py").write_text(
                        "VALUE = 1\n", encoding="utf-8"
                    )
                    Path(command[command.index("--output-last-message") + 1]).write_text(
                        "READY\n", encoding="utf-8"
                    )
                    return ProcessOutcome(0, events, "", False, False)

                with mock.patch("tla_steer.worker.init_repository", _fake_git_init):
                    return request, run_worker(request, process_runner=fake_process)

            accepted_request, accepted = run_with(
                _events(code_mode_warning=_CODE_MODE_DISABLED_WARNING),
                "accepted-warning",
            )
            self.assertEqual(accepted.status, "COMPLETED")
            self.assertEqual(accepted.event_fatal_defects, ())
            preserved = (accepted_request.spool_dir / "events.jsonl").read_text(
                encoding="utf-8"
            )
            self.assertIn(_CODE_MODE_DISABLED_WARNING, preserved)

            _, rejected = run_with(
                _events(code_mode_warning="some other error"), "rejected-error"
            )
            self.assertEqual(rejected.status, "INVALID_EVIDENCE")
            self.assertIn(
                'line:2:unknown_item_type:"error"', rejected.event_fatal_defects
            )

    def test_request_rejects_unsafe_paths_modes_and_schema(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            common = {
                "call_id": "safe",
                "role": "direct",
                "prompt": "work",
                "input_files": {},
                "artifact_path": "candidate.py",
                "spool_dir": root / "spool",
                "codex_home": root / "home",
            }
            with self.assertRaisesRegex(ValueError, "fresh workspace"):
                WorkerRequest(**{**common, "input_files": {"../secret": "x"}})
            with self.assertRaisesRegex(ValueError, "prototype_local"):
                WorkerRequest(**{**common, "containment_mode": "mdseval_sealed"})
            with self.assertRaisesRegex(ValueError, "finite JSON"):
                WorkerRequest(**{**common, "output_schema": {"x": float("nan")}})
            with self.assertRaisesRegex(ValueError, "collides"):
                WorkerRequest(**{**common, "artifact_path": "result.json"})


ROOT = Path(__file__).resolve().parents[1]


class OfflineModels:
    """Only the hosted process is fake; capture, scoring and grading stay real."""

    def __init__(self, *, resample=False, invalid_planners=0, collapse=False,
                 direct_timeout=False, direct_model_mismatch=False,
                 invalid_follower_step=None, after_snapshot=None):
        self.resample = resample
        self.invalid_planners = invalid_planners
        self.collapse = collapse
        self.direct_timeout = direct_timeout
        self.direct_model_mismatch = direct_model_mismatch
        self.invalid_follower_step = invalid_follower_step
        self.after_snapshot = after_snapshot
        self.requests = []
        self.lock = threading.Lock()
        self.golden = (ROOT / "tests/fixtures/candidates/golden.py").read_text()
        error_source = (ROOT / "tests/fixtures/candidates/frame_copy_error.py").read_text()
        self.error_fragment = next(ast.get_source_segment(error_source, node) for node in ast.parse(error_source).body
                                   if isinstance(node, ast.FunctionDef) and node.name == "b_green_to_yellow")
        self.fragments = {}
        for node in ast.parse(self.golden).body:
            if isinstance(node, ast.FunctionDef):
                self.fragments[node.name] = ast.get_source_segment(self.golden, node)
        steps = [{
            "id": "initial", "kind": "initial", "target": "INITIAL",
            "python_symbol": "INITIAL", "proposal_instruction": "Return INITIAL.",
            "expected_initial": dict(INITIAL),
        }]
        states = list(iter_type_correct_states())
        for label, symbol in ACTION_SYMBOLS.items():
            enabled = next(state for state in states if oracle_successor(label, state) is not None)
            disabled = next(state for state in states if oracle_successor(label, state) is None)
            steps.append({
                "id": symbol, "kind": "action", "target": label,
                "python_symbol": symbol, "proposal_instruction": f"Return {symbol}.",
                "probes": [
                    {"state": enabled, "expected_successor": oracle_successor(label, enabled)},
                    {"state": disabled, "expected_successor": None},
                ],
            })
        self.controller = {"schema_version": CONTROLLER_SCHEMA_VERSION, "steps": steps}

    def __call__(self, request):
        with self.lock:
            self.requests.append(request)
            planner_attempt = sum(item.role == "planner" for item in self.requests)

        def process(command, **kwargs):
            if request.role == "direct":
                if self.after_snapshot is not None:
                    self.after_snapshot()
                if self.direct_timeout:
                    return ProcessOutcome(None, "", "injected timeout", True, False)
                document = self.golden
            elif request.role == "planner":
                document = "{}" if planner_attempt <= self.invalid_planners else json.dumps(self.controller)
            else:
                step = json.loads(request.input_files["controller-step.json"])
                symbol = step["python_symbol"]
                particle_id = request.call_id[-8:]
                if symbol == "INITIAL":
                    wrong = self.collapse or (self.resample and particle_id != "p00-0000")
                    value = ({"clock": 1, "lightA": "red", "timerA": 1,
                              "lightB": "green", "timerB": 3} if wrong else INITIAL)
                    fragment = "INITIAL = " + repr(value)
                else:
                    fragment = self.fragments[symbol]
                    if self.resample and symbol == "b_green_to_yellow" and int(particle_id[-4:]) < 4:
                        # Pinned reviewed frame-copy error gives q=.5.
                        fragment = self.error_fragment
                document = json.dumps({
                    "schema_version": PROPOSAL_SCHEMA_VERSION,
                    "step_id": step["id"], "python_fragment": fragment,
                })
                if step["id"] == self.invalid_follower_step:
                    document = "not JSON"
            Path(command[command.index("--output-last-message") + 1]).write_text(document)
            model = ROLE_POLICIES[request.role].model
            if request.role == "direct" and self.direct_model_mismatch:
                model = "unexpected-returned-model"
            return ProcessOutcome(0, _events(model=model), "", False, False)

        ticks = iter((10.0, 10.25))
        return run_worker(request, process_runner=process, monotonic=lambda: next(ticks))


class PipelineOfflineTests(unittest.TestCase):
    """Regression coverage for the frozen two-arm coordinator and offline report."""

    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name) / "repository"
        for name in ("configs", "prompts", "schemas"):
            shutil.copytree(ROOT / name, self.root / name)
        for name in ("TwoLights.tla", "TwoLights.cfg"):
            shutil.copyfile(ROOT / name, self.root / name)
        self.config_path = self.root / "configs/prototype.json"
        self.config = json.loads(self.config_path.read_text())
        self.home = Path(self.temporary.name) / "empty-fake-oauth-profile"
        self.home.mkdir()

    def run_offline(self, models, *, smoke=True, verifier=None):
        with mock.patch("tla_steer.execution.preflight", return_value={"test_fixture_only": True}), \
             mock.patch("tla_steer.pipeline._codex_home", return_value=(self.home, "offline-test")), \
             mock.patch("tla_steer.pipeline.run_worker", side_effect=models), \
             mock.patch("tla_steer.pipeline.verify_candidate", side_effect=verifier or verify_candidate):
            return pipeline.run_comparison(
                config=self.config, config_path=self.config_path, repository_root=self.root,
                particle_count=2 if smoke else 8, max_concurrency=2 if smoke else 4,
                smoke=smoke,
            )

    def test_full_comparison_freezes_both_artifacts_before_grading_and_reconciles_usage(self):
        models = OfflineModels(resample=True)
        frozen = {}
        verified = []

        def observe_verification(candidate):
            run_dir = candidate.parents[1]
            manifest = json.loads((run_dir / "manifest.json").read_text())
            self.assertTrue(manifest["selection_complete"])
            for arm, filename in (("direct", "candidate.py"), ("discipl", "selected-candidate.py")):
                content = (run_dir / arm / filename).read_bytes()
                digest = hashlib.sha256(content).hexdigest()
                self.assertEqual(manifest[f"official_{arm}_candidate_sha256"], digest)
                if arm in frozen:
                    self.assertEqual(frozen[arm], content)
                frozen[arm] = content
            selected = json.loads((run_dir / "discipl/particles.json").read_text())
            # After eight initial resampling draws, the ninth seeded draw is
            # 0.28439129548227504. Mass [.5,.5,.5,.5,1,1,1,1] selects 3;
            # uniform selection chooses 2, argmax chooses 4. The official
            # artifact is intentionally wrong despite exact alternatives.
            self.assertEqual(selected["official_particle_index"], 3)
            for actual, expected in zip(selected["selection_weights"], [1/12] * 4 + [1/6] * 4):
                self.assertAlmostEqual(actual, expected)
            self.assertIn(b"Copy/paste error", frozen["discipl"])
            self.assertFalse((run_dir / "direct/verification.json").exists() and not verified)
            verified.append(candidate)
            return verify_candidate(candidate)

        run_dir = self.run_offline(models, smoke=False, verifier=observe_verification)
        summary = json.loads((run_dir / "summary.json").read_text())
        self.assertEqual(len(verified), 2)
        self.assertEqual(summary["run_status"], "completed")
        self.assertEqual(summary["configuration"]["logical_particles"], 8)
        self.assertEqual(summary["configuration"]["max_active_follower_calls"], 4)
        self.assertLessEqual(summary["maximum_observed_concurrency"], 4)
        self.assertEqual(summary["totals"]["calls"], 66)
        self.assertEqual(summary["follower_call_count"], 64)
        self.assertEqual(summary["smc"]["completed_steps"], 8)
        self.assertEqual(summary["smc"]["resampling_events"], 1)
        self.assertEqual(summary["smc"]["minimum_ess"], 1.0)
        self.assertEqual(summary["containment_mode"], "prototype_local")
        self.assertEqual(summary["totals"]["usage"], {
            "input_tokens": 6666, "cached_input_tokens": 2706,
            "cache_write_input_tokens": 462, "output_tokens": 1518,
            "reasoning_output_tokens": 726, "usage_reported": True, "total_tokens": 8184,
        })
        # Fixed fake counters + frozen static rates, calculated independently:
        # 2 Sol calls at $0.0007234 and 64 Luna calls at $0.00004077.
        self.assertAlmostEqual(summary["totals"]["api_price_equivalent_usd"], 0.00405608, places=12)
        self.assertEqual(summary["arms"]["direct"]["verification"]["outcome"], "EXACT")
        self.assertEqual(summary["arms"]["discipl"]["verification"]["outcome"], "SEMANTIC_MISMATCH")
        for candidate in verified:
            self.assertEqual(candidate.read_bytes(), frozen[candidate.parent.name])
        for request in models.requests:
            for name in ("intent.json", "events.jsonl", "stderr.txt", "final.txt", "result.json", "context.json"):
                self.assertTrue((request.spool_dir / name).is_file(), (request.call_id, name))

    def test_smoke_report_reproduces_from_copied_evidence_without_models(self):
        models = OfflineModels()
        run_dir = self.run_offline(models)
        expected_json = (run_dir / "summary.json").read_bytes()
        expected_markdown = (run_dir / "summary.md").read_bytes()
        copy = Path(self.temporary.name) / "detached-evidence"
        shutil.copytree(run_dir, copy)
        (copy / "summary.json").unlink()
        (copy / "summary.md").unlink()
        with mock.patch("tla_steer.pipeline.run_worker", side_effect=AssertionError("report launched a model")), \
             mock.patch("subprocess.Popen", side_effect=AssertionError("report launched a process")), \
             contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(cli.main(["report", str(copy)]), 0)
        self.assertEqual((copy / "summary.json").read_bytes(), expected_json)
        self.assertEqual((copy / "summary.md").read_bytes(), expected_markdown)
        summary = json.loads(expected_json)
        self.assertEqual(summary["configuration"]["logical_particles"], 2)
        self.assertEqual(summary["configuration"]["max_active_follower_calls"], 2)
        self.assertEqual(summary["totals"]["calls"], 18)
        self.assertEqual(summary["follower_call_count"], 16)
        for arm in ("direct", "discipl"):
            self.assertEqual(summary["arms"][arm]["verification"]["outcome"], "EXACT")

    def test_planner_schema_failure_repairs_only_once_and_retains_both_attempts(self):
        models = OfflineModels(invalid_planners=1)
        run_dir = self.run_offline(models)
        summary = json.loads((run_dir / "summary.json").read_text())
        self.assertEqual(summary["planner_schema_repair_count"], 1)
        self.assertEqual(summary["arms"]["discipl"]["retries"], 1)
        self.assertEqual(summary["totals"]["calls"], 19)
        planner = [request for request in models.requests if request.role == "planner"]
        self.assertEqual(len(planner), 2)
        self.assertIn("invalid-controller.json", planner[1].input_files)
        self.assertEqual(planner[1].input_files["invalid-controller.json"], "{}")
        self.assertEqual(summary["arms"]["discipl"]["verification"]["outcome"], "EXACT")

    def test_exhausted_planner_repair_resolves_selection_and_still_grades_direct(self):
        models = OfflineModels(invalid_planners=2)

        def observe(candidate):
            manifest = json.loads((candidate.parents[1] / "manifest.json").read_text())
            self.assertTrue(manifest["selection_complete"])
            self.assertIsNone(manifest["official_discipl_candidate_sha256"])
            self.assertIsNotNone(manifest["official_direct_candidate_sha256"])
            self.assertEqual(sum(item.role == "planner" for item in models.requests), 2)
            return verify_candidate(candidate)

        run_dir = self.run_offline(models, verifier=observe)
        summary = json.loads((run_dir / "summary.json").read_text())
        self.assertEqual(summary["totals"]["calls"], 3)
        self.assertEqual(summary["run_status"], "completed_with_failures")
        self.assertEqual(summary["arms"]["direct"]["verification"]["outcome"], "EXACT")
        self.assertTrue(summary["arms"]["discipl"]["verification"]["details"]["verification_not_run"])
        self.assertIn("Planner controller remained invalid", (run_dir / "summary.md").read_text())

    def test_particle_collapse_is_preserved_without_follower_retries(self):
        models = OfflineModels(collapse=True)
        run_dir = self.run_offline(models)
        summary = json.loads((run_dir / "summary.json").read_text())
        self.assertEqual(summary["totals"]["calls"], 4)
        self.assertEqual(summary["follower_call_count"], 2)
        self.assertEqual(summary["arms"]["discipl"]["retries"], 0)
        self.assertTrue(summary["smc"]["particle_collapse"])
        self.assertEqual(summary["arms"]["direct"]["verification"]["outcome"], "EXACT")
        manifest = json.loads((run_dir / "manifest.json").read_text())
        self.assertTrue(manifest["selection_complete"])
        self.assertIsNone(manifest["official_discipl_candidate_sha256"])
        self.assertIn("particle_collapse", json.dumps(summary["errors"]))

    def test_direct_timeout_still_grades_selected_discipl_and_preserves_missing_usage(self):
        run_dir = self.run_offline(OfflineModels(direct_timeout=True))
        summary = json.loads((run_dir / "summary.json").read_text())
        self.assertEqual(summary["totals"]["calls"], 18)
        self.assertEqual(summary["arms"]["direct"]["timeouts"], 1)
        self.assertFalse(summary["totals"]["usage"]["usage_reported"])
        self.assertIsNone(summary["totals"]["usage"]["input_tokens"])
        self.assertEqual(summary["arms"]["discipl"]["verification"]["outcome"], "EXACT")
        manifest = json.loads((run_dir / "manifest.json").read_text())
        self.assertTrue(manifest["selection_complete"])
        self.assertIsNone(manifest["official_direct_candidate_sha256"])
        self.assertIsNotNone(manifest["official_discipl_candidate_sha256"])

    def test_pipeline_error_and_nonconformities_survive_offline_report(self):
        models = OfflineModels()
        with self.assertRaisesRegex(pipeline.PipelineError, "injected verifier failure"):
            self.run_offline(models, verifier=mock.Mock(side_effect=RuntimeError("injected verifier failure")))
        run_dir, = (self.root / "runs").iterdir()
        manifest = json.loads((run_dir / "manifest.json").read_text())
        self.assertTrue(manifest["selection_complete"])
        self.assertTrue((run_dir / "direct/candidate.py").is_file())
        self.assertTrue((run_dir / "discipl/selected-candidate.py").is_file())
        self.assertTrue((run_dir / "discipl/particles.json").is_file())
        self.assertFalse((run_dir / "direct/verification.json").exists())
        self.assertFalse((run_dir / "discipl/verification.json").exists())
        manifest["nonconformities"] = ["returned model mismatch"]
        (run_dir / "manifest.json").write_text(json.dumps(manifest))
        summary = write_run_report(run_dir)
        self.assertEqual(summary["run_status"], "pipeline_error")
        self.assertIn("injected verifier failure", json.dumps(summary["errors"]))
        self.assertIn("returned model mismatch", json.dumps(summary["errors"]))
        markdown = (run_dir / "summary.md").read_text()
        self.assertIn("pipeline_error", markdown)
        self.assertIn("injected verifier failure", markdown)

    def test_returned_model_mismatch_is_not_graded_and_is_visible_in_report(self):
        run_dir = self.run_offline(OfflineModels(direct_model_mismatch=True))
        summary = json.loads((run_dir / "summary.json").read_text())
        self.assertEqual(summary["run_status"], "completed_with_failures")
        self.assertTrue(summary["arms"]["direct"]["verification"]["details"]["verification_not_run"])
        self.assertFalse((run_dir / "direct/candidate.py").exists())
        self.assertEqual(summary["arms"]["discipl"]["verification"]["outcome"], "EXACT")
        self.assertIn("unexpected-returned-model", (run_dir / "summary.md").read_text())

    def test_invalid_follower_json_preserves_partial_trace_without_retries(self):
        models = OfflineModels(invalid_follower_step="tick")
        run_dir = self.run_offline(models)
        summary = json.loads((run_dir / "summary.json").read_text())
        self.assertEqual(summary["totals"]["calls"], 6)
        self.assertEqual(summary["follower_call_count"], 4)
        self.assertEqual(summary["arms"]["discipl"]["retries"], 0)
        trace = [json.loads(line) for line in (run_dir / "discipl/trace.jsonl").read_text().splitlines()]
        self.assertEqual([row["step_id"] for row in trace], ["initial", "tick"])
        self.assertTrue(all("not strict JSON" in error for error in trace[-1]["errors"]))
        self.assertTrue(trace[-1]["particle_collapse"])
        self.assertEqual(summary["arms"]["direct"]["verification"]["outcome"], "EXACT")

    def test_two_failed_arms_resolve_without_invoking_verifier(self):
        models = OfflineModels(direct_timeout=True, invalid_planners=2)
        verifier = mock.Mock(side_effect=AssertionError("there is no selected candidate to grade"))
        run_dir = self.run_offline(models, verifier=verifier)
        verifier.assert_not_called()
        manifest = json.loads((run_dir / "manifest.json").read_text())
        self.assertTrue(manifest["selection_complete"])
        self.assertIsNone(manifest["official_direct_candidate_sha256"])
        self.assertIsNone(manifest["official_discipl_candidate_sha256"])
        summary = json.loads((run_dir / "summary.json").read_text())
        self.assertEqual(summary["run_status"], "completed_with_failures")
        self.assertEqual(summary["totals"]["calls"], 3)
        for arm in ("direct", "discipl"):
            self.assertTrue(summary["arms"][arm]["verification"]["details"]["verification_not_run"])

    def test_live_command_keeps_frozen_rate_card_for_report_reproduction(self):
        def change_source_card():
            path = self.root / "configs/rate-card-2026-08-30.json"
            card = json.loads(path.read_text())
            card["models"]["gpt-5.6-sol"]["input"] = 999
            path.write_text(json.dumps(card))

        models = OfflineModels(after_snapshot=change_source_card)
        with mock.patch("tla_steer.execution.preflight", return_value={"test_fixture_only": True}), \
             mock.patch("tla_steer.pipeline._codex_home", return_value=(self.home, "offline-test")), \
             mock.patch("tla_steer.pipeline.run_worker", side_effect=models), \
             contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(cli.main(["smoke", "--config", str(self.config_path)]), 0)
        run_dir, = (self.root / "runs").iterdir()
        live = (run_dir / "summary.json").read_bytes()
        self.assertAlmostEqual(json.loads(live)["totals"]["api_price_equivalent_usd"], 0.00209912, places=12)
        write_run_report(run_dir)
        self.assertEqual((run_dir / "summary.json").read_bytes(), live)


if __name__ == "__main__":
    unittest.main()


class CostScreenTests(unittest.TestCase):
    """Six bounded risk checks; all executed candidate bytes are reviewed fixtures."""

    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name) / "repository"
        for name in ("configs", "prompts", "schemas", "tests/fixtures/candidates"):
            shutil.copytree(ROOT / name, self.root / name)
        for name in ("TwoLights.tla", "TwoLights.cfg"):
            shutil.copyfile(ROOT / name, self.root / name)
        self.config_path = self.root / "configs/prototype.json"
        self.config = json.loads(self.config_path.read_text())

    def screen(self):
        with mock.patch("tla_steer.pipeline._codex_home", side_effect=AssertionError("credential lookup")), \
             mock.patch("tla_steer.pipeline.run_worker", side_effect=AssertionError("live worker fallback")):
            return pipeline.run_comparison(self.config, self.config_path, self.root, 2, 2, True, offline_screen=True)

    def report(self, run_dir):
        with mock.patch("subprocess.Popen", side_effect=AssertionError("report spawned process")):
            return write_run_report(run_dir)

    def test_three_arms_same_direct_inputs_and_all_frozen_before_first_grade(self):
        observed = []
        snapshots = {}

        def grade(path):
            run_dir = path.parents[1]
            manifest = json.loads((run_dir / "manifest.json").read_text())
            self.assertTrue(manifest["selection_complete"])
            for arm, filename in (("direct", "candidate.py"), ("cheap_alone", "candidate.py"), ("discipl", "selected-candidate.py")):
                data = (run_dir / arm / filename).read_bytes()
                self.assertEqual(manifest[f"official_{arm}_candidate_sha256"], hashlib.sha256(data).hexdigest())
                if arm in snapshots:
                    self.assertEqual(snapshots[arm], data)
                snapshots[arm] = data
            selected = json.loads((run_dir / "discipl/particles.json").read_text())
            # No resampling at N=2. Literal first seeded draw .055206537...
            # selects less likely particle 0 with weights [1/3, 2/3].
            # Argmax/best-grade choose the exact particle 1 instead.
            self.assertEqual(selected["official_particle_index"], 0)
            self.assertAlmostEqual(selected["selection_weights"][0], 1/3)
            self.assertAlmostEqual(selected["selection_weights"][1], 2/3)
            self.assertIn(b"Copy/paste error", snapshots["discipl"])
            if not observed:
                self.assertFalse(any(run_dir.glob("*/verification.json")))
            observed.append(path.parent.name)
            return verify_candidate(path)

        with mock.patch("tla_steer.pipeline.verify_candidate", side_effect=grade):
            run_dir = self.screen()
        self.assertEqual(observed, ["direct", "cheap_alone", "discipl"])
        summary = self.report(run_dir)
        self.assertEqual(summary["totals"]["attempted_calls"], 19)
        self.assertEqual(summary["totals"]["calls"], 19)
        self.assertTrue(summary["accounting"]["complete"])
        self.assertEqual(summary["accounting"]["attempted_by_role"], {"direct": 1, "cheap_alone": 1, "planner": 1, "follower": 16})
        self.assertEqual(summary["totals"]["usage"]["input_tokens"], 1919)
        self.assertEqual(summary["totals"]["usage"]["output_tokens"], 437)
        self.assertAlmostEqual(summary["totals"]["api_price_equivalent_usd"], .00213989, places=12)
        self.assertAlmostEqual(summary["arms"]["cheap_alone"]["api_price_equivalent"]["total_usd"], .00004077, places=12)
        self.assertEqual(summary["arms"]["discipl"]["verification"]["outcome"], "SEMANTIC_MISMATCH")
        self.assertEqual(summary["arms"]["direct"]["verification"]["outcome"], "EXACT")
        self.assertEqual(summary["arms"]["cheap_alone"]["verification"]["outcome"], "EXACT")
        intents = []
        for arm in ("direct", "cheap_alone"):
            intents.append(json.loads((run_dir / arm / "calls" / f"{arm}-0001/intent.json").read_text()))
        for field in ("prompt", "prompt_sha256", "input_files", "artifact_path", "output_schema", "timeout_seconds", "containment_mode"):
            self.assertEqual(intents[0][field], intents[1][field], field)
        self.assertNotEqual(intents[0]["requested_model"], intents[1]["requested_model"])
        self.assertEqual(intents[1]["reasoning_effort"], "low")
        self.assertFalse((run_dir / "cheap_alone/planner").exists())
        self.assertEqual((run_dir / "inputs/TwoLights.tla").read_bytes(), (ROOT / "TwoLights.tla").read_bytes())
        self.assertIn("synthetic token counters only", (run_dir / "summary.md").read_text())
        self.assertLessEqual(summary["maximum_observed_concurrency"], 2)

    def test_source_hash_mismatch_blocks_before_worker_or_credentials(self):
        for name in ("TwoLights.tla", "TwoLights.cfg"):
            with self.subTest(name=name):
                path = self.root / name
                original = path.read_bytes()
                path.write_bytes(original + b"\n")
                with mock.patch("tla_steer.pipeline.ReviewedFixtureWorker") as fixture, \
                     mock.patch("tla_steer.pipeline._codex_home") as credentials:
                    with self.assertRaisesRegex(pipeline.PipelineError, "hash mismatch"):
                        self.screen()
                    fixture.assert_not_called()
                    credentials.assert_not_called()
                path.write_bytes(original)
        self.config["input"]["sha256"]["TwoLights.tla"] = "0" * 64
        with self.assertRaisesRegex(pipeline.PipelineError, "source pins"):
            self.screen()
        self.assertFalse((self.root / "runs").exists())

    def test_failed_call_is_counted_and_missing_usage_is_unknown(self):
        from tla_steer.worker import ReviewedFixtureWorker
        actual = ReviewedFixtureWorker.__call__

        def timeout(worker, request):
            if request.role == "cheap_alone":
                return run_worker(request, process_runner=lambda *_args, **_kwargs: ProcessOutcome(None, "", "fixture timeout", True, False))
            return actual(worker, request)

        with mock.patch.object(ReviewedFixtureWorker, "__call__", timeout):
            run_dir = self.screen()
        summary = self.report(run_dir)
        self.assertEqual(summary["totals"]["attempted_calls"], 19)
        cheap = summary["arms"]["cheap_alone"]
        self.assertEqual(cheap["failed_calls"], 1)
        self.assertEqual(cheap["timeouts"], 1)
        self.assertIsNone(cheap["usage"]["input_tokens"])
        self.assertIsNone(cheap["api_price_equivalent"]["total_usd"])
        self.assertIsNone(summary["totals"]["api_price_equivalent_usd"])
        self.assertFalse(summary["accounting"]["complete"])
        manifest = json.loads((run_dir / "manifest.json").read_text())
        self.assertTrue(manifest["selection_complete"])
        self.assertIsNone(manifest["official_cheap_alone_candidate_sha256"])
        self.assertEqual(summary["arms"]["direct"]["verification"]["outcome"], "EXACT")
        self.assertIn("UNKNOWN", (run_dir / "summary.md").read_text())

    def test_setup_exception_before_intent_reconciles_coordinator_count(self):
        from tla_steer.worker import ReviewedFixtureWorker
        with mock.patch.object(ReviewedFixtureWorker, "__call__", side_effect=OSError("injected setup failure")):
            with self.assertRaisesRegex(pipeline.PipelineError, "injected setup failure"):
                self.screen()
        run_dir, = (self.root / "runs/offline-cost-screen-r2").iterdir()
        summary = self.report(run_dir)
        self.assertEqual(summary["totals"]["attempted_calls"], 1)
        self.assertEqual(summary["totals"]["calls"], 0)
        self.assertFalse(summary["accounting"]["complete"])
        self.assertIsNone(summary["totals"]["api_price_equivalent_usd"])
        self.assertIn("coordinator attempted 1, observed 0", json.dumps(summary["errors"]))

    def test_missing_duplicate_and_invalid_evidence_never_becomes_free(self):
        original = self.screen()
        scenarios = ("missing_result", "missing_intent", "missing_both", "duplicate", "bad_json", "duplicate_json_key", "wrong_id", "wrong_role", "invalid_usage", "missing_usage", "invalid_counter")
        for index, scenario in enumerate(scenarios):
            with self.subTest(scenario=scenario):
                run_dir = Path(self.temporary.name) / f"damaged-{index}"
                shutil.copytree(original, run_dir)
                spool = run_dir / "cheap_alone/calls/cheap_alone-0001"
                result_path = spool / "result.json"
                result = json.loads(result_path.read_text())
                if scenario == "missing_result":
                    result_path.unlink()
                elif scenario == "missing_intent":
                    (spool / "intent.json").unlink()
                elif scenario == "missing_both":
                    shutil.rmtree(spool)
                elif scenario == "duplicate":
                    shutil.copytree(spool, spool.parent / "duplicate")
                elif scenario == "bad_json":
                    result_path.write_text("{")
                elif scenario == "duplicate_json_key":
                    result_path.write_text(result_path.read_text().replace('"usage": {', '"status": "COMPLETED", "usage": {'))
                elif scenario == "invalid_counter":
                    path = run_dir / "manifest.json"
                    manifest = json.loads(path.read_text())
                    manifest["attempted_calls_by_role"]["cheap_alone"] = True
                    path.write_text(json.dumps(manifest))
                else:
                    if scenario == "wrong_id":
                        result["call_id"] = "direct-0001"
                    elif scenario == "wrong_role":
                        result["role"] = "direct"
                    elif scenario == "invalid_usage":
                        result["usage"]["input_tokens"] = -1
                    elif scenario == "missing_usage":
                        result.pop("usage")
                    result_path.write_text(json.dumps(result))
                summary = self.report(run_dir)
                self.assertFalse(summary["accounting"]["complete"])
                self.assertIsNone(summary["totals"]["api_price_equivalent_usd"])
                self.assertIsNone(summary["arms"]["cheap_alone"]["api_price_equivalent"]["total_usd"])
                self.assertIsNone(summary["totals"]["usage"]["input_tokens"])
                self.assertTrue(summary["errors"])

    def test_usage_validation_rejects_partial_bool_nonfinite_and_overlap(self):
        from tla_steer.evidence import normalize_usage, price_equivalent, load_rate_card
        valid = {"input_tokens": 101, "cached_input_tokens": 41, "cache_write_input_tokens": 7, "output_tokens": 23, "reasoning_output_tokens": 11, "usage_reported": True}
        invalid = [{}, {**valid, "input_tokens": True}, {**valid, "output_tokens": float("nan")}, {**valid, "cached_input_tokens": 102}, {**valid, "reasoning_output_tokens": 24}, {**valid, "usage_reported": "yes"}]
        partial = dict(valid)
        partial.pop("cache_write_input_tokens")
        invalid.append(partial)
        card = load_rate_card(ROOT / "configs/rate-card-2026-08-30.json")
        for value in invalid:
            with self.subTest(value=value):
                usage = normalize_usage(value)
                self.assertFalse(usage["usage_reported"])
                self.assertIsNone(usage["input_tokens"])
                price = price_equivalent(value, "gpt-5.6-luna", card)
                self.assertFalse(price["priced"])
                self.assertIsNone(price["total_usd"])

    def test_frozen_rate_card_replay_is_byte_identical_and_tampering_rejected(self):
        from tla_steer.evidence import EvidenceError
        run_dir = self.screen()
        expected_json = (run_dir / "summary.json").read_bytes()
        expected_md = (run_dir / "summary.md").read_bytes()
        (self.root / "configs/rate-card-2026-08-30.json").write_text("{}")
        self.report(run_dir)
        self.assertEqual((run_dir / "summary.json").read_bytes(), expected_json)
        self.assertEqual((run_dir / "summary.md").read_bytes(), expected_md)
        card = run_dir / "rate-card.json"
        value = json.loads(card.read_text())
        value["models"]["gpt-5.6-luna"]["input"] = 0
        card.write_text(json.dumps(value))
        with self.assertRaisesRegex(EvidenceError, "frozen run snapshot"):
            self.report(run_dir)

    def test_cli_never_uses_live_runner_and_rejects_unreviewed_fixture(self):
        # Guard the actual subprocess boundary too: a default argument could
        # retain a live process runner despite patching its module attribute.
        original_popen = subprocess.Popen
        launched = []
        def guarded_popen(command, *args, **kwargs):
            executable = str(command[0])
            self.assertIn(executable, {"git", "/usr/bin/prlimit"})
            if executable == "/usr/bin/prlimit":
                boundary = command.index("--")
                self.assertEqual(command[boundary+1:boundary+4], [sys.executable, "-I", "-S"])
            launched.append(executable)
            return original_popen(command, *args, **kwargs)

        with mock.patch("tla_steer.pipeline._codex_home", side_effect=AssertionError("credential lookup")), \
             mock.patch("subprocess.Popen", side_effect=guarded_popen), \
             mock.patch("tla_steer.pipeline.run_worker", side_effect=AssertionError("live worker")), \
             contextlib.redirect_stdout(io.StringIO()) as output:
            self.assertEqual(cli.main(["offline-screen", "--config", str(self.config_path)]), 0)
        self.assertIn("synthetic token counters only", output.getvalue())
        self.assertIn("git", launched)
        self.assertIn("/usr/bin/prlimit", launched)
        path = self.root / "tests/fixtures/candidates/golden.py"
        path.write_text(path.read_text() + "\nraise RuntimeError('unreviewed')\n")
        with mock.patch("tla_steer.worker.run_worker") as worker, \
             mock.patch("tla_steer.pipeline.verify_candidate") as verifier, \
             contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(cli.main(["offline-screen", "--config", str(self.config_path)]), 3)
            worker.assert_not_called()
            verifier.assert_not_called()

    def test_unreviewed_fragment_is_rejected_before_probe_execution(self):
        from tla_steer.worker import ReviewedFixtureWorker

        # Validate the real pipeline's pre-probe boundary by corrupting the
        # worker output, rather than substituting the scorer.
        original_call = ReviewedFixtureWorker.__call__
        def corrupt(worker, request):
            result = original_call(worker, request)
            if request.role == "follower" and "-tick-" in request.call_id:
                path = request.spool_dir / "final.txt"
                value = json.loads(path.read_text())
                value["python_fragment"] = "def tick(state):\n    return None"
                path.write_text(json.dumps(value))
            return result
        with mock.patch.object(ReviewedFixtureWorker, "__call__", corrupt), \
             mock.patch("tla_steer.pipeline._score_action", side_effect=AssertionError("unreviewed code executed")) as execute:
            run_dir = self.screen()
            execute.assert_not_called()
        summary = self.report(run_dir)
        self.assertTrue(summary["smc"]["particle_collapse"])
        self.assertEqual(summary["arms"]["discipl"]["verification"]["outcome"], "INVALID_CANDIDATE")

    def test_failed_call_with_complete_usage_is_included_in_cost(self):
        from tla_steer.worker import ReviewedFixtureWorker
        actual = ReviewedFixtureWorker.__call__
        def failed(worker, request):
            if request.role == "cheap_alone":
                return run_worker(request, process_runner=lambda *_args, **_kwargs: ProcessOutcome(1, _events(model="gpt-5.6-luna"), "fixture failure", False, False))
            return actual(worker, request)
        with mock.patch.object(ReviewedFixtureWorker, "__call__", failed):
            run_dir = self.screen()
        summary = self.report(run_dir)
        self.assertTrue(summary["accounting"]["complete"])
        self.assertEqual(summary["arms"]["cheap_alone"]["failed_calls"], 1)
        self.assertAlmostEqual(summary["arms"]["cheap_alone"]["api_price_equivalent"]["total_usd"], .00004077, places=12)
        self.assertAlmostEqual(summary["totals"]["api_price_equivalent_usd"], .00213989, places=12)

    def test_unreviewed_direct_bytes_never_reach_final_verifier(self):
        from tla_steer.worker import ReviewedFixtureWorker
        actual = ReviewedFixtureWorker.__call__
        def corrupt(worker, request):
            result = actual(worker, request)
            if request.role == "direct":
                (request.spool_dir / "final.txt").write_text("raise RuntimeError('unreviewed')\n")
            return result
        with mock.patch.object(ReviewedFixtureWorker, "__call__", corrupt), \
             mock.patch("tla_steer.pipeline.verify_candidate") as grade:
            with self.assertRaisesRegex(pipeline.PipelineError, "unreviewed direct candidate"):
                self.screen()
            grade.assert_not_called()
