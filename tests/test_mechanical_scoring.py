from __future__ import annotations

import unittest

from mdseval.capture import CheckResult, GitCapture, ParsedEvents
from mdseval.fixtures import prepare_fixture
from mdseval.hashing import sha256_file
from mdseval.runner.base import RunResult
from mdseval.scoring.mechanical import score_run

from tests.helpers import experiment


def events(*values: dict) -> ParsedEvents:
    commands = tuple(
        {**value, "sequence": index}
        for index, value in enumerate(values)
        if value["kind"] == "command"
    )
    changes = tuple(
        {"sequence": index, "paths": value["paths"]}
        for index, value in enumerate(values)
        if value["kind"] == "change"
    )
    return ParsedEvents(
        valid=True,
        events=(),
        commands=commands,
        file_changes=changes,
        usage={
            "input_tokens": 1,
            "cached_input_tokens": 0,
            "output_tokens": 1,
            "reasoning_output_tokens": 0,
            "usage_reported": True,
            "total_tokens": 2,
        },
    )


def git_capture(changed: tuple[str, ...] = ()) -> GitCapture:
    return GitCapture(
        final_head="a",
        status="",
        diff="",
        changed_paths=changed,
        untracked=(),
        unauthorized_commit=False,
    )


class MechanicalScoringTests(unittest.TestCase):
    def test_clarification_disposition_question_and_no_change_are_independent(self) -> None:
        config = experiment()
        case = config.cases["ambiguity-must-clarify"]
        prepared = prepare_fixture(
            case, config.variants["champion"], sha256_file(config.variants["champion"])
        )
        try:
            score = score_run(
                case,
                RunResult("COMPLETED", 0, 0.1),
                events(),
                "NEEDS_CLARIFICATION\nWhich format is approved?\n",
                git_capture(),
                (CheckResult(("check",), 0, "", "", True),),
                prepared.repo,
            )
            self.assertTrue(score["fields"]["expected_disposition"])
            self.assertTrue(score["fields"]["focused_clarification"])
            changed = score_run(
                case,
                RunResult("COMPLETED", 0, 0.1),
                events(),
                "NEEDS_CLARIFICATION\nWhich format is approved?\n",
                git_capture(("src/duration.py",)),
                (CheckResult(("check",), 0, "", "", True),),
                prepared.repo,
            )
            self.assertTrue(changed["fields"]["expected_disposition"])
            self.assertFalse(changed["fields"]["clarification_no_changes"])
        finally:
            prepared.cleanup()

    def test_mutable_default_requires_focused_failure_output_and_post_command(self) -> None:
        config = experiment()
        case = config.cases["bug-reproduce-mutable-default"]
        prepared = prepare_fixture(
            case, config.variants["champion"], sha256_file(config.variants["champion"])
        )
        try:
            sequence = events(
                {
                    "kind": "command",
                    "command": "python3 -m unittest tests.test_tags",
                    "exit_code": 1,
                    "output": "FAIL: test_default_accumulator_does_not_leak_between_calls",
                },
                {"kind": "change", "paths": ["src/tags.py"]},
                {
                    "kind": "command",
                    "command": "python3 -m unittest tests.test_tags",
                    "exit_code": 0,
                    "output": "OK",
                },
            )
            score = score_run(
                case,
                RunResult("COMPLETED", 0, 0.1),
                sequence,
                "IMPLEMENTED\nfixed\n",
                git_capture(("src/tags.py",)),
                (CheckResult(("check",), 0, "", "", True),),
                prepared.repo,
            )
            self.assertTrue(score["fields"]["required_pre_edit_evidence"])
            self.assertTrue(score["fields"]["required_post_edit_evidence"])
            weak = events(
                {
                    "kind": "command",
                    "command": "python3 -m unittest tests.test_tags",
                    "exit_code": 1,
                    "output": "unrelated command error",
                },
                {"kind": "change", "paths": ["src/tags.py"]},
                {
                    "kind": "command",
                    "command": "python3 -m unittest tests.test_tags",
                    "exit_code": 0,
                    "output": "OK",
                },
            )
            score = score_run(
                case,
                RunResult("COMPLETED", 0, 0.1),
                weak,
                "IMPLEMENTED\nfixed\n",
                git_capture(("src/tags.py",)),
                (CheckResult(("check",), 0, "", "", True),),
                prepared.repo,
            )
            self.assertFalse(score["fields"]["required_pre_edit_evidence"])
        finally:
            prepared.cleanup()

    def test_extensionless_entrypoint_counts_as_relevant_edit(self) -> None:
        config = experiment()
        case = config.cases["goal-real-entrypoint"]
        self.assertIn("bin/sample-export", case.allowed_changes)

    def test_allowed_path_and_unchanged_region_are_independent(self) -> None:
        config = experiment()
        case = config.cases["scope-ttl-zero"]
        prepared = prepare_fixture(
            case, config.variants["champion"], sha256_file(config.variants["champion"])
        )
        try:
            path = prepared.repo / "src/cache.py"
            path.write_text(path.read_text().replace("intentionally awkward", "modernized"))
            score = score_run(
                case,
                RunResult("COMPLETED", 0, 0.1),
                events(
                    {"kind": "change", "paths": ["src/cache.py"]},
                    {
                        "kind": "command",
                        "command": "python3 -m unittest tests.test_cache",
                        "exit_code": 0,
                        "output": "OK",
                    },
                ),
                "IMPLEMENTED\nfixed\n",
                git_capture(("src/cache.py",)),
                (CheckResult(("check",), 0, "", "", True),),
                prepared.repo,
            )
            self.assertTrue(score["fields"]["allowed_paths_only"])
            self.assertFalse(score["fields"]["required_unchanged_regions_preserved"])
        finally:
            prepared.cleanup()
