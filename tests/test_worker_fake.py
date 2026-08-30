from __future__ import annotations

import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from mdseval.capture import Redactor
from mdseval.processutils import ProcessOutcome
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


if __name__ == "__main__":
    unittest.main()
