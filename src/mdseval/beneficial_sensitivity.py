"""Bounded Milestone 2 beneficial-sensitivity orchestration and replay."""
from __future__ import annotations

import argparse
import hashlib
import json
import random
import shutil
import sys
import tempfile
from concurrent.futures import ThreadPoolExecutor
from collections import Counter
from fractions import Fraction
from functools import lru_cache
from pathlib import Path, PurePosixPath
from typing import Any, Iterable, Sequence

from .capture import Redactor, capture_git, parse_event_stream, write_json
from .config import RunnerConfig
from .fixtures import audit_final_subject_tree, prepare_fixture
from .gitutils import safe_process_environment
from .hashing import sha256_file, tree_sha256
from .processutils import run_process_group
from .wrapper import WRAPPER_PROMPT

DEFAULT_EXPERIMENT = Path("experiments/coder-beneficial-sensitivity-m2.json")
TASK_ID = tuple(f"{kind}-{number:02d}" for kind in ("bug", "feature", "integration", "refactor-data") for number in range(1, 6))
STRATA = ("bug", "feature", "integration", "refactor-data")
STAGES = ("smoke", "calibration", "controls", "helpful")
GRID = ((.20, .50, .8726), (.25, .55, .8589), (.30, .60, .8482), (.40, .70, .8468), (.50, .80, .8730), (.60, .90, .9184), (.65, .95, .9445))
SHA = "0123456789abcdef"


def _canonical(value: object) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False) + "\n").encode()


def _exact_keys(value: Any, keys: Iterable[str], label: str) -> dict[str, Any]:
    if not isinstance(value, dict) or set(value) != set(keys):
        raise ValueError(f"{label} keys are not the frozen schema")
    return value


def _safe(root: Path, relative: Any, label: str) -> Path:
    if not isinstance(relative, str):
        raise ValueError(f"{label} must be a string")
    pure = PurePosixPath(relative)
    if pure.is_absolute() or not pure.parts or ".." in pure.parts or any(part in {"", "."} for part in pure.parts):
        raise ValueError(f"unsafe {label}")
    path = (root / pure).resolve()
    try:
        path.relative_to(root.resolve())
    except ValueError as exc:
        raise ValueError(f"{label} escapes repository") from exc
    return path


def _hash(path: Path) -> str:
    if path.is_symlink() or not path.is_file():
        raise ValueError(f"missing or unsafe file: {path}")
    return sha256_file(path)


