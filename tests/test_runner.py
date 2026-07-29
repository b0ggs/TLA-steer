from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from mdseval.runner.codex_cli import (
    CodexCLI,
    build_codex_command,
    doctor,
    isolated_environment,
)
from mdseval.capture import Redactor
from mdseval.execution import evaluator_identity
from mdseval.fixtures import prepare_fixture
from mdseval.hashing import sha256_file
from mdseval.processutils import ProcessOutcome

from tests.helpers import experiment


class RunnerTests(unittest.TestCase):
    def test_command_contains_all_locked_isolation_flags(self) -> None:
        config = experiment()
        command = build_codex_command(
            config.runner, Path("/tmp/subject"), Path("/tmp/final")
        )
        joined = " ".join(command)
        for value in (
            "--ephemeral",
            "--strict-config",
            "--json",
            "--sandbox workspace-write",
            "--ignore-user-config",
            "--ignore-rules",
            "--model gpt-5.6-sol",
            'model_reasoning_effort="high"',
            'project_doc_fallback_filenames=["CODER.md"]',
            "agents.enabled=false",
            "sandbox_workspace_write.network_access=false",
        ):
            self.assertIn(value, joined)
        self.assertNotIn("--dangerously-bypass-approvals-and-sandbox", joined)
        self.assertNotIn("--skip-git-repo-check", joined)

    def test_minimal_environment_drops_credentials(self) -> None:
        with mock.patch.dict(
            os.environ,
            {"PATH": "/bin", "AWS_SECRET_ACCESS_KEY": "canary", "HOME": "/private"},
            clear=True,
        ):
            environment = isolated_environment("/isolated")
        self.assertEqual(environment["CODEX_HOME"], "/isolated")
        self.assertNotIn("AWS_SECRET_ACCESS_KEY", environment)
        self.assertNotIn("HOME", environment)

    def test_doctor_default_never_invokes_model(self) -> None:
        config = experiment()

        def result_for(command, **_kwargs):
            if "archive" in command:
                return mock.Mock(
                    returncode=1,
                    stdout="",
                    stderr="Error: failed to connect to remote app server",
                )
            return mock.Mock(
                returncode=0,
                stdout=(
                    "--strict-config --ephemeral --json --sandbox --ignore-user-config "
                    "--ignore-rules --model --config --cd --output-last-message "
                    "--ask-for-approval"
                ),
                stderr="",
            )

        with tempfile.TemporaryDirectory() as temporary:
            with mock.patch.dict(
                os.environ, {"MDSEVAL_CODEX_HOME": temporary}, clear=False
            ), mock.patch(
                "mdseval.runner.codex_cli.shutil.which",
                side_effect=lambda name: f"/usr/bin/{name}",
            ), mock.patch(
                "mdseval.runner.codex_cli.subprocess.run", side_effect=result_for
            ) as run:
                result = doctor(config)
        self.assertTrue(result.available)
        self.assertEqual(result.code, "LIVE_RUNNER_AVAILABLE")
        calls = list(run.call_args_list)
        commands = [call.args[0] for call in calls]
        probes = [
            call
            for call in calls
            if "exec" in call.args[0] and "--help" not in call.args[0]
        ]
        self.assertEqual(probes, [])
        self.assertTrue(
            all("exec" not in command or "--help" in command for command in commands)
        )
        archives = [command for command in commands if "archive" in command]
        self.assertEqual(len(archives), 3)
        self.assertTrue(all("--remote" in command for command in archives))
        self.assertTrue(
            all(
                command[command.index("--remote") + 1].startswith("unix://")
                and command[command.index("--remote") + 1].endswith("/absent.sock")
                for command in archives
            )
        )
        self.assertTrue(
            all(command[-1] == "ffffffff-ffff-ffff-ffff-ffffffffffff" for command in archives)
        )
        self.assertEqual(
            result.checks["config_compatibility_status"],
            "VERIFIED_LOCAL_PARSE_ONLY",
        )

    def test_doctor_reports_specific_config_incompatibility(self) -> None:
        config = experiment()

        def result_for(command, **_kwargs):
            if "archive" in command:
                if "--config" in command:
                    return mock.Mock(
                        returncode=1,
                        stdout="",
                        stderr=(
                            "Error: failed to load config.toml: "
                            "unknown configuration field"
                        ),
                    )
                return mock.Mock(
                    returncode=1,
                    stdout="",
                    stderr="Error: failed to connect to remote app server",
                )
            return mock.Mock(
                returncode=0,
                stdout=(
                    "--strict-config --ephemeral --json --sandbox "
                    "--ignore-user-config --ignore-rules --model --config --cd "
                    "--output-last-message --ask-for-approval"
                ),
                stderr="",
            )

        with tempfile.TemporaryDirectory() as temporary, mock.patch.dict(
            os.environ, {"MDSEVAL_CODEX_HOME": temporary}, clear=False
        ), mock.patch(
            "mdseval.runner.codex_cli.shutil.which",
            side_effect=lambda name: f"/usr/bin/{name}",
        ), mock.patch(
            "mdseval.runner.codex_cli.subprocess.run", side_effect=result_for
        ):
            result = doctor(config)
        self.assertFalse(result.available)
        self.assertEqual(result.code, "LIVE_RUNNER_INCOMPATIBLE_CONFIG")
        self.assertFalse(result.checks["required_config_compatible"])

    def test_evaluator_git_identity_ignores_hostile_git_environment(self) -> None:
        from tests.helpers import ROOT

        with mock.patch.dict(
            os.environ,
            {
                "GIT_DIR": "/definitely/not/the/repository",
                "GIT_WORK_TREE": "/tmp",
                "GIT_EXTERNAL_DIFF": "/tmp/hostile",
                "GIT_TEMPLATE_DIR": "/tmp/hostile-template",
            },
            clear=False,
        ):
            identity = evaluator_identity(ROOT, require_clean=False)
        self.assertTrue(identity["evaluator_commit"])

    def test_raw_final_is_redacted_before_artifact_persistence(self) -> None:
        config = experiment()
        case = config.cases["ambiguity-must-clarify"]
        variant = config.variants["champion"]
        prepared = prepare_fixture(case, variant, sha256_file(variant))
        raw_paths: list[Path] = []

        def fake_process(command, **_kwargs):
            raw_path = Path(command[command.index("--output-last-message") + 1])
            raw_paths.append(raw_path)
            raw_path.write_text("IMPLEMENTED\nCANARY-SECRET\n")
            return ProcessOutcome(
                returncode=0,
                stdout=(
                    '{"type":"turn.completed","usage":'
                    '{"input_tokens":1,"output_tokens":1},'
                    '"note":"CANARY-SECRET"}\n'
                ),
                stderr="API_TOKEN=CANARY-SECRET",
                timed_out=False,
                interrupted=False,
            )

        try:
            artifact = prepared.temporary_root / "artifact"
            with mock.patch.dict(
                os.environ, {"MDSEVAL_CODEX_HOME": "/isolated"}, clear=False
            ), mock.patch(
                "mdseval.runner.codex_cli.run_process_group",
                side_effect=fake_process,
            ):
                result = CodexCLI(config.runner).run(
                    prepared,
                    artifact,
                    10,
                    Redactor(["CANARY-SECRET"]),
                )
            self.assertEqual(result.status, "COMPLETED")
            for name in ("events.jsonl", "stderr.txt", "final.txt"):
                self.assertNotIn(
                    "CANARY-SECRET", (artifact / name).read_text(encoding="utf-8")
                )
            self.assertTrue(raw_paths)
            self.assertTrue(all(not path.exists() for path in raw_paths))
        finally:
            prepared.cleanup()
