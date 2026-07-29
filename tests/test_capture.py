from __future__ import annotations

import json
import os
import base64
import subprocess
import unittest
from pathlib import Path

from mdseval.capture import Redactor, capture_git, parse_event_stream
from mdseval.fixtures import prepare_fixture
from mdseval.hashing import sha256_file

from tests.helpers import experiment, git


class CaptureTests(unittest.TestCase):
    def setUp(self) -> None:
        config = experiment()
        self.case = config.cases["goal-status-422"]
        variant = config.variants["champion"]
        self.prepared = prepare_fixture(self.case, variant, sha256_file(variant))

    def tearDown(self) -> None:
        self.prepared.cleanup()

    def test_committed_staged_unstaged_and_untracked_are_captured(self) -> None:
        repo = self.prepared.repo
        source = repo / "src/statuses.py"
        source.write_text(source.read_text() + "\n# committed\n")
        git(repo, "add", "src/statuses.py")
        git(repo, "commit", "-m", "unauthorized")
        source.write_text(source.read_text() + "# unstaged\n")
        (repo / "tests/new_test.py").write_text("# staged\n")
        git(repo, "add", "tests/new_test.py")
        (repo / "notes.md").write_text("untracked\n")
        captured = capture_git(repo, self.prepared.baseline_commit, Redactor())
        self.assertTrue(captured.unauthorized_commit)
        self.assertIn("src/statuses.py", captured.changed_paths)
        self.assertIn("tests/new_test.py", captured.changed_paths)
        self.assertIn("notes.md", captured.changed_paths)
        self.assertIn("notes.md", captured.diff)

    def test_ignored_untracked_files_are_not_hidden(self) -> None:
        repo = self.prepared.repo
        (repo / ".gitignore").write_text("*\n")
        (repo / "secret.env").write_text("VALUE=canary\n")
        (repo / ".git/info").mkdir(parents=True, exist_ok=True)
        (repo / ".git/info/exclude").write_text("excluded.md\n")
        (repo / "excluded.md").write_text("must capture\n")
        captured = capture_git(repo, self.prepared.baseline_commit, Redactor())
        self.assertIn(".gitignore", captured.changed_paths)
        self.assertIn("secret.env", captured.changed_paths)
        self.assertIn("excluded.md", captured.changed_paths)

    def test_commit_then_reset_and_side_branch_are_unauthorized(self) -> None:
        repo = self.prepared.repo
        (repo / "temp.txt").write_text("x")
        git(repo, "add", "temp.txt")
        git(repo, "commit", "-m", "hidden")
        git(repo, "reset", "--hard", self.prepared.baseline_commit)
        captured = capture_git(repo, self.prepared.baseline_commit, Redactor())
        self.assertTrue(captured.unauthorized_commit)
        self.assertIn("temp.txt", captured.changed_paths)
        self.assertIn("temp.txt", captured.historical_diff)

    def test_redaction_covers_values_and_assignments(self) -> None:
        redactor = Redactor(["CANARY-SECRET"])
        text = redactor.text("x CANARY-SECRET API_TOKEN=abc y")
        self.assertNotIn("CANARY-SECRET", text)
        self.assertNotIn("abc", text)
        self.assertIn("[REDACTED]", text)
        self.assertEqual(
            redactor.text("MONKEY=banana COMPASS=north"),
            "MONKEY=banana COMPASS=north",
        )
        self.assertIn("API_TOKEN=[REDACTED]", redactor.text('API_TOKEN="a b"'))
        serialized = json.dumps(
            redactor.object(
                {
                    "fixture/CANARY-SECRET.txt": "CANARY-SECRET",
                    "fixture/[REDACTED].txt": "second",
                }
            )
        )
        self.assertNotIn("CANARY-SECRET", serialized)
        self.assertIn("#2", serialized)

    def test_binary_secret_and_expanding_redaction_stay_bounded(self) -> None:
        repo = self.prepared.repo
        secret = "S"
        (repo / "binary.dat").write_bytes(b"prefix\xffSsuffix")
        (repo / "second.dat").write_bytes(b"S" * 100)
        captured = capture_git(
            repo, self.prepared.baseline_commit, Redactor([secret])
        )
        serialized = json.dumps(captured.untracked)
        self.assertNotIn(base64.b64encode(b"prefix\xffSsuffix").decode(), serialized)
        self.assertLessEqual(
            sum(item["raw_bytes_captured"] for item in captured.untracked),
            524_288,
        )

    def test_secret_filename_is_redacted_in_metadata(self) -> None:
        repo = self.prepared.repo
        (repo / "CANARY.txt").write_text("x")
        captured = capture_git(
            repo, self.prepared.baseline_commit, Redactor(["CANARY"])
        )
        self.assertNotIn("CANARY", json.dumps(captured.untracked))
        self.assertNotIn("CANARY", json.dumps(captured.changed_paths))

    def test_event_parser_preserves_unknown_and_token_arithmetic(self) -> None:
        path = self.prepared.temporary_root / "events.jsonl"
        path.write_text(
            "\n".join(
                (
                    json.dumps({"type": "unknown.future", "value": 1}),
                    json.dumps({"type": "command", "command": "test", "exit_code": 0}),
                    json.dumps(
                        {
                            "type": "turn.completed",
                            "usage": {
                                "input_tokens": 10,
                                "cached_input_tokens": 7,
                                "output_tokens": 3,
                                "reasoning_output_tokens": 2,
                            },
                        }
                    ),
                    "malformed",
                )
            )
        )
        parsed = parse_event_stream(path)
        self.assertFalse(parsed.valid)
        self.assertEqual(parsed.events[0]["type"], "unknown.future")
        self.assertEqual(parsed.usage["total_tokens"], 13)
        self.assertTrue(parsed.usage["usage_reported"])

    def test_usage_is_incomplete_if_any_usage_turn_is_partial(self) -> None:
        path = self.prepared.temporary_root / "partial-events.jsonl"
        path.write_text(
            "\n".join(
                (
                    json.dumps(
                        {
                            "type": "turn.completed",
                            "usage": {"input_tokens": 5, "output_tokens": 2},
                        }
                    ),
                    json.dumps(
                        {
                            "type": "turn.completed",
                            "usage": {"input_tokens": 3},
                        }
                    ),
                )
            )
        )
        parsed = parse_event_stream(path)
        self.assertEqual(parsed.usage["total_tokens"], 10)
        self.assertFalse(parsed.usage["usage_reported"])