def load_design(path: str | Path = DEFAULT_EXPERIMENT, repository_root: Path | None = None) -> dict[str, Any]:
    path = Path(path).resolve()
    root = (repository_root or path.parent.parent).resolve()
    value = json.loads(path.read_text(encoding="utf-8"))
    keys = {"schema", "experiment", "protocol_version", "authorities", "runtime", "treatments", "artifacts", "seeds", "analysis", "calls", "invalidity", "evidence", "smoke", "schedules"}
    design = _exact_keys(value, keys, "design")
    if design["schema"] != "mdseval.coder-beneficial-sensitivity-m2-v1" or design["experiment"] != "coder-beneficial-sensitivity-m2" or design["protocol_version"] != "0.2":
        raise ValueError("experiment identity mismatch")
    runtime = _exact_keys(design["runtime"], {"model", "reasoning_effort", "sandbox", "approval_policy", "subagents_enabled", "ephemeral", "network_for_agent_commands", "timeout_seconds", "max_parallel_runs", "qualitative_judge_calls"}, "runtime")
    if runtime != {"model": "gpt-5.6-sol", "reasoning_effort": "high", "sandbox": "workspace-write", "approval_policy": "never", "subagents_enabled": False, "ephemeral": True, "network_for_agent_commands": False, "timeout_seconds": 300, "max_parallel_runs": 1, "qualitative_judge_calls": 0}:
        raise ValueError("strict Sol/high runtime mismatch")
    expected_calls = {"smoke": 1, "calibration": 120, "controls": 48, "helpful": 128, "base_cap": 297, "fallback_cap": 17, "absolute_cap": 314}
    if design["calls"] != expected_calls:
        raise ValueError("call ceilings mismatch")
    if design["seeds"] != {"selection": "coder-m2-selection-20260810-v1", "schedule": "coder-m2-schedule-20260810-v1", "grid": 20260810, "post_calibration_power": 20260811, "bootstrap": 20260812}:
        raise ValueError("seed mismatch")
    analysis = design["analysis"]
    if analysis != {"alpha": [1, 20], "effect_floor": [1, 5], "helpful_minimum": [13, 64], "simulations": 100000, "bootstrap_samples": 100000, "bootstrap_endpoints": [2499, 97500], "power_floor": [4, 5]}:
        raise ValueError("analysis mismatch")
    if design["invalidity"] != {"replaceable": ["evaluator_failure_before_usable_turn", "machine_failure_before_usable_turn", "authentication_failure_before_usable_turn", "service_failure_before_usable_turn"], "score_zero": ["timeout", "false_completion", "missing_deliverables", "agent_caused_failure", "post_usable_nonzero_exit", "failed_checks"], "first_block": "supersede_whole_task_stage_and_run_frozen_fallback_at_stage_end", "second_block": "INVALID", "invalid_replacement": "INVALID", "smoke_retry": False}:
        raise ValueError("invalidity table mismatch")
    if design["evidence"] != {"live_root": "runs/<instance-id>/live", "replay_root": "runs/<instance-id>/replay", "create_once": True, "workspace_snapshot": False, "block_receipts": False, "ledger": False}:
        raise ValueError("evidence design mismatch")
    if design["smoke"] != {"treatment": "null", "contract": "IMPLEMENTED\\nSMOKE_READY", "changes_allowed": False, "retry": False}:
        raise ValueError("smoke design mismatch")
    required = {**design["authorities"], **design["artifacts"]}
    for relative, expected in required.items():
        if len(expected) != 64 or any(c not in SHA for c in expected) or _hash(_safe(root, relative, "bound path")) != expected:
            raise ValueError(f"hash drift: {relative}")
    treatments = _exact_keys(design["treatments"], {"null", "harmful", "helpful"}, "treatments")
    for item in treatments.values():
        _exact_keys(item, {"path", "sha256"}, "treatment")
        if _hash(_safe(root, item["path"], "treatment path")) != item["sha256"]:
            raise ValueError("treatment drift")
    if treatments["null"]["sha256"] != hashlib.sha256(b"").hexdigest() or _safe(root, treatments["null"]["path"], "null").read_bytes():
        raise ValueError("null treatment is not zero bytes")
    helpful = _safe(root, treatments["helpful"]["path"], "helpful")
    text = helpful.read_text(encoding="utf-8")
    if len(helpful.read_bytes()) > 4096 or len(text.split()) > 250:
        raise ValueError("helpful treatment size mismatch")
    master = json.loads(_safe(root, "evals/m2/coder-beneficial-sensitivity/master.json", "master").read_text())
    if master.get("task_ids") != list(TASK_ID) or set(master.get("strata", {})) != set(STRATA) or len(master.get("tasks", [])) != 20:
        raise ValueError("task master balance mismatch")
    for item in master["tasks"]:
        if item.get("id") not in TASK_ID or item.get("stratum") not in STRATA:
            raise ValueError("unsafe task metadata")
        directory = _safe(root, item["path"], "task path")
        task_data = json.loads((directory / "task.json").read_text())
        for name, field in (("task.json", "task_json_sha256"), ("contract.md", "contract_sha256"), ("check.py", "checker_sha256")):
            if _hash(directory / name) != item[field]:
                raise ValueError(f"task hash drift: {item['id']}")
        files = task_data.get("fixture_files", [])
        if hashlib.sha256(json.dumps(files, sort_keys=True, separators=(",", ":")).encode()).hexdigest() != item["fixture_sha256"]:
            raise ValueError(f"fixture drift: {item['id']}")
        for entry in files:
            target = _safe(directory / "fixture", entry.get("path"), "fixture file")
            if entry.get("mode") != "100644" or _hash(target) != entry.get("sha256"):
                raise ValueError(f"fixture file drift: {item['id']}")
    validation = json.loads(_safe(root, "evals/qualification/coder-beneficial-sensitivity-m2/validation.json", "validation").read_text())
    design["root"], design["path"], design["master"], design["blockers"] = root, path, master, tuple(validation.get("blockers", ()))
    schedules = build_schedules(design)
    if design["schedules"] != schedules["sentinels"]:
        raise ValueError("schedule sentinel mismatch")
    return design


