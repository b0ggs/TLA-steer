#!/usr/bin/env python3
"""Compare a completed two-arm development batch without recomputing scores."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
import sys
from fractions import Fraction
from pathlib import Path
from typing import Any

try:
    from . import taskcheck
except ImportError:  # direct script execution
    import taskcheck  # type: ignore

DISPOSITION_KEYS = {"q", "s", "label", "fidelity_note", "task_id", "attempts",
                    "retired_ancestors", "task_denominator", "arm", "runner"}
RUNNER_KEYS = {"type", "model", "reasoning_effort", "sandbox", "approval_policy",
               "subagents_enabled", "ephemeral", "network_for_agent_commands",
               "timeout_seconds", "max_parallel_runs"}


class CompareError(RuntimeError):
    """Comparison input or output violated the evidence contract."""


def _bytes(value: Any) -> bytes:
    return (taskcheck.canonical(value) + "\n").encode()


def _json(path: Path, *, canonical: bool = True) -> dict[str, Any]:
    if path.is_symlink() or not path.is_file():
        raise CompareError(f"missing or unsafe JSON: {path}")
    raw = path.read_bytes()
    try:
        value = json.loads(raw)
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise CompareError(f"malformed JSON: {path}") from exc
    if not isinstance(value, dict) or (canonical and raw != _bytes(value)):
        raise CompareError(f"noncanonical JSON object: {path}")
    return value


def _sha_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _sha(value: Any) -> bool:
    return isinstance(value, str) and bool(re.fullmatch(r"[0-9a-f]{64}", value))


def _runner(value: Any) -> bool:
    return (isinstance(value, dict) and set(value) == RUNNER_KEYS
            and value["type"] == "codex-cli" and value["sandbox"] == "workspace-write"
            and value["approval_policy"] == "never" and value["subagents_enabled"] is False
            and value["ephemeral"] is True and value["network_for_agent_commands"] is False
            and all(isinstance(value[key], str) and value[key]
                    for key in ("model", "reasoning_effort"))
            and isinstance(value["timeout_seconds"], int)
            and not isinstance(value["timeout_seconds"], bool)
            and value["timeout_seconds"] > 0 and value["max_parallel_runs"] == 1
            and not isinstance(value["max_parallel_runs"], bool))


def _request(batch: Path) -> dict[str, Any]:
    path = batch / "REQUEST.json"
    request = _json(path)
    approval = _json(batch / "APPROVED.json", canonical=False)
    try:
        taskcheck._validate_batch_request(request, batch.name, {2})
    except taskcheck.TaskError as exc:
        raise CompareError("REQUEST/APPROVED binding is invalid") from exc
    if (set(approval) != {"request_sha256"} or approval["request_sha256"] != _sha_file(path)
            or not _runner(request.get("runner"))):
        raise CompareError("REQUEST/APPROVED binding is invalid")
    return request


def _disposition_anchors(batch: Path) -> tuple[dict[str, str], str]:
    rows = taskcheck._read_chain(batch / "evidence-ledger.jsonl", "evidence ledger", required=True)
    anchors: dict[str, str] = {}
    attempts: set[str] = set()
    for number, row in enumerate(rows, 1):
        if "type" not in row:
            attempt = row.get("attempt")
            parts = attempt.split("/") if isinstance(attempt, str) else []
            if (set(row) != {"attempt", "manifest_sha256", "prev_sha256"} or len(parts) != 3
                    or not all(taskcheck.TASK_ID.fullmatch(part) for part in parts[:2])
                    or not re.fullmatch(r"attempt-[1-9][0-9]*", parts[2])
                    or not _sha(row.get("manifest_sha256")) or attempt in attempts):
                raise CompareError(f"invalid attempt ledger row {number}")
            attempts.add(attempt)
            continue
        key = f"{row.get('task_id')}/{row.get('arm')}"
        if (set(row) != {"type", "task_id", "arm", "sha256", "prev_sha256"}
                or row.get("type") != "disposition"
                or not taskcheck.TASK_ID.fullmatch(str(row.get("task_id", "")))
                or not taskcheck.TASK_ID.fullmatch(str(row.get("arm", "")))
                or not re.fullmatch(r"[0-9a-f]{64}", str(row.get("sha256", ""))) or key in anchors):
            raise CompareError(f"invalid disposition ledger row {number}")
        anchors[key] = row["sha256"]
    head = hashlib.sha256(taskcheck.canonical(rows[-1]).encode()).hexdigest() if rows else "GENESIS"
    return anchors, head


def _load_dispositions(batch: Path, request: dict[str, Any],
                       anchors: dict[str, str]) -> dict[str, dict[str, Any]]:
    expected = {f"{task['id']}/{arm['name']}" for task in request["tasks"] for arm in request["arms"]}
    files = {path.parent.relative_to(batch).as_posix(): path for path in batch.rglob("disposition.json")}
    if set(anchors) != expected or set(files) != expected:
        raise CompareError("disposition evidence set differs from request")
    values = {}
    for key, path in files.items():
        value = _json(path)
        task_id, arm = key.split("/")
        if (_sha_file(path) != anchors[key] or set(value) != DISPOSITION_KEYS
                or value.get("task_id") != task_id or value.get("arm") != arm
                or value.get("runner") != request["runner"]
                or value.get("label") not in {"invalid", "wrong-failure-mode", "promising", "ceiling", "floor"}
                or isinstance(value.get("s"), bool) or value.get("s") not in {0, 1, 2, 3}
                or not isinstance(value.get("attempts"), list)):
            raise CompareError(f"invalid or mismatched disposition: {key}")
        values[key] = value
    return values


def _sign_test(wins_a: int, wins_b: int) -> Fraction:
    count = wins_a + wins_b
    if not count:
        return Fraction(1)
    tail = sum(math.comb(count, index) for index in range(max(wins_a, wins_b), count + 1))
    return min(Fraction(1), Fraction(2 * tail, 2 ** count))


def _write(path: Path, data: bytes) -> None:
    if path.exists():
        if path.read_bytes() != data:
            raise CompareError(f"existing output differs: {path}")
        return
    try:
        with path.open("xb") as stream:
            stream.write(data)
    except BaseException:
        path.unlink(missing_ok=True)
        raise


def _report(verdict: dict[str, Any]) -> str:
    lines = ["# Development-only two-arm comparison", "",
             "This result cannot support an incumbent or candidate replacement decision.", "",
             f"- Verdict: **{verdict['verdict']}**", f"- Batch: `{verdict['batch_id']}`",
             f"- Effective non-ties: {verdict['n_effective']}",
             f"- Effect (B-A): {verdict['effect']['exact']} ({verdict['effect']['value']:.6f})",
             f"- Exact two-sided sign p: {verdict['p_value']['exact']}",
             f"- Alpha: {verdict['thresholds']['alpha']}",
             f"- Effect threshold: {verdict['thresholds']['effect']}",
             f"- Minimum effective non-ties: {verdict['thresholds']['min_effective']}",
             f"- Excluded tasks: {', '.join(verdict['excluded_tasks']) or 'none'}",
             f"- Unbalanced tasks: {', '.join(verdict['unbalanced_tasks']) or 'none'}",
             f"- Evidence ledger head: `{verdict['evidence_ledger_head']}`", "",
             "## Arms", ""]
    lines.extend(f"- `{arm['name']}`: `{arm['sha256']}`" for arm in verdict["arms"])
    lines.extend(["", "## Tasks", ""])
    lines.extend(f"- `{row['task_id']}`: {row.get('delta', 'excluded')} ({row.get('reason', 'included')})"
                 for row in verdict["tasks"])
    lines.extend(["", "## Runner", "", "```json", taskcheck.canonical(verdict["runner"]), "```"])
    if verdict.get("integrity_error"):
        lines.extend(["", f"Integrity error: {verdict['integrity_error']}"])
    return "\n".join(lines) + "\n"


def compare_batch(batch: Path, *, alpha: str = "0.05", threshold: str = "0.20",
                  min_effective: int = 6) -> dict[str, Any]:
    batch = batch.resolve()
    request = _request(batch)
    if len(request["tasks"]) > 24 or min_effective < 1:
        raise CompareError("task enumeration or min-effective is invalid")
    alpha_value, threshold_value = Fraction(alpha), Fraction(threshold)
    if not 0 < alpha_value <= 1 or not 0 <= threshold_value <= 1:
        raise CompareError("alpha/threshold is invalid")
    integrity_error = ""
    try:
        anchors, head = _disposition_anchors(batch)
    except (CompareError, taskcheck.TaskError) as exc:
        anchors, head, integrity_error = {}, "UNVERIFIED", str(exc)
    if not integrity_error:
        try:
            dispositions = _load_dispositions(batch, request, anchors)
        except (CompareError, taskcheck.TaskError) as exc:
            dispositions, integrity_error = {}, str(exc)
    else:
        dispositions = {}
    arm_a, arm_b = request["arms"]
    task_rows, excluded, deltas = [], [], []
    if integrity_error:
        excluded = [task["id"] for task in request["tasks"]]
        task_rows = [{"task_id": task_id, "reason": "integrity failure"} for task_id in excluded]
    else:
        for task in request["tasks"]:
            left = dispositions[f"{task['id']}/{arm_a['name']}"]
            right = dispositions[f"{task['id']}/{arm_b['name']}"]
            reason = ("invalid disposition" if "invalid" in {left["label"], right["label"]}
                      else "unequal usable counts" if len(left["attempts"]) != len(right["attempts"]) else "")
            if reason:
                excluded.append(task["id"])
                task_rows.append({"task_id": task["id"], "reason": reason})
            else:
                delta = right["s"] - left["s"]
                deltas.append(delta)
                task_rows.append({"task_id": task["id"], "s_A": left["s"], "s_B": right["s"],
                                  "delta": delta, "reason": "included"})
    wins_a, wins_b = sum(item < 0 for item in deltas), sum(item > 0 for item in deltas)
    p_value = _sign_test(wins_a, wins_b)
    effect = Fraction(sum(deltas), 3 * len(deltas)) if deltas else Fraction(0)
    invalid = bool(integrity_error) or len(excluded) * 4 > len(request["tasks"])
    verdict = "INVALID" if invalid else "INCONCLUSIVE"
    if not invalid and wins_a + wins_b >= min_effective and p_value <= alpha_value:
        if effect >= threshold_value:
            verdict = "B_BETTER"
        elif effect <= -threshold_value:
            verdict = "A_BETTER"
    result = {"schema": "task-comparison-v1", "development_only": True,
              "batch_id": request["batch_id"], "arms": request["arms"],
              "evidence_ledger_head": head, "runner": request["runner"],
              "thresholds": {"alpha": alpha, "effect": threshold, "min_effective": min_effective},
              "tasks": task_rows, "excluded_tasks": excluded, "unbalanced_tasks": [
                  row["task_id"] for row in task_rows if row.get("reason") == "unequal usable counts"],
              "n_effective": wins_a + wins_b, "included_tasks": len(deltas),
              "wins_A": wins_a, "wins_B": wins_b,
              "p_value": {"exact": str(p_value), "value": float(p_value)},
              "effect": {"exact": str(effect), "value": float(effect)},
              "integrity_error": integrity_error or None, "verdict": verdict}
    _write(batch / "verdict.json", _bytes(result))
    _write(batch / "report.md", _report(result).encode())
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("batch", type=Path)
    parser.add_argument("--alpha", default="0.05")
    parser.add_argument("--threshold", default="0.20")
    parser.add_argument("--min-effective", type=int, default=6)
    args = parser.parse_args(argv)
    try:
        print(taskcheck.canonical(compare_batch(
            args.batch, alpha=args.alpha, threshold=args.threshold, min_effective=args.min_effective)))
        return 0
    except (CompareError, taskcheck.TaskError, ValueError, ZeroDivisionError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
