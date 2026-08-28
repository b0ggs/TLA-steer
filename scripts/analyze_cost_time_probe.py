#!/usr/bin/env python3
"""Analyze a fixed null-versus-candidate cost/time batch without live calls."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import statistics
import sys
import tempfile
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_BATCH_DIR = ROOT / "runs" / "dev-v2" / "cost-time-probe-v1"
DEFAULT_ANALYSIS_OUTPUT = DEFAULT_BATCH_DIR / "analysis.json"
DEFAULT_SUMMARY_OUTPUT = ROOT / "handoffs" / "COST_TIME_PROBE_RESULT.md"

CENSOR_SECONDS = 900.0
EXPECTED_ATTEMPTS = 3
NULL_ARM_PATH = "controls/coder/null-m2.md"
PROBE_ARM_PATH = "controls/coder/cost-time-probe-v1.md"
EMPTY_SHA256 = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
METRICS = (
    "primary_token_cost",
    "wall_time_seconds",
    "trajectory_length",
)
METRIC_LABELS = {
    "primary_token_cost": "Primary token cost",
    "wall_time_seconds": "Wall time",
    "trajectory_length": "Trajectory length",
}
TRAJECTORY_ITEM_TYPES = frozenset({"command_execution", "file_change"})


class AnalysisError(ValueError):
    """The batch evidence is absent, malformed, or inconsistent."""


def _fail(message: str) -> None:
    raise AnalysisError(message)


def _read_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        _fail(f"missing required file: {path}")
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        _fail(f"cannot read JSON object {path}: {type(exc).__name__}: {exc}")
    if not isinstance(value, dict):
        _fail(f"expected a JSON object: {path}")
    return value


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    try:
        with path.open("rb") as stream:
            for chunk in iter(lambda: stream.read(1024 * 1024), b""):
                digest.update(chunk)
    except OSError as exc:
        _fail(f"cannot hash {path}: {type(exc).__name__}: {exc}")
    return digest.hexdigest()


def _is_number(value: object) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def _nonnegative_number(value: object, context: str) -> int | float:
    if (
        not _is_number(value)
        or not math.isfinite(float(value))
        or value < 0  # type: ignore[operator]
    ):
        _fail(f"{context} must be a finite nonnegative number")
    return value  # type: ignore[return-value]


def _boolean(value: object, context: str) -> bool:
    if not isinstance(value, bool):
        _fail(f"{context} must be boolean")
    return value


def _string_list(value: object, context: str) -> list[str]:
    if not isinstance(value, list) or any(not isinstance(item, str) for item in value):
        _fail(f"{context} must be a list of strings")
    return list(value)


def _bool_map(value: object, context: str) -> dict[str, bool]:
    if not isinstance(value, dict) or any(
        not isinstance(key, str) or not isinstance(item, bool)
        for key, item in value.items()
    ):
        _fail(f"{context} must be a string-to-boolean object")
    return dict(value)


def _request_shape(
    batch_dir: Path,
    null_arm: str | None,
    probe_arm: str | None,
    probe_path: str,
) -> tuple[dict[str, Any], list[str], list[str], str, str, dict[str, dict[str, str]]]:
    request = _read_json(batch_dir / "REQUEST.json")
    batch_id = request.get("batch_id")
    if not isinstance(batch_id, str) or not batch_id:
        _fail("REQUEST.json batch_id must be a nonempty string")

    task_rows = request.get("tasks")
    if not isinstance(task_rows, list) or not task_rows:
        _fail("REQUEST.json tasks must be a nonempty list")
    task_ids: list[str] = []
    for index, row in enumerate(task_rows):
        if not isinstance(row, dict) or not isinstance(row.get("id"), str) or not row["id"]:
            _fail(f"REQUEST.json tasks[{index}] has no valid id")
        task_ids.append(row["id"])
    if len(set(task_ids)) != len(task_ids):
        _fail("REQUEST.json has duplicate task ids")

    arm_rows = request.get("arms")
    if not isinstance(arm_rows, list) or len(arm_rows) != 2:
        _fail("REQUEST.json must contain exactly two arms")
    arm_names: list[str] = []
    arms_by_path: dict[str, dict[str, str]] = {}
    for index, row in enumerate(arm_rows):
        if not isinstance(row, dict) or not isinstance(row.get("name"), str) or not row["name"]:
            _fail(f"REQUEST.json arms[{index}] has no valid name")
        path = row.get("path")
        digest = row.get("sha256")
        if not isinstance(path, str) or not path:
            _fail(f"REQUEST.json arms[{index}] has no valid path")
        if (
            not isinstance(digest, str)
            or len(digest) != 64
            or any(character not in "0123456789abcdef" for character in digest)
        ):
            _fail(f"REQUEST.json arms[{index}] has no valid sha256")
        arm_names.append(row["name"])
        if path in arms_by_path:
            _fail("REQUEST.json has duplicate arm paths")
        arms_by_path[path] = {"name": row["name"], "path": path, "sha256": digest}
    if len(set(arm_names)) != 2:
        _fail("REQUEST.json has duplicate arm names")
    if not probe_path or probe_path == NULL_ARM_PATH:
        _fail("probe path must be nonempty and different from the fixed null arm path")
    if set(arms_by_path) != {NULL_ARM_PATH, probe_path}:
        _fail(
            f"REQUEST.json arms must bind the fixed null path and probe path {probe_path!r}"
        )
    derived_null = arms_by_path[NULL_ARM_PATH]["name"]
    derived_probe = arms_by_path[probe_path]["name"]
    if arms_by_path[NULL_ARM_PATH]["sha256"] != EMPTY_SHA256:
        _fail("REQUEST.json null arm does not have the zero-byte SHA-256")
    if null_arm is not None and null_arm != derived_null:
        _fail(f"--null-arm {null_arm!r} conflicts with the fixed null arm path")
    if probe_arm is not None and probe_arm != derived_probe:
        _fail(f"--probe-arm {probe_arm!r} conflicts with the fixed probe arm path")
    null_arm, probe_arm = derived_null, derived_probe

    runner = request.get("runner")
    if not isinstance(runner, dict):
        _fail("REQUEST.json runner must be an object")
    timeout = runner.get("timeout_seconds")
    if not _is_number(timeout) or float(timeout) != CENSOR_SECONDS:
        _fail("the cost/time probe request must use the fixed 900-second attempt timeout")

    bindings = {"null": arms_by_path[NULL_ARM_PATH], "probe": arms_by_path[probe_path]}
    return request, task_ids, arm_names, null_arm, probe_arm, bindings


def _verify_analysis_files(attempt_dir: Path, manifest: dict[str, Any]) -> None:
    files = manifest.get("files")
    if not isinstance(files, dict):
        _fail(f"attempt manifest files must be an object: {attempt_dir}")
    for name in ("result.json", "checker.json", "capture.json", "events.jsonl"):
        expected = files.get(name)
        if not isinstance(expected, str) or len(expected) != 64:
            _fail(f"attempt manifest does not bind {name}: {attempt_dir}")
        path = attempt_dir / name
        if not path.is_file() or path.is_symlink():
            _fail(f"finalized attempt is missing regular {name}: {attempt_dir}")
        if _sha256(path) != expected:
            _fail(f"attempt manifest hash mismatch for {name}: {attempt_dir}")


def _event_metrics(path: Path) -> tuple[int, list[str]]:
    completed_trajectory_ids: set[str] = set()
    completed_categories_by_id: dict[str, str] = {}
    ordered_categories: list[str] = []
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except (OSError, UnicodeError) as exc:
        _fail(f"cannot read event stream {path}: {type(exc).__name__}: {exc}")
    for number, line in enumerate(lines, 1):
        if not line.strip():
            continue
        try:
            event = json.loads(line)
        except json.JSONDecodeError as exc:
            _fail(f"malformed event JSON at {path}:{number}: {exc}")
        if not isinstance(event, dict):
            _fail(f"event must be an object at {path}:{number}")
        event_type = event.get("type")
        if event_type != "item.completed":
            continue
        item = event.get("item")
        if not isinstance(item, dict):
            continue
        category = item.get("type")
        if not isinstance(category, str) or not category:
            continue
        if category not in TRAJECTORY_ITEM_TYPES:
            continue
        item_id = item.get("id")
        if not isinstance(item_id, str) or not item_id:
            _fail(f"completed command/file item has no id at {path}:{number}")
        prior = completed_categories_by_id.get(item_id)
        if prior is None:
            completed_categories_by_id[item_id] = category
            ordered_categories.append(category)
        elif prior != category:
            _fail(f"completed item {item_id!r} changes category in {path}")
        completed_trajectory_ids.add(item_id)
    return len(completed_trajectory_ids), ordered_categories


def _checker(path: Path, result: dict[str, Any]) -> dict[str, Any]:
    checker = _read_json(path)
    requirements = _bool_map(checker.get("requirements"), f"{path} requirements")
    regressions = _bool_map(checker.get("regressions"), f"{path} regressions")
    resolved = _boolean(checker.get("resolved"), f"{path} resolved")
    for key, value in (
        ("requirements", requirements),
        ("regressions", regressions),
        ("resolved", resolved),
    ):
        if result.get(key) != value:
            _fail(f"checker/result {key} mismatch: {path.parent}")
    return {
        "requirements": requirements,
        "regressions": regressions,
        "resolved": resolved,
    }


def _token_evidence(
    result: dict[str, Any], context: str
) -> tuple[bool, dict[str, Any], int | None]:
    totals = result.get("token_totals")
    if not isinstance(totals, dict):
        _fail(f"{context} token_totals must be an object")
    usage_reported = _boolean(totals.get("usage_reported"), f"{context} usage_reported")
    values: dict[str, int] = {}
    for name in ("input_tokens", "cached_input_tokens", "output_tokens"):
        value = totals.get(name)
        if not isinstance(value, int) or isinstance(value, bool) or value < 0:
            _fail(f"{context} {name} must be a nonnegative integer")
        values[name] = value
    if values["cached_input_tokens"] > values["input_tokens"]:
        _fail(f"{context} cached input exceeds input tokens")
    primary = (
        values["input_tokens"]
        - values["cached_input_tokens"]
        + values["output_tokens"]
        if usage_reported
        else None
    )
    reported_totals = {
        "input_tokens": values["input_tokens"],
        "cached_input_tokens": values["cached_input_tokens"],
        "output_tokens": values["output_tokens"],
    }
    return usage_reported, reported_totals, primary


def _unfinished_attempt(attempt_dir: Path, ordinal: int) -> dict[str, Any]:
    if (attempt_dir / "result.json").exists():
        _fail(f"attempt has result.json but no finalizing manifest: {attempt_dir}")
    status = "unfinished"
    status_evidence: dict[str, str] | None = None
    for name, label in (
        ("infra-invalid.json", "runner infrastructure failure"),
        ("pre-spawn.json", "pre-spawn failure"),
        ("build-rejected.json", "sealed build rejected"),
    ):
        path = attempt_dir / name
        if not path.exists():
            continue
        if status_evidence is not None:
            _fail(f"unfinished attempt has multiple terminal status files: {attempt_dir}")
        evidence = _read_json(path)
        error = evidence.get("error")
        if not isinstance(error, str):
            _fail(f"{path} error must be a string")
        status = label
        status_evidence = {"file": name, "error": error}

    trajectory: int | None = None
    categories: list[str] | None = None
    events_path = attempt_dir / "events.jsonl"
    if events_path.exists():
        if not events_path.is_file() or events_path.is_symlink():
            _fail(f"unfinished attempt events are not a regular file: {events_path}")
        trajectory, categories = _event_metrics(events_path)

    changed_paths: list[str] | None = None
    capture_path = attempt_dir / "capture.json"
    if capture_path.exists():
        if not capture_path.is_file() or capture_path.is_symlink():
            _fail(f"unfinished attempt capture is not a regular file: {capture_path}")
        capture = _read_json(capture_path)
        if "changed_paths" in capture:
            changed_paths = _string_list(
                capture["changed_paths"], f"{capture_path} changed_paths"
            )

    exclusion = f"not finalized: {status}"
    reasons = {metric: exclusion for metric in METRICS}
    return {
        "ordinal": ordinal,
        "directory": attempt_dir.name,
        "status": status,
        "status_evidence": status_evidence,
        "finalized": False,
        "valid": None,
        "usable": False,
        "exclusion_reason": exclusion,
        "metric_usable": {metric: False for metric in METRICS},
        "metric_exclusion_reasons": reasons,
        "usage_reported": None,
        "token_totals": None,
        "primary_token_cost": None,
        "recorded_duration_seconds": None,
        "wall_time_seconds": None,
        "wall_time_censored": None,
        "trajectory_length": trajectory,
        "resolved": None,
        "checker": None,
        "changed_paths": changed_paths,
        "ordered_tool_call_categories": categories,
    }


def _finalized_attempt(
    attempt_dir: Path, ordinal: int, task_id: str, arm_name: str
) -> dict[str, Any]:
    manifest = _read_json(attempt_dir / "attempt-manifest.json")
    _verify_analysis_files(attempt_dir, manifest)
    result_path = attempt_dir / "result.json"
    result = _read_json(result_path)
    expected = {
        "task_id": task_id,
        "arm": arm_name,
        "ordinal": ordinal,
    }
    for key, value in expected.items():
        if result.get(key) != value:
            _fail(f"result {key} binding mismatch: {attempt_dir}")

    valid = _boolean(result.get("valid"), f"{result_path} valid")
    invalid_reason = result.get("invalid_reason")
    if not isinstance(invalid_reason, str):
        _fail(f"{result_path} invalid_reason must be a string")
    timed_out = _boolean(result.get("timed_out"), f"{result_path} timed_out")
    recorded_duration = _nonnegative_number(
        result.get("duration_seconds"), f"{result_path} duration_seconds"
    )
    wall_time = CENSOR_SECONDS if timed_out else recorded_duration
    usage_reported, token_totals, primary = _token_evidence(result, str(result_path))
    checker = _checker(attempt_dir / "checker.json", result)
    trajectory, categories = _event_metrics(attempt_dir / "events.jsonl")

    capture_path = attempt_dir / "capture.json"
    capture = _read_json(capture_path)
    changed_paths: list[str] | None
    if "changed_paths" in capture:
        changed_paths = _string_list(capture["changed_paths"], f"{capture_path} changed_paths")
    else:
        changed_paths = None
        if valid:
            _fail(f"valid attempt capture has no changed_paths: {attempt_dir}")

    usable = valid
    exclusion_reason = (
        None if usable else f"invalid attempt: {invalid_reason or 'unspecified reason'}"
    )
    metric_usable = {
        "primary_token_cost": usable and usage_reported,
        "wall_time_seconds": usable,
        "trajectory_length": usable,
    }
    metric_reasons: dict[str, str | None] = {}
    for metric in METRICS:
        if not usable:
            metric_reasons[metric] = exclusion_reason
        elif metric == "primary_token_cost" and not usage_reported:
            metric_reasons[metric] = "usage not reported"
        else:
            metric_reasons[metric] = None

    return {
        "ordinal": ordinal,
        "directory": attempt_dir.name,
        "status": "finalized",
        "status_evidence": None,
        "finalized": True,
        "valid": valid,
        "usable": usable,
        "exclusion_reason": exclusion_reason,
        "metric_usable": metric_usable,
        "metric_exclusion_reasons": metric_reasons,
        "usage_reported": usage_reported,
        "token_totals": token_totals,
        "primary_token_cost": primary,
        "recorded_duration_seconds": recorded_duration,
        "wall_time_seconds": wall_time,
        "wall_time_censored": timed_out,
        "trajectory_length": trajectory,
        "resolved": checker["resolved"],
        "checker": checker,
        "changed_paths": changed_paths,
        "ordered_tool_call_categories": categories,
    }


def _attempts(arm_dir: Path, task_id: str, arm_name: str) -> list[dict[str, Any]]:
    if not arm_dir.is_dir():
        _fail(f"missing task/arm evidence directory: {arm_dir}")
    indexed: list[tuple[int, Path]] = []
    for path in arm_dir.glob("attempt-*"):
        if not path.is_dir() or path.is_symlink():
            _fail(f"attempt evidence is not a regular directory: {path}")
        suffix = path.name.removeprefix("attempt-")
        if not suffix.isdigit() or int(suffix) < 1:
            _fail(f"invalid attempt directory name: {path}")
        indexed.append((int(suffix), path))
    indexed.sort()
    if len({ordinal for ordinal, _ in indexed}) != len(indexed):
        _fail(f"duplicate attempt ordinal under {arm_dir}")
    attempts: list[dict[str, Any]] = []
    for ordinal, path in indexed:
        if (path / "attempt-manifest.json").is_file():
            attempts.append(_finalized_attempt(path, ordinal, task_id, arm_name))
        else:
            attempts.append(_unfinished_attempt(path, ordinal))
    return attempts


def _metric_summary(attempts: list[dict[str, Any]], metric: str) -> dict[str, Any]:
    usable = [attempt for attempt in attempts if attempt["metric_usable"][metric]]
    values = [attempt[metric] for attempt in usable]
    result: dict[str, Any] = {
        "values": values,
        "attempt_ordinals": [attempt["ordinal"] for attempt in usable],
        "usable_attempt_count": len(values),
        "excluded_attempt_count": len(attempts) - len(values),
        "median": statistics.median(values) if values else None,
    }
    if metric == "wall_time_seconds":
        result["censored_attempt_count"] = sum(
            bool(attempt["wall_time_censored"]) for attempt in usable
        )
    return result


def _arm_summary(attempts: list[dict[str, Any]]) -> dict[str, Any]:
    finalized = [attempt for attempt in attempts if attempt["finalized"]]
    valid = [attempt for attempt in finalized if attempt["valid"]]
    reported = [attempt for attempt in finalized if attempt["usage_reported"]]
    resolved_count = sum(bool(attempt["resolved"]) for attempt in valid)
    return {
        "attempts": attempts,
        "attempt_count": len(attempts),
        "finalized_attempt_count": len(finalized),
        "valid_attempt_count": len(valid),
        "usage_completeness": {
            "usage_reported_attempts": len(reported),
            "finalized_attempts": len(finalized),
            "complete": bool(finalized) and len(reported) == len(finalized),
        },
        "correctness": {
            "resolved_attempts": resolved_count,
            "expected_attempts": EXPECTED_ATTEMPTS,
            "score": f"{resolved_count}/{EXPECTED_ATTEMPTS}",
            "regression_risk": resolved_count < EXPECTED_ATTEMPTS,
        },
        "metrics": {metric: _metric_summary(attempts, metric) for metric in METRICS},
    }


def _comparison(
    null_summary: dict[str, Any], probe_summary: dict[str, Any], metric: str
) -> dict[str, Any]:
    null_metric = null_summary["metrics"][metric]
    probe_metric = probe_summary["metrics"][metric]
    null_values = null_metric["values"]
    null_median = null_metric["median"]
    probe_median = probe_metric["median"]
    enough = (
        null_metric["usable_attempt_count"] >= 2
        and probe_metric["usable_attempt_count"] >= 2
    )
    delta = (
        probe_median - null_median
        if null_median is not None and probe_median is not None
        else None
    )
    null_range = max(null_values) - min(null_values) if null_values else None
    sign = None
    if delta is not None:
        sign = "positive" if delta > 0 else "negative" if delta < 0 else "zero"
    qualifies = bool(
        enough
        and delta is not None
        and delta != 0
        and null_range is not None
        and abs(delta) > null_range
    )
    return {
        "null_usable_attempt_count": null_metric["usable_attempt_count"],
        "probe_usable_attempt_count": probe_metric["usable_attempt_count"],
        "null_median": null_median,
        "probe_median": probe_median,
        "probe_minus_null_median": delta,
        "null_arm_range": null_range,
        "has_two_usable_attempts_per_arm": enough,
        "sign": sign,
        "qualifies": qualifies,
    }


def _classification(tasks: list[dict[str, Any]], metric: str) -> dict[str, Any]:
    comparisons = [(task["task_id"], task["comparisons"][metric]) for task in tasks]
    measurable = [task_id for task_id, row in comparisons if row["has_two_usable_attempts_per_arm"]]
    positive = [
        task_id
        for task_id, row in comparisons
        if row["qualifies"] and row["sign"] == "positive"
    ]
    negative = [
        task_id
        for task_id, row in comparisons
        if row["qualifies"] and row["sign"] == "negative"
    ]
    if len(measurable) < 3:
        label = "NOT MEASURABLE"
        direction = None
        same_direction = []
    elif len(positive) >= 3:
        label = "DIRECTIONAL SIGNAL"
        direction = "probe higher than null"
        same_direction = positive
    elif len(negative) >= 3:
        label = "DIRECTIONAL SIGNAL"
        direction = "probe lower than null"
        same_direction = negative
    else:
        label = "NO DIRECTIONAL SIGNAL"
        direction = None
        same_direction = positive if len(positive) >= len(negative) else negative
    return {
        "classification": label,
        "measurable_task_count": len(measurable),
        "measurable_tasks": measurable,
        "positive_qualifying_tasks": positive,
        "negative_qualifying_tasks": negative,
        "largest_same_direction_qualifying_count": len(same_direction),
        "direction": direction,
    }


def analyze_batch(
    batch_dir: Path,
    *,
    null_arm: str | None = None,
    probe_arm: str | None = None,
    probe_path: str = PROBE_ARM_PATH,
) -> dict[str, Any]:
    batch_dir = batch_dir.resolve()
    request, task_ids, arm_names, null_arm, probe_arm, arm_bindings = _request_shape(
        batch_dir, null_arm, probe_arm, probe_path
    )
    tasks: list[dict[str, Any]] = []
    regression_risks: list[dict[str, Any]] = []
    for task_id in task_ids:
        arms: dict[str, Any] = {}
        for arm_name in arm_names:
            attempts = _attempts(batch_dir / task_id / arm_name, task_id, arm_name)
            arms[arm_name] = _arm_summary(attempts)
            correctness = arms[arm_name]["correctness"]
            if correctness["regression_risk"]:
                regression_risks.append(
                    {
                        "task_id": task_id,
                        "arm": arm_name,
                        "resolved_attempts": correctness["resolved_attempts"],
                        "expected_attempts": EXPECTED_ATTEMPTS,
                        "score": correctness["score"],
                    }
                )
        task = {
            "task_id": task_id,
            "arms": arms,
            "comparisons": {
                metric: _comparison(arms[null_arm], arms[probe_arm], metric)
                for metric in METRICS
            },
        }
        tasks.append(task)

    classifications = {metric: _classification(tasks, metric) for metric in METRICS}
    return {
        "schema_version": "cost-time-probe-analysis-v1",
        "batch_id": request["batch_id"],
        "arm_roles": {"null": null_arm, "probe": probe_arm},
        "arm_bindings": arm_bindings,
        "attempt_timeout_seconds": CENSOR_SECONDS,
        "metric_definitions": {
            "primary_token_cost": "input_tokens - cached_input_tokens + output_tokens",
            "wall_time_seconds": (
                "subject duration_seconds; timed-out attempts censored at 900 seconds"
            ),
            "trajectory_length": (
                "distinct completed item IDs of type command_execution or file_change"
            ),
        },
        "evidence_definitions": {
            "ordered_tool_call_categories": (
                "raw command_execution/file_change categories in first completed-item order, "
                "with each completed item ID listed once"
            )
        },
        "tasks": tasks,
        "classifications": classifications,
        "correctness_regression_risk": bool(regression_risks),
        "regression_risks": regression_risks,
        "interpretation": (
            "Independent descriptive triage only; not a significance test or causal claim. "
            "Correctness risks do not alter numeric classifications."
        ),
    }


def _format_number(value: int | float | None, *, signed: bool = False) -> str:
    if value is None:
        return "N/A"
    prefix = "+" if signed and value > 0 else ""
    if isinstance(value, int) or float(value).is_integer():
        return f"{prefix}{int(value):,}"
    return f"{prefix}{value:,.3f}"


def _format_values(metric: str, arm: dict[str, Any]) -> str:
    row = arm["metrics"][metric]
    if not row["values"]:
        return "N/A"
    values = [_format_number(value) for value in row["values"]]
    if metric == "wall_time_seconds" and row["censored_attempt_count"]:
        values = [
            f">={value}" if attempt["wall_time_censored"] else value
            for attempt, value in zip(
                [a for a in arm["attempts"] if a["metric_usable"][metric]], values
            )
        ]
    return (
        f"{', '.join(values)} (median {_format_number(row['median'])}; "
        f"n={row['usable_attempt_count']})"
    )


def _compress_categories(categories: list[str] | None) -> str:
    if categories is None:
        return "unavailable"
    if not categories:
        return "none"
    runs: list[tuple[str, int]] = []
    for category in categories:
        if runs and runs[-1][0] == category:
            runs[-1] = (category, runs[-1][1] + 1)
        else:
            runs.append((category, 1))
    return " → ".join(
        category if count == 1 else f"{category}×{count}" for category, count in runs
    )


def _checker_brief(checker: dict[str, Any] | None) -> str:
    if checker is None:
        return "unavailable"
    fields = [
        f"{key}={'pass' if value else 'fail'}"
        for group in ("requirements", "regressions")
        for key, value in checker[group].items()
    ]
    return ", ".join(fields) if fields else "no named checks"


def _overall_arm_summary(analysis: dict[str, Any], arm_name: str) -> dict[str, Any]:
    arms = [task["arms"][arm_name] for task in analysis["tasks"]]
    return {
        "resolved_attempts": sum(
            arm["correctness"]["resolved_attempts"] for arm in arms
        ),
        "expected_attempts": sum(
            arm["correctness"]["expected_attempts"] for arm in arms
        ),
        "primary_token_cost": {
            "total": sum(
                sum(arm["metrics"]["primary_token_cost"]["values"]) for arm in arms
            ),
            "usable_attempt_count": sum(
                arm["metrics"]["primary_token_cost"]["usable_attempt_count"]
                for arm in arms
            ),
        },
        "wall_time_seconds": {
            "total": sum(
                sum(arm["metrics"]["wall_time_seconds"]["values"]) for arm in arms
            ),
            "usable_attempt_count": sum(
                arm["metrics"]["wall_time_seconds"]["usable_attempt_count"]
                for arm in arms
            ),
        },
    }


def render_summary(analysis: dict[str, Any]) -> str:
    null_arm = analysis["arm_roles"]["null"]
    probe_arm = analysis["arm_roles"]["probe"]
    lines = ["# Cost/time probe result", ""]
    if analysis["correctness_regression_risk"]:
        lines.extend(
            [
                "> **CORRECTNESS REGRESSION RISK: YES.** At least one task/arm "
                "resolved fewer than 3/3 valid finalized attempts.",
                "",
            ]
        )
        for risk in analysis["regression_risks"]:
            lines.append(
                f"- `{risk['task_id']}` / `{risk['arm']}`: {risk['score']} resolved."
            )
        lines.append("")
    else:
        lines.extend(
            [
                "> **CORRECTNESS REGRESSION RISK: NO.** Every task/arm resolved 3/3 "
                "valid finalized attempts.",
                "",
            ]
        )

    overall_null = _overall_arm_summary(analysis, null_arm)
    overall_probe = _overall_arm_summary(analysis, probe_arm)
    lines.extend(
        [
            "## Overall outcome",
            "",
            "| Arm | Resolved | Primary-token total | Wall-time total (s) |",
            "|---|---:|---:|---:|",
        ]
    )
    for arm_name, overall in ((null_arm, overall_null), (probe_arm, overall_probe)):
        token = overall["primary_token_cost"]
        wall = overall["wall_time_seconds"]
        lines.append(
            f"| `{arm_name}` | {overall['resolved_attempts']}/"
            f"{overall['expected_attempts']} | {_format_number(token['total'])} "
            f"(n={token['usable_attempt_count']}) | {_format_number(wall['total'])} "
            f"(n={wall['usable_attempt_count']}) |"
        )
    lines.append("")
    if overall_probe["resolved_attempts"] < overall_null["resolved_attempts"]:
        lines.extend(
            [
                "**Quality gate failed:** the candidate resolved fewer attempts than null, "
                "so lower aggregate resource totals cannot be treated as an efficiency "
                "improvement.",
                "",
            ]
        )
    lines.extend(
        [
            "Totals are descriptive sums over metric-usable attempts and can be confounded "
            "by failed attempts ending earlier.",
            "",
        ]
    )

    lines.extend(
        [
            "## Metric classifications",
            "",
            "| Metric | Classification | Measurable tasks | Direction |",
            "|---|---|---:|---|",
        ]
    )
    for metric in METRICS:
        row = analysis["classifications"][metric]
        lines.append(
            f"| {METRIC_LABELS[metric]} | **{row['classification']}** | "
            f"{row['measurable_task_count']} | {row['direction'] or '—'} |"
        )
    lines.extend(
        [
            "",
            "Positive differences mean the probe arm was higher than null. Classifications "
            "are independent descriptive triage, not significance tests or causal claims. "
            "No dollar price or time-to-first-action is inferred.",
            "",
            "## Per-task comparisons",
            "",
            "| Task | Metric | Probe − null median | Null range | Qualifies |",
            "|---|---|---:|---:|---|",
        ]
    )
    for task in analysis["tasks"]:
        for metric in METRICS:
            row = task["comparisons"][metric]
            lines.append(
                f"| `{task['task_id']}` | {METRIC_LABELS[metric]} | "
                f"{_format_number(row['probe_minus_null_median'], signed=True)} | "
                f"{_format_number(row['null_arm_range'])} | "
                f"{'yes' if row['qualifies'] else 'no'} |"
            )

    lines.extend(["", "## Attempt evidence", ""])
    for task in analysis["tasks"]:
        lines.extend(
            [
                f"### `{task['task_id']}`",
                "",
                "| Arm | Primary token attempts | Wall-time attempts (s) | "
                "Trajectory attempts | Correctness | Usage |",
                "|---|---|---|---|---:|---:|",
            ]
        )
        for arm_name in (null_arm, probe_arm):
            arm = task["arms"][arm_name]
            usage = arm["usage_completeness"]
            lines.append(
                f"| `{arm_name}` | {_format_values('primary_token_cost', arm)} | "
                f"{_format_values('wall_time_seconds', arm)} | "
                f"{_format_values('trajectory_length', arm)} | "
                f"{arm['correctness']['score']} | "
                f"{usage['usage_reported_attempts']}/{usage['finalized_attempts']} |"
            )
        lines.append("")
        for arm_name in (null_arm, probe_arm):
            arm = task["arms"][arm_name]
            for attempt in arm["attempts"]:
                status = "usable" if attempt["usable"] else attempt["exclusion_reason"]
                wall = _format_number(attempt["wall_time_seconds"])
                if attempt["wall_time_censored"]:
                    wall = f">={wall} (censored)"
                paths = (
                    ", ".join(f"`{path}`" for path in attempt["changed_paths"])
                    if attempt["changed_paths"]
                    else "none" if attempt["changed_paths"] == [] else "unavailable"
                )
                lines.append(
                    f"- `{arm_name}` attempt {attempt['ordinal']}: {status}; "
                    f"token={_format_number(attempt['primary_token_cost'])}; wall={wall}; "
                    f"trajectory={_format_number(attempt['trajectory_length'])}; "
                    f"resolved={attempt['resolved']}; checks={_checker_brief(attempt['checker'])}; "
                    f"paths={paths}; "
                    f"tools={_compress_categories(attempt['ordered_tool_call_categories'])}."
                )
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def _stage(path: Path, data: bytes) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor: int | None = None
    temporary_path: Path | None = None
    try:
        descriptor, temporary_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
        temporary_path = Path(temporary_name)
        stream = os.fdopen(descriptor, "wb")
        descriptor = None
        with stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
    except OSError as exc:
        if descriptor is not None:
            try:
                os.close(descriptor)
            except OSError:
                pass
        if temporary_path is not None:
            try:
                temporary_path.unlink()
            except FileNotFoundError:
                pass
        _fail(f"cannot stage output {path}: {type(exc).__name__}: {exc}")
    assert temporary_path is not None
    return temporary_path


def write_outputs(analysis: dict[str, Any], analysis_output: Path, summary_output: Path) -> None:
    if analysis_output.resolve() == summary_output.resolve():
        _fail("analysis and summary outputs must be different paths")
    analysis_bytes = (json.dumps(analysis, indent=2, sort_keys=True) + "\n").encode("utf-8")
    summary_bytes = render_summary(analysis).encode("utf-8")
    staged: list[Path] = []
    try:
        staged.append(_stage(analysis_output, analysis_bytes))
        staged.append(_stage(summary_output, summary_bytes))
        os.replace(staged[0], analysis_output)
        staged.pop(0)
        os.replace(staged[0], summary_output)
        staged.pop(0)
    except OSError as exc:
        _fail(f"cannot replace analysis output: {type(exc).__name__}: {exc}")
    finally:
        for path in staged:
            try:
                path.unlink()
            except FileNotFoundError:
                pass


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--batch-dir", type=Path, default=DEFAULT_BATCH_DIR)
    parser.add_argument("--analysis-output", type=Path, default=DEFAULT_ANALYSIS_OUTPUT)
    parser.add_argument("--summary-output", type=Path, default=DEFAULT_SUMMARY_OUTPUT)
    parser.add_argument("--null-arm")
    parser.add_argument("--probe-arm")
    parser.add_argument(
        "--probe-path",
        default=PROBE_ARM_PATH,
        help="request path that identifies the candidate arm",
    )
    args = parser.parse_args(argv)
    try:
        analysis = analyze_batch(
            args.batch_dir,
            null_arm=args.null_arm,
            probe_arm=args.probe_arm,
            probe_path=args.probe_path,
        )
        write_outputs(analysis, args.analysis_output, args.summary_output)
    except AnalysisError as exc:
        print(f"analysis failed: {exc}", file=sys.stderr)
        return 2
    print(json.dumps({"status": "PASS", "analysis_output": str(args.analysis_output),
                      "summary_output": str(args.summary_output)}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