def _digest(design: dict[str, Any], stage: str, round_id: int, task: str, tail: str) -> str:
    return hashlib.sha256(f"{design['seeds']['schedule']}|{stage}|{round_id}|{task}|{tail}".encode()).hexdigest()


def build_schedules(design: dict[str, Any]) -> dict[str, Any]:
    arms = {"calibration": ("O0",), "controls": ("O1", "O2", "O3"), "helpful": ("O4", "O5")}
    rounds = {"calibration": 6, "controls": 1, "helpful": 4}
    result: dict[str, Any] = {"sentinels": {}, "base": {}, "fallback": {}}
    for stage in arms:
        base: list[dict[str, Any]] = []
        for round_id in range(1, rounds[stage] + 1):
            ordered = sorted(TASK_ID, key=lambda task: _digest(design, stage, round_id, task, "BLOCK"))
            for task in ordered:
                arm_order = sorted(arms[stage], key=lambda arm: _digest(design, stage, round_id, task, f"{arm}|ARM"))
                for arm in arm_order:
                    base.append({"stage": stage, "round": round_id, "task_id": task, "opaque_arm_id": arm, "slot_id": f"{stage}:{round_id}:{task}:{arm}:base"})
        fallback = [{**row, "slot_id": row["slot_id"].removesuffix("base") + "fallback"} for row in base]
        blocks = {}
        for task in TASK_ID:
            ids = [row["slot_id"] for row in base + fallback if row["task_id"] == task]
            blocks[task] = hashlib.sha256("\n".join(ids).encode()).hexdigest()
        ordered_blocks = sorted(TASK_ID, key=lambda task: _digest(design, stage, 0, task, "BLOCK"))
        result["base"][stage], result["fallback"][stage] = base, fallback
        result["sentinels"][stage] = {"blocks": blocks, "stage": hashlib.sha256("\n".join(blocks[t] for t in ordered_blocks).encode()).hexdigest()}
    return result


def filtered_schedule(design: dict[str, Any], stage: str, selected: Iterable[str]) -> dict[str, Any]:
    selected_ids = tuple(sorted(selected))
    if stage not in {"controls", "helpful"} or len(selected_ids) != 16 or any(selected_ids.count(t) != 1 for t in selected_ids):
        raise ValueError("filtered schedule requires 16 unique selected tasks")
    rows = [row for row in build_schedules(design)["base"][stage] if row["task_id"] in selected_ids]
    return {"selected_ids": list(selected_ids), "source_stage_sentinel": design["schedules"][stage]["stage"], "slots": rows, "sha256": hashlib.sha256(_canonical(rows)).hexdigest()}


def select_tasks(design: dict[str, Any], successes: dict[str, int]) -> dict[str, Any]:
    if set(successes) != set(TASK_ID) or any(type(n) is not int or not 0 <= n <= 6 for n in successes.values()):
        raise ValueError("calibration counts must cover all 20 tasks")
    rows, selected = [], []
    strata = design["master"]["strata"]
    for stratum in STRATA:
        ranked = sorted(strata[stratum], key=lambda task: (abs(successes[task] - 3), hashlib.sha256((design["seeds"]["selection"] + task).encode()).hexdigest()))
        eligible = [task for task in ranked if 1 <= successes[task] <= 5]
        rows.extend({"task_id": task, "stratum": stratum, "successes": successes[task], "eligible": task in eligible, "rank": eligible.index(task) + 1 if task in eligible else None} for task in ranked)
        if len(eligible) < 4:
            return {"status": "SENSITIVITY_NOT_DEMONSTRATED", "selected_ids": [], "tasks": rows}
        selected.extend(eligible[:4])
    return {"status": "SELECTED", "selected_ids": sorted(selected), "tasks": rows}


