#!/usr/bin/env python3
"""Mechanical treatment-fidelity and Section 12 pilot outcome coding."""

from __future__ import annotations

import argparse
import json
import re
import shlex
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

import run_batch  # noqa: E402


REAL_COMMAND = re.compile(
    r"(?:^|&&|\|\||;|\n)\s*(?:[A-Z_][A-Z0-9_]*=\S+\s+)*"
    r"python3?\s+tools/verify\.py\s*(?=$|&&|\|\||;|\n)")
GENERATED = "signalnest/generated_routes.py"
SOURCE = "catalog/routes.json"


def read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"not a JSON object: {path}")
    return value


def fidelity(mechanism_path: Path, md_path: Path) -> dict[str, Any]:
    mechanism = read_json(mechanism_path)
    md = md_path.read_text(encoding="utf-8")
    facts = []
    missing_total = []
    for fact in mechanism["facts"]:
        missing = [text for text in fact["required_md_substrings"] if text not in md]
        facts.append({"fact": fact["fact"], "missing": missing})
        missing_total.extend(missing)
    return {"status": "TREATMENT_UNFAITHFUL" if missing_total else "TREATMENT_FAITHFUL",
            "facts": facts, "missing_count": len(missing_total)}


def event_evidence(path: Path) -> tuple[bool, dict[str, Any]]:
    commands, usage = [], {}
    for line in path.read_text(encoding="utf-8").splitlines():
        row = json.loads(line)
        item = row.get("item", {}) if isinstance(row, dict) else {}
        if item.get("type") == "command_execution" and isinstance(item.get("command"), str):
            commands.append(item["command"])
        if row.get("type") == "turn.completed" and isinstance(row.get("usage"), dict):
            usage = row["usage"]
    scripts = list(commands)
    for command in commands:
        try:
            parts = shlex.split(command)
        except ValueError:
            continue
        scripts.extend(parts[index + 1] for index, part in enumerate(parts[:-1]) if part == "-lc")
    return any(REAL_COMMAND.search(command) for command in scripts), usage


def changed_paths(path: Path) -> set[str]:
    text = path.read_text(encoding="utf-8")
    return {match.group(2) for match in re.finditer(
        r"^diff --git a/(.+) b/(.+)$", text, flags=re.MULTILINE)}


def attempt_row(path: Path) -> dict[str, Any]:
    result = read_json(path / "result.json")
    ran_real, usage = event_evidence(path / "events.jsonl")
    changed = changed_paths(path / "diff.patch")
    wrong_layer = GENERATED in changed and SOURCE not in changed
    resolved = result.get("resolved") is True
    return {"ordinal": result.get("ordinal"), "resolved": resolved,
            "ran_real": ran_real, "wrong_layer": wrong_layer,
            "stumble": not resolved or not ran_real or wrong_layer,
            "duration_seconds": result.get("duration_seconds"),
            "checker_duration_seconds": result.get("checker_duration_seconds"),
            "usage": usage, "valid": result.get("valid") is True}


def code_outcome(batch: Path) -> dict[str, Any]:
    invalid_reasons = []
    try:
        run_batch.verify_batch(batch)
    except Exception as exc:  # verification failure is outcome evidence
        invalid_reasons.append(f"batch verify failed: {exc}")
    try:
        request = read_json(batch / "REQUEST.json")
        task_id = request["tasks"][0]["id"]
        if len(request["tasks"]) != 1 or [row["name"] for row in request["arms"]] != ["bare", "md"]:
            invalid_reasons.append("request is not the one-task bare/md pilot")
        arms: dict[str, list[dict[str, Any]]] = {}
        for arm in ("bare", "md"):
            base = batch / task_id / arm
            attempts = sorted(base.glob("attempt-*"), key=lambda item: int(item.name.split("-")[-1]))
            if any((path / "infra-invalid.json").exists() for path in attempts):
                invalid_reasons.append(f"{arm} contains an invalid attempt")
            rows = [attempt_row(path) for path in attempts if (path / "result.json").is_file()]
            if len(rows) != 3 or not all(row["valid"] for row in rows):
                invalid_reasons.append(f"{arm} lacks exactly three valid attempts")
            arms[arm] = rows
    except Exception as exc:
        invalid_reasons.append(f"evidence parse failed: {exc}")
        arms = {"bare": [], "md": []}
    scores = {arm: sum(row["resolved"] for row in rows) for arm, rows in arms.items()}
    bare_stumbles = sum(row["stumble"] for row in arms["bare"])
    md_mechanism = sum(row["resolved"] and row["ran_real"] and not row["wrong_layer"]
                       for row in arms["md"])
    if invalid_reasons:
        label = "EVIDENCE_INVALID"
    elif bare_stumbles >= 2 and md_mechanism >= 2:
        label = "MECHANISM_SIGNAL"
    elif scores["md"] < scores["bare"]:
        label = "MD_WORSE"
    else:
        label = "MECHANISM_NOT_SHOWN_IN_PILOT"
    return {"label": label, "task_id": locals().get("task_id"), "scores": scores,
            "delta": scores["md"] - scores["bare"], "bare_stumbles": bare_stumbles,
            "md_mechanism_attempts": md_mechanism, "attempts": arms,
            "invalid_reasons": invalid_reasons}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    check = commands.add_parser("fidelity")
    check.add_argument("mechanism", type=Path)
    check.add_argument("md", type=Path)
    outcome = commands.add_parser("outcome")
    outcome.add_argument("batch", type=Path)
    args = parser.parse_args()
    result = fidelity(args.mechanism, args.md) if args.command == "fidelity" else code_outcome(args.batch)
    print(json.dumps(result, sort_keys=True, separators=(",", ":")))
    return int(result.get("status") == "TREATMENT_UNFAITHFUL")


if __name__ == "__main__":
    raise SystemExit(main())
