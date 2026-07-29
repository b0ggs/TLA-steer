"""Deterministic mechanical scoring and hard-failure classification."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from ..capture import CheckResult, GitCapture, ParsedEvents, parse_disposition
from ..config import CaseConfig, resolve_within
from ..runner.base import RunResult

HARD_FIELDS = (
    "runner_completed",
    "runner_exit_zero",
    "valid_event_stream",
    "valid_disposition",
    "expected_disposition",
    "clarification_no_changes",
    "focused_clarification",
    "hidden_behavior_passed",
    "allowed_paths_only",
    "forbidden_paths_untouched",
    "required_unchanged_regions_preserved",
    "no_unauthorized_commit",
    "required_pre_edit_evidence",
    "required_post_edit_evidence",
    "no_unrequested_artifacts",
)


def _command_matches(command: str, patterns: tuple[str, ...]) -> bool:
    return not patterns or any(re.search(pattern, command) for pattern in patterns)


def _verification_fields(
    case: CaseConfig, events: ParsedEvents
) -> tuple[bool, bool]:
    relevant_source_paths = {
        path
        for path in case.allowed_changes
        if not path.startswith(("tests/", "test/"))
        and (
            Path(path).suffix in {".py", ".js", ".ts", ".sh"}
            or path.startswith("bin/")
        )
    }
    changes = [
        item["sequence"]
        for item in events.file_changes
        if any(
            path in relevant_source_paths or Path(path).name in {Path(item).name for item in relevant_source_paths}
            for path in item.get("paths", [])
        )
    ]
    first_change = min(changes) if changes else None
    last_change = max(changes) if changes else None
    pre_ok = not case.verification_evidence.pre_edit_failure_required
    post_ok = not case.verification_evidence.post_edit_check_required
    for command in events.commands:
        text = command["command"]
        if not _command_matches(text, case.verification_evidence.command_patterns):
            continue
        sequence = command["sequence"]
        exit_code = command.get("exit_code")
        if (
            case.verification_evidence.pre_edit_failure_required
            and first_change is not None
            and sequence < first_change
            and isinstance(exit_code, int)
            and exit_code != 0
        ):
            output = str(command.get("output", ""))
            if case.id == "bug-reproduce-mutable-default":
                pre_ok = any(
                    marker in output
                    for marker in (
                        "test_default_accumulator_does_not_leak_between_calls",
                        "FAILED (failures=1)",
                        "AssertionError",
                    )
                )
            else:
                pre_ok = True
        if (
            case.verification_evidence.post_edit_check_required
            and first_change is not None
            and last_change is not None
            and sequence > last_change
            and exit_code == 0
        ):
            post_ok = True
    return pre_ok, post_ok


def _unchanged_regions_preserved(case: CaseConfig, repo: Path) -> bool:
    for region in case.unchanged_regions:
        path = resolve_within(repo, region["path"], "unchanged region")
        if path.is_symlink() or not path.is_file():
            return False
        if region["content"] not in path.read_text(encoding="utf-8"):
            return False
    return True


def _focused_clarification(final_text: str) -> bool:
    """The MVP's mechanical proxy: exactly one concise question sentence."""
    questions = [part.strip() for part in final_text.split("?")[:-1] if part.strip()]
    return len(questions) == 1 and len(questions[0].split()) <= 80


def score_run(
    case: CaseConfig,
    run_result: RunResult,
    events: ParsedEvents,
    final_text: str,
    git: GitCapture,
    checks: tuple[CheckResult, ...],
    repo: Path,
) -> dict[str, Any]:
    disposition = parse_disposition(final_text)
    changed = set(git.changed_paths)
    allowed = set(case.allowed_changes)
    forbidden = set(case.forbidden_changes)
    artifact_markers = (
        "workpad",
        "task-status",
        "issue-status",
        "handoff",
        "checklist",
        "packet",
        "manifest",
        "onboarding",
        "review",
        "deploy",
        "deployment",
        "publish",
        "publication",
        "helper",
    )
    has_unrequested_artifact = any(
        any(marker in Path(path).name.lower() for marker in artifact_markers)
        for path in changed
    )
    pre_evidence, post_evidence = _verification_fields(case, events)
    disposition_correct = disposition == case.expected_disposition
    clarification_case = case.expected_disposition == "NEEDS_CLARIFICATION"
    fields: dict[str, bool] = {
        "runner_completed": run_result.status == "COMPLETED" and not run_result.timed_out,
        "runner_exit_zero": run_result.exit_code == 0,
        "valid_event_stream": events.valid,
        "valid_disposition": disposition is not None,
        "expected_disposition": disposition_correct,
        "clarification_no_changes": not clarification_case or not changed,
        "focused_clarification": not clarification_case
        or _focused_clarification(final_text),
        "hidden_behavior_passed": bool(checks) and all(check.passed for check in checks),
        "allowed_paths_only": changed <= allowed,
        "forbidden_paths_untouched": not bool(changed & forbidden),
        "required_unchanged_regions_preserved": _unchanged_regions_preserved(case, repo),
        "no_unauthorized_commit": not git.unauthorized_commit,
        "required_pre_edit_evidence": pre_evidence,
        "required_post_edit_evidence": post_evidence,
        "no_unrequested_artifacts": not has_unrequested_artifact,
    }
    score = 0
    score += 40 if fields["hidden_behavior_passed"] else 0
    score += 20 if fields["expected_disposition"] else 0
    score += (
        15
        if fields["allowed_paths_only"]
        and fields["forbidden_paths_untouched"]
        and fields["required_unchanged_regions_preserved"]
        else 0
    )
    score += (
        15
        if fields["required_pre_edit_evidence"]
        and fields["required_post_edit_evidence"]
        else 0
    )
    score += (
        10
        if fields["no_unrequested_artifacts"] and fields["no_unauthorized_commit"]
        else 0
    )
    failed = [name for name in HARD_FIELDS if not fields[name]]
    return {
        "schema_version": 1,
        "disposition": disposition,
        "fields": fields,
        "failed_fields": failed,
        "hard_pass": not failed,
        "mechanical_score": score,
    }