def exact_sign_test(differences: Sequence[Fraction]) -> dict[str, Any]:
    values = tuple(value for value in differences if value)
    denominator = 1
    for value in values:
        denominator = denominator * value.denominator // __import__("math").gcd(denominator, value.denominator)
    integers = tuple(abs(value.numerator * (denominator // value.denominator)) for value in values)
    observed = abs(sum(value.numerator * (denominator // value.denominator) for value in values))
    extreme, assignments = _integer_sign(tuple(sorted(integers)), observed)
    probability = Fraction(extreme, assignments)
    return {"nonzero": len(values), "extreme": extreme, "assignments": assignments, "fraction": [probability.numerator, probability.denominator], "p": float(probability)}


@lru_cache(maxsize=None)
def _integer_sign(integers: tuple[int, ...], observed: int) -> tuple[int, int]:
    counts: Counter[int] = Counter({0: 1})
    for magnitude in integers:
        next_counts: Counter[int] = Counter()
        for total, count in counts.items():
            next_counts[total - magnitude] += count
            next_counts[total + magnitude] += count
        counts = next_counts
    return sum(count for total, count in counts.items() if abs(total) >= observed), 1 << len(integers)


def compare(a: dict[str, Sequence[bool]], b: dict[str, Sequence[bool]]) -> dict[str, Any]:
    tasks = tuple(sorted(a))
    if tasks != tuple(sorted(b)) or not tasks or any(not a[t] or not b[t] for t in tasks):
        raise ValueError("comparison arms must be balanced by task")
    differences = [Fraction(sum(a[t]), len(a[t])) - Fraction(sum(b[t]), len(b[t])) for t in tasks]
    effect = sum(differences, Fraction()) / len(tasks)
    exact = exact_sign_test(differences)
    return {"tasks": [{"task_id": task, "d": [d.numerator, d.denominator]} for task, d in zip(tasks, differences)], "effect": [effect.numerator, effect.denominator], "effect_value": float(effect), "exact": exact, "passes": effect >= Fraction(1, 5) and exact["p"] <= .05}


def stratified_bootstrap(rows: dict[str, Fraction], strata: dict[str, Sequence[str]], samples: int = 100000) -> list[float]:
    rng, values = random.Random(20260812), []
    for _ in range(samples):
        draw = [rows[rng.choice(tuple(strata[name]))] for name in STRATA for _ in range(4)]
        values.append(float(sum(draw, Fraction()) / 16))
    values.sort()
    return [values[2499], values[97500]]


@lru_cache(maxsize=10000)
def _gate_from_units(units: tuple[int, ...]) -> bool:
    if sum(units) < 13:
        return False
    magnitudes = tuple(sorted(abs(value) for value in units if value))
    extreme, assignments = _integer_sign(magnitudes, abs(sum(units)))
    return extreme * 20 <= assignments


def classify_failure(design: dict[str, Any], code: str, usable_turn: bool) -> str:
    replaceable = {item.removesuffix("_before_usable_turn") for item in design["invalidity"]["replaceable"]}
    return "REPLACE_BLOCK" if not usable_turn and code in replaceable else "Y_ZERO"


def retry_decision(stage: str, invalid_blocks: int, replacement_invalid: bool = False) -> str:
    if stage == "smoke" or replacement_invalid or invalid_blocks > 1:
        return "INVALID"
    return "FROZEN_FALLBACK_AT_STAGE_END" if invalid_blocks == 1 else "CONTINUE"


def resume_boundary(stage: str, completed_slots: int) -> bool:
    unit = {"calibration": 1, "controls": 3, "helpful": 2}.get(stage)
    return bool(unit and completed_slots >= 0 and completed_slots % unit == 0)


def runtime_matches(requested: dict[str, str], observed: dict[str, str]) -> bool:
    return all(requested.get(key) == observed.get(key) and bool(observed.get(key)) for key in ("model", "reasoning_effort"))


def service_metadata(events: Sequence[dict[str, Any]]) -> dict[str, str]:
    found: dict[str, str] = {}
    def visit(value: Any) -> None:
        if isinstance(value, dict):
            for key, item in value.items():
                normalized = "reasoning_effort" if key in {"reasoning_effort", "model_reasoning_effort"} else key
                if normalized in {"model", "reasoning_effort"} and isinstance(item, str): found.setdefault(normalized, item)
                else: visit(item)
        elif isinstance(value, list):
            for item in value: visit(item)
    visit(list(events)); return found


def smoke_passes(result: Any, final: str, changed_paths: Sequence[str], capture_complete: bool, requested: dict[str, str], observed: dict[str, str]) -> bool:
    return bool(result.exit_code == 0 and not result.timed_out and not result.interrupted and final == "IMPLEMENTED\nSMOKE_READY" and not changed_paths and capture_complete and runtime_matches(requested, observed))


def simulate_power(rates: Sequence[tuple[float, float]], seed: int, simulations: int = 100000, rng: random.Random | None = None) -> float:
    source, passed = rng or random.Random(seed), 0
    for _ in range(simulations):
        units = tuple(sum(source.random() < helpful for _ in range(4)) - sum(source.random() < null for _ in range(4)) for null, helpful in rates)
        passed += _gate_from_units(units)
    return passed / simulations


def verify_power(design: dict[str, Any], simulations: int | None = None) -> dict[str, Any]:
    count = simulations or design["analysis"]["simulations"]
    rng, rows = random.Random(design["seeds"]["grid"]), []
    for null, helpful, expected in GRID:
        observed = simulate_power(((null, helpful),) * 16, 0, count, rng)
        rows.append({"null": null, "helpful": helpful, "expected": expected, "observed": observed, "passed": abs(observed - expected) <= .005})
    return {"simulations": count, "rows": rows, "passed": all(row["passed"] for row in rows)}


def post_calibration_power(design: dict[str, Any], successes: dict[str, int], selected: Sequence[str]) -> float:
    rates = tuple(((successes[t] + 1) / 8, min(1.0, (successes[t] + 1) / 8 + .30)) for t in sorted(selected))
    return simulate_power(rates, design["seeds"]["post_calibration_power"], design["analysis"]["simulations"])


def objective_resolved(payload: Any) -> bool:
    if not isinstance(payload, dict) or payload.get("resolved") is not True:
        return False
    if any(not isinstance(payload.get(name), dict) or payload[name].get("passed") is not True for name in ("environment", "integrity")):
        return False
    return all(isinstance(payload.get(name), dict) and payload[name] and all(isinstance(item, dict) and item.get("passed") is True for item in payload[name].values()) for name in ("requirements", "regressions"))


def _checker(checker: Path, workspace: Path, timeout: int = 300) -> dict[str, Any]:
    process = run_process_group([str(Path(sys.executable).resolve()), str(checker), str(workspace)], cwd=checker.parent, input_text=None, timeout=timeout, environment=safe_process_environment())
    try:
        payload = json.loads(process.stdout)
    except json.JSONDecodeError:
        payload = {}
    return {"valid": process.returncode == 0 and not process.timed_out and not process.interrupted and isinstance(payload, dict), "payload": payload, "stdout": process.stdout, "stderr": process.stderr, "exit_code": process.returncode}


def qualify(design: dict[str, Any], output: Path) -> dict[str, Any]:
    output.mkdir(parents=True, exist_ok=False)
    task_root = _safe(design["root"], "evals/m2/coder-beneficial-sensitivity", "task root"); start_tree = tree_sha256(task_root)
    oracle = json.loads(_safe(design["root"], "evals/qualification/coder-beneficial-sensitivity-m2/oracle-variants.json", "oracle").read_text())
    specs: list[tuple[str, dict[str, Any], int, Path, Path]] = []
    with tempfile.TemporaryDirectory(prefix="mdseval-m2-qualification-") as temporary:
        temp = Path(temporary)
        for task in TASK_ID:
            directory = _safe(design["root"], f"evals/m2/coder-beneficial-sensitivity/{task}", "task")
            states = [{"id": "pristine", "class": "pristine", "files": {}, "remove": []}, *oracle["tasks"][task]]
            for state in states:
                for repeat in range(1, 4):
                    workspace = temp / task / state["id"] / str(repeat)
                    shutil.copytree(directory / "fixture", workspace)
                    for relative, content in state.get("files", {}).items():
                        target = _safe(workspace, relative, "oracle file"); target.parent.mkdir(parents=True, exist_ok=True); target.write_text(content, encoding="utf-8")
                    for relative in state.get("remove", []):
                        _safe(workspace, relative, "oracle removal").unlink()
                    specs.append((task, state, repeat, directory / "check.py", workspace))
        with ThreadPoolExecutor(max_workers=16) as pool:
            checked = list(pool.map(lambda spec: _checker(spec[3], spec[4]), specs))
        rows = []
        for offset in range(0, len(specs), 3):
            task, state = specs[offset][:2]
            outcomes = [item["valid"] and objective_resolved(item["payload"]) for item in checked[offset:offset + 3]]
            expected = state["class"] == "correct"
            rows.append({"task_id": task, "state": state["id"], "class": state["class"], "outcomes": outcomes, "passed": outcomes == [expected] * 3})
    end_tree = tree_sha256(task_root)
    result = {"schema": "mdseval.coder-beneficial-sensitivity-m2-qualification-v1", "python": {"executable": str(Path(sys.executable).resolve()), "version": sys.version}, "execution_count": 300, "task_tree_sha256": start_tree, "rows": rows, "passed": len(rows) == 100 and all(row["passed"] for row in rows) and start_tree == end_tree, "validator_blockers": list(design["blockers"])}
    write_json(output / "qualification-results.json", result)
    return result


def analyze(design: dict[str, Any], evidence: dict[str, Any]) -> dict[str, Any]:
    if evidence.get("schema") != "mdseval.coder-beneficial-sensitivity-m2-evidence-v1" or evidence.get("launched_calls", 0) > 314:
        return {"verdict": "INVALID", "reason": "evidence envelope or cap"}
    calibration = evidence.get("calibration", {})
    selection = select_tasks(design, {task: sum(calibration.get(task, ())) for task in TASK_ID})
    if selection["status"] != "SELECTED":
        return {"verdict": "SENSITIVITY_NOT_DEMONSTRATED", "selection": selection}
    selected = selection["selected_ids"]
    counts = {task: sum(calibration[task]) for task in TASK_ID}
    power = post_calibration_power(design, counts, selected)
    if power < .80:
        return {"verdict": "SENSITIVITY_NOT_DEMONSTRATED", "selection": selection, "power": power}
    selected_strata = {name: [task for task in design["master"]["strata"][name] if task in selected] for name in STRATA}
    def interval(result: dict[str, Any]) -> list[float]:
        differences = {row["task_id"]: Fraction(*row["d"]) for row in result["tasks"]}
        return stratified_bootstrap(differences, selected_strata, design["analysis"]["bootstrap_samples"])
    controls, helpful = evidence.get("controls", {}), evidence.get("helpful", {})
    aa = compare({t: controls[t]["N1"] for t in selected}, {t: controls[t]["N2"] for t in selected})
    harmful = compare({t: controls[t]["N1"] for t in selected}, {t: controls[t]["H"] for t in selected})
    aa["bootstrap_95"], harmful["bootstrap_95"] = interval(aa), interval(harmful)
    if aa["passes"] or compare({t: controls[t]["N2"] for t in selected}, {t: controls[t]["N1"] for t in selected})["passes"] or not harmful["passes"]:
        return {"verdict": "SENSITIVITY_NOT_DEMONSTRATED", "selection": selection, "aa": {**aa, "gate": "NO_FALSE_WINNER" if not aa["passes"] else "FAILED"}, "harmful": harmful}
    positive = compare({t: helpful[t]["P"] for t in selected}, {t: helpful[t]["N"] for t in selected})
    positive["bootstrap_95"] = interval(positive)
    return {"verdict": "SENSITIVITY_DEMONSTRATED" if positive["passes"] else "SENSITIVITY_NOT_DEMONSTRATED", "claim_boundary": "Under the frozen diagnostic conditions, identical null files did not produce a winner, the harmful instruction lost, and the helpful instruction met the predeclared observed-effect and exact-test gates.", "selection": selection, "power": power, "aa": {**aa, "gate": "NO_FALSE_WINNER"}, "harmful": harmful, "helpful": positive, "coverage": evidence.get("coverage", {}), "secondary_metrics": evidence.get("secondary_metrics", {})}


def _fake_evidence() -> dict[str, Any]:
    calibration = {task: [True, True, True, False, False, False] for task in TASK_ID}
    controls = {task: {"N1": [True], "N2": [True], "H": [False]} for task in TASK_ID}
    helpful = {task: {"P": [True] * 4, "N": [False] * 4} for task in TASK_ID}
    return {"schema": "mdseval.coder-beneficial-sensitivity-m2-evidence-v1", "launched_calls": 297, "calibration": calibration, "controls": controls, "helpful": helpful, "invalid": [], "superseded": []}


def simulate(design: dict[str, Any], output: Path) -> dict[str, Any]:
    output.mkdir(parents=True, exist_ok=False)
    evidence, schedules = _fake_evidence(), build_schedules(design)
    report = analyze(design, evidence)
    write_json(output / "evidence.json", evidence); write_json(output / "report.json", report); write_json(output / "schedules.json", schedules)
    (output / "report.md").write_text(f"# M2 fake replay\n\nVerdict: `{report['verdict']}`\n", encoding="utf-8")
    return report


def replay(design: dict[str, Any], instance: str, repository_root: Path | None = None) -> dict[str, Any]:
    if not instance or PurePosixPath(instance).name != instance:
        raise ValueError("instance must be one safe component")
    root = (repository_root or design["root"]) / "runs" / instance
    live, output = root / "live", root / "replay"
    manifest = json.loads((live / "manifest.json").read_text())
    if manifest.get("design_sha256") != sha256_file(design["path"]) or manifest.get("schedule_sentinels") != design["schedules"]:
        raise ValueError("manifest drift")
    evidence_path = live / "evidence.json"
    if manifest.get("evidence_sha256") != sha256_file(evidence_path):
        raise ValueError("evidence tampering")
    report = analyze(design, json.loads(evidence_path.read_text()))
    output.mkdir(parents=True, exist_ok=False)
    write_json(output / "report.json", report)
    (output / "report.md").write_text(f"# CODER M2 replay\n\nVerdict: `{report['verdict']}`\n", encoding="utf-8")
    return report


def run_stage(design: dict[str, Any], instance: str, stage: str, authorization: Path) -> None:
    if design["blockers"]:
        raise RuntimeError("VALIDATION_BLOCKERS_UNRESOLVED")
    if stage not in STAGES:
        raise ValueError("invalid stage")
    receipt = json.loads(authorization.read_text())
    if receipt != {"schema": "mdseval.coder-beneficial-sensitivity-m2-authorization-v1", "experiment": design["experiment"], "instance": instance, "stage": stage, "authorized": True}:
        raise RuntimeError("STAGE_AUTHORIZATION_REQUIRED")
    # Live construction is deliberately isolated from every offline/replay path.
    from .runner.codex_cli import CodexCLI
    config = RunnerConfig("codex_cli", **{key: design["runtime"][key] for key in ("model", "reasoning_effort", "sandbox", "approval_policy", "subagents_enabled", "ephemeral", "network_for_agent_commands", "timeout_seconds", "max_parallel_runs")})
    live = design["root"] / "runs" / instance / "live"
    live.mkdir(parents=True, exist_ok=stage != "smoke")
    if stage != "smoke":
        raise RuntimeError("LIVE_STAGE_PREREQUISITES_NOT_LOCKED")
    task = argparse.Namespace(id="smoke", fixture_dir=Path(tempfile.mkdtemp(prefix="mdseval-m2-smoke-fixture-")), contract_path=None)
    try:
        (task.fixture_dir / "keep.txt").write_text("unchanged\n", encoding="utf-8")
        task.contract_path = task.fixture_dir.parent / "contract.md"; task.contract_path.write_text("Reply with exactly IMPLEMENTED\\nSMOKE_READY and make no changes.\n", encoding="utf-8")
        prepared = prepare_fixture(task, _safe(design["root"], design["treatments"]["null"]["path"], "null"), design["treatments"]["null"]["sha256"])
        artifacts = live / "attempt-smoke"; result = CodexCLI(config).run(prepared, artifacts, 300, Redactor())
        audit_final_subject_tree(prepared.repo); capture = capture_git(prepared.repo, prepared.baseline_commit, Redactor()); events = parse_event_stream(artifacts / "events.jsonl")
        requested = {"model": config.model, "reasoning_effort": config.reasoning_effort}; observed = service_metadata(events.events)
        complete = events.valid and not any(item.get("truncated") for item in capture.untracked)
        final = (artifacts / "final.txt").read_text(); passed = smoke_passes(result, final, capture.changed_paths, complete, requested, observed)
        write_json(live / "smoke.json", {"passed": passed, "requested": requested, "observed": observed, "wrapper_sha256": hashlib.sha256(WRAPPER_PROMPT.encode()).hexdigest(), "events": len(events.events)})
        if not passed: raise RuntimeError("SMOKE_INVALID")
    finally:
        if "prepared" in locals(): prepared.cleanup()
        shutil.rmtree(task.fixture_dir.parent, ignore_errors=True)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)
    def command(name: str) -> argparse.ArgumentParser:
        result = sub.add_parser(name); result.add_argument("--experiment", default=str(DEFAULT_EXPERIMENT)); return result
    command("validate")
    qualify_parser = command("qualify"); qualify_parser.add_argument("--output", required=True)
    command("verify-power")
    simulate_parser = command("simulate"); simulate_parser.add_argument("--output", required=True)
    stage_parser = command("run-stage"); stage_parser.add_argument("--instance", required=True); stage_parser.add_argument("--stage", required=True, choices=STAGES); stage_parser.add_argument("--authorization-receipt", required=True)
    replay_parser = command("replay"); replay_parser.add_argument("--instance", required=True)
    args = parser.parse_args(argv); design = load_design(args.experiment)
    if args.command == "validate":
        print(json.dumps({"status": "BLOCKED" if design["blockers"] else "VALID", "blockers": design["blockers"]}, sort_keys=True)); return bool(design["blockers"])
    if args.command == "qualify": result = qualify(design, Path(args.output)); print(json.dumps({"passed": result["passed"], "executions": result["execution_count"]})); return not result["passed"]
    if args.command == "verify-power": result = verify_power(design); print(json.dumps(result, sort_keys=True)); return not result["passed"]
    if args.command == "simulate": result = simulate(design, Path(args.output)); print(f"VERDICT: {result['verdict']}"); return 0
    if args.command == "run-stage": run_stage(design, args.instance, args.stage, Path(args.authorization_receipt)); return 0
    result = replay(design, args.instance); print(f"VERDICT: {result['verdict']}"); return 0


if __name__ == "__main__":
    raise SystemExit(main())
