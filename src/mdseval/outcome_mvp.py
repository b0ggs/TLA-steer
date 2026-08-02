"""Frozen offline schedule, analysis, and replay boundary for the outcome MVP."""
from __future__ import annotations
import argparse, hashlib, itertools, json, re, shutil, subprocess, time
from bisect import bisect_left
from fractions import Fraction
from functools import lru_cache
from pathlib import Path, PurePosixPath
from typing import Any, Iterable, Sequence
from .capture import Redactor, parse_event_stream, write_json; from .config import RunnerConfig; from .runner.codex_cli import CodexCLI
from .hashing import tree_sha256
DEFAULT_DESIGN = Path("experiments/coder-outcomes-v2-mvp.json")
WAVE_LABELS = {"controls": ("C1", "C2", "H"), "real": ("A1", "A2", "B1", "B2")}
OUTCOMES = frozenset({"A_BETTER", "B_BETTER", "INCONCLUSIVE", "INVALID"})
_TASK_ID = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*")
_SHA256 = re.compile(r"[0-9a-f]{64}")
def _canonical(value: object) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n").encode()
def _fraction(value: Any, name: str) -> Fraction:
    if not isinstance(value, dict) or set(value) != {"numerator", "denominator"}:
        raise ValueError(f"{name} must be an exact fraction")
    numerator, denominator = value["numerator"], value["denominator"]
    if type(numerator) is not int or type(denominator) is not int or denominator <= 0:
        raise ValueError(f"{name} must contain plain integers and a positive denominator")
    return Fraction(numerator, denominator)
def load_design(path: Path = DEFAULT_DESIGN) -> dict[str, Any]:
    """Load the prospective design and verify every bound instruction hash."""
    path = Path(path)
    design = json.loads(path.read_text(encoding="utf-8"))
    runner, packet, analysis, calls = (design.get(name, {}) for name in ("runner", "task_pack", "analysis", "calls"))
    expected = {"model": runner.get("model") == "gpt-5.6-sol", "effort": runner.get("reasoning_effort") == "high", "timeout": runner.get("timeout_seconds") == 300,
                "judge": runner.get("qualitative_judge_calls") == 0, "tasks": packet.get("task_count") == 8, "blocks": analysis.get("task_blocks") == 8,
                "flips": analysis.get("sign_flips") == 256, "outcomes": set(analysis.get("outcomes", ())) == OUTCOMES, "controls": calls.get("controls") == 24,
                "real": calls.get("real") == 32, "base cap": calls.get("base_cap") == 56, "absolute cap": calls.get("absolute_cap") == 60, "retry": calls.get("max_whole_block_retries") == 1}
    failures = [name for name, passed in expected.items() if not passed]
    if failures or _fraction(analysis.get("delta_mvp"), "delta_mvp") != Fraction(1, 10) or _fraction(analysis.get("alpha"), "alpha") != Fraction(1, 20):
        raise ValueError(f"frozen design mismatch: {failures or ['analysis thresholds']}")
    bindings = design.get("bindings")
    if not isinstance(bindings, dict) or set(bindings) != set(sum(WAVE_LABELS.values(), ())):
        raise ValueError("the seven blinded bindings are required")
    root = path.resolve().parent.parent
    for label, binding in bindings.items():
        relative = PurePosixPath(binding.get("path", "")) if isinstance(binding, dict) else PurePosixPath()
        if relative.is_absolute() or not relative.parts or ".." in relative.parts:
            raise ValueError(f"unsafe binding path for {label}")
        target = root / relative
        if (target.is_symlink() or not target.is_file() or not _SHA256.fullmatch(str(binding.get("sha256", "")))
                or hashlib.sha256(target.read_bytes()).hexdigest() != binding["sha256"]):
            raise ValueError(f"unsafe binding for {label}")
        expected_wave = "controls" if label in WAVE_LABELS["controls"] else "real"
        if binding.get("wave") != expected_wave:
            raise ValueError(f"binding wave mismatch for {label}")
    packet_path = root / PurePosixPath(packet["path"])
    if packet_path.is_symlink() or tree_sha256(packet_path) != packet["tree_sha256"]:
        raise ValueError("frozen task packet drift")
    discovered: dict[str, str] = {}
    task_hashes: dict[str, str] = {}
    for repository, metadata in packet["repositories"].items():
        manifest = root / PurePosixPath(metadata["tasks_path"])
        checker = root / PurePosixPath(metadata["checker_path"])
        fixture = root / PurePosixPath(metadata["fixture_path"])
        public, subject = fixture / "test_public.py", fixture / metadata["subject_file"]
        if any(path.is_symlink() for path in (manifest, checker, fixture, public, subject)):
            raise ValueError(f"unsafe task packet path for {repository}")
        if (hashlib.sha256(manifest.read_bytes()).hexdigest() != metadata["tasks_sha256"]
                or hashlib.sha256(checker.read_bytes()).hexdigest() != metadata["checker_sha256"]
                or tree_sha256(fixture) != metadata["fixture_sha256"]
                or hashlib.sha256(public.read_bytes()).hexdigest() != metadata["public_test_sha256"]
                or not subject.is_file()):
            raise ValueError(f"task packet hash drift for {repository}")
        entries = json.loads(manifest.read_text(encoding="utf-8"))
        if [item.get("id") for item in entries] != metadata["task_ids"] or any(item.get("checker_invocation") !=
                ["python3", "check.py", item.get("id"), "{workspace}"] for item in entries):
            raise ValueError(f"task manifest mismatch for {repository}")
        for item in entries:
            if item["id"] in discovered:
                raise ValueError("duplicate task ID")
            discovered[item["id"]] = item.get("category")
            task_hashes[item["id"]] = hashlib.sha256(_canonical({"task": item, **{key: metadata[key] for key in ("tasks_sha256", "checker_sha256", "fixture_sha256")}})).hexdigest()
    counts = {category: list(discovered.values()).count(category) for category in packet["category_counts"]}
    if (sorted(discovered) != packet["task_ids"] or discovered != packet["categories"]
            or task_hashes != packet["task_hashes"] or counts != packet["category_counts"]
            or len(packet["repositories"]) != packet["repository_count"]
            or any(len(value["task_ids"]) != packet["tasks_per_repository"] for value in packet["repositories"].values())):
        raise ValueError("frozen task IDs or categories mismatch")
    allowed = design.get("implementation_paths", ())
    if len(allowed) != 20 or len(set(allowed)) != 20 or any(PurePosixPath(value).is_absolute() or
            ".." in PurePosixPath(value).parts or not (root / value).is_file() for value in allowed):
        raise ValueError("implementation path allowlist mismatch")
    return design
def require_live_authorization(design: dict[str, Any], dollar_ceiling: float | None = None,
                               max_wall_seconds: float | None = None) -> dict[str, float]:
    if design.get("live_authorization", {}).get("dollar_ceiling") is not None:
        raise RuntimeError("committed dollar ceiling placeholder must remain null")
    values = {"dollar_ceiling": dollar_ceiling, "max_wall_seconds": max_wall_seconds}
    if any(isinstance(value, bool) or not isinstance(value, (int, float)) or value <= 0 for value in values.values()):
        raise RuntimeError("LIVE_AUTHORIZATION_REQUIRED: positive dollar ceiling and maximum wall time are required")
    return {name: float(value) for name, value in values.items()}
def default_checker(checker_path: Path, task_id: str, workspace: Path, timeout_seconds: float) -> dict[str, Any]:
    stdout = stderr = ""
    try:
        process = subprocess.run(["python3", str(checker_path), task_id, str(workspace)], text=True, capture_output=True, timeout=timeout_seconds); stdout, stderr, payload = process.stdout, process.stderr, json.loads(process.stdout)
        codes = {"PASS": 0, "SUBJECT_TIMEOUT": 1, "PUBLIC_REGRESSION_FAILURE": 1, "HIDDEN_ACCEPTANCE_FAILURE": 1, "INTEGRITY_FAILURE": 3}; code = payload.get("code") if isinstance(payload, dict) else None
        valid = code in codes and payload.get("task") == task_id and type(payload.get("ok")) is bool and payload["ok"] == (code == "PASS") and process.returncode == codes[code]
        return {"valid": valid, "resolved": code == "PASS" if valid else None, "integrity": not (valid and code == "INTEGRITY_FAILURE"), "stdout": stdout, "stderr": stderr, "exit_code": process.returncode, "payload": payload}
    except (OSError, subprocess.SubprocessError, TypeError, ValueError, json.JSONDecodeError) as exc: return {"valid": False, "resolved": None, "integrity": True, "stdout": stdout, "stderr": stderr, "error": type(exc).__name__}
def _bound(design_path: Path, design: dict[str, Any], label: str, task_id: str) -> tuple[Path, dict[str, Any], dict[str, Any], dict[str, str]]:
    root = Path(design_path).resolve().parent.parent; binding = design["bindings"][label]; metadata = next(value for value in design["task_pack"]["repositories"].values() if task_id in value["task_ids"]); manifest = root / metadata["tasks_path"]
    actual = {"tasks_sha256": hashlib.sha256(manifest.read_bytes()).hexdigest(), "checker_sha256": hashlib.sha256((root / metadata["checker_path"]).read_bytes()).hexdigest(), "fixture_sha256": tree_sha256(root / metadata["fixture_path"])}
    entries = json.loads(manifest.read_text(encoding="utf-8")); task = next(item for item in entries if item.get("id") == task_id)
    hashes = {"instruction_sha256": hashlib.sha256((root / binding["path"]).read_bytes()).hexdigest(), "task_sha256": hashlib.sha256(_canonical({"task": task, **actual})).hexdigest(), **actual}
    return root, metadata, task, hashes
def run_demonstration(design_path: Path, run_dir: Path, dollar_ceiling: float, max_wall_seconds: float, oracle_controls_passed: bool, *, runner: Any = None, checker: Any = default_checker, clock: Any = time.monotonic) -> dict[str, Any]:
    design = load_design(Path(design_path)); authorization = require_live_authorization(design, dollar_ceiling, max_wall_seconds)
    if type(oracle_controls_passed) is not bool: raise ValueError("oracle_controls_passed must be boolean")
    root, run_dir = Path(design_path).resolve().parent.parent, Path(run_dir); run_dir.mkdir(parents=True, exist_ok=False)
    config = RunnerConfig("codex_cli", design["runner"]["model"], design["runner"]["reasoning_effort"], "workspace-write", "never", False, True, False, design["runner"]["timeout_seconds"], 1)
    write_json(run_dir / "authorization.json", {**authorization, "oracle_controls_passed": oracle_controls_passed, "absolute_call_cap": 60, "runner": config.__dict__})
    evidence: dict[str, Any] = {"schema_version": 1, "task_ids": design["task_pack"]["task_ids"], "oracle_controls_passed": oracle_controls_passed, "observations": [], "wave_hashes": {}, "errors": []}
    live, deadline, retry, stopped = (runner if runner is not None or not oracle_controls_passed else CodexCLI(config)), clock() + authorization["max_wall_seconds"], None, not oracle_controls_passed
    def launch(original: dict[str, Any]) -> str:
        nonlocal stopped
        if stopped: return "stopped"
        remaining = deadline - clock()
        if remaining <= 0: evidence["errors"].append("aggregate wall deadline expired"); stopped = True; return "stopped"
        try: bound_root, metadata, task, before = _bound(design_path, design, original["label"], original["task_id"])
        except (OSError, ValueError, KeyError, StopIteration, json.JSONDecodeError) as exc: evidence["errors"].append(f"input preflight: {type(exc).__name__}"); stopped = True; return "stopped"
        if before["instruction_sha256"] != design["bindings"][original["label"]]["sha256"] or before["task_sha256"] != design["task_pack"]["task_hashes"][original["task_id"]]: evidence["errors"].append("frozen input hash mismatch"); stopped = True; return "stopped"
        slot = {**original, "launch_index": len(evidence["observations"]) + 1}; directory = run_dir / "raw" / f"slot-{slot['launch_index']:02d}"; directory.mkdir(parents=True)
        workspace = directory / "workspace"; shutil.copytree(bound_root / metadata["fixture_path"], workspace)
        (workspace / "CODER.md").write_bytes((bound_root / design["bindings"][slot["label"]]["path"]).read_bytes()); (workspace / ".issue-contract.md").write_text(task["prompt"] + "\n", encoding="utf-8")
        artifacts = directory / "runner"; artifacts.mkdir(); write_json(directory / "launch.json", {**slot, "timeout_seconds": min(300, remaining), "input": before})
        started, result, error = clock(), None, None
        try: result = live.run(argparse.Namespace(repo=workspace, case=argparse.Namespace(id=slot["task_id"])), artifacts, min(300, remaining), Redactor())
        except Exception as exc: error = f"{type(exc).__name__}: {exc}"
        for name in ("events.jsonl", "stderr.txt", "final.txt"): (artifacts / name).touch(exist_ok=True)
        events = parse_event_stream(artifacts / "events.jsonl")
        try: checked = checker(bound_root / metadata["checker_path"], slot["task_id"], workspace, min(300, max(0.001, deadline - clock()))) if error is None else {"valid": False, "resolved": None, "integrity": True, "stdout": "", "stderr": ""}
        except Exception as exc: checked = {"valid": False, "resolved": None, "integrity": True, "stdout": "", "stderr": "", "error": type(exc).__name__}
        try: after = _bound(design_path, design, slot["label"], slot["task_id"])[3]
        except (OSError, ValueError, KeyError, StopIteration, json.JSONDecodeError): after = {}
        shape = isinstance(checked, dict) and type(checked.get("valid")) is bool and type(checked.get("integrity")) is bool and isinstance(checked.get("stdout"), str) and isinstance(checked.get("stderr"), str) and ((checked["valid"] and type(checked.get("resolved")) is bool) or (not checked["valid"] and checked.get("resolved") is None))
        integrity = bool(shape and checked["integrity"] and after == before); valid = bool(shape and checked["valid"] and events.valid and result is not None and not result.interrupted and error is None)
        resolved = (False if result and result.timed_out else checked["resolved"]) if valid else None; usage = {name: events.usage.get("reasoning_output_tokens" if name == "reasoning_tokens" else name, 0) for name in ("input_tokens", "cached_input_tokens", "output_tokens", "reasoning_tokens", "total_tokens")}
        row = {**slot, "session_id": f"session:{slot['slot_id']}", "workspace_id": f"workspace:{slot['slot_id']}", "raw_artifact_path": str(directory.relative_to(run_dir)), **before,
               "observation_valid": valid, "objective_resolved": resolved, "subject_integrity": integrity, "duration_seconds": max(0.0, clock() - started), "usage": usage,
               "runner": {"status": getattr(result, "status", "EXCEPTION"), "exit_code": getattr(result, "exit_code", None), "timed_out": bool(result and result.timed_out), "interrupted": bool(result and result.interrupted), "error": error}, "checker": checked,
               "input_before": before, "input_after": after, "git_integrity": {"workspace_before": before["fixture_sha256"], "workspace_after": tree_sha256(workspace)}}
        write_json(directory / "slot.json", row); evidence["observations"].append(row)
        if not integrity: evidence["errors"].append("mechanical input or checker integrity drift"); stopped = True; return "stopped"
        return "valid" if valid else "invalid"
    def wave(name: str) -> None:
        nonlocal retry, stopped
        evidence["wave_hashes"][name] = {"before": tree_sha256(root / design["task_pack"]["path"])}
        scheduled = build_schedule(design, evidence["task_ids"], waves=("controls", "real") if name == "real" else ("controls",), retry=retry); base = [slot for slot in scheduled if slot["wave"] == name and slot["block_attempt"] == 1]
        for task_id in dict.fromkeys(slot["task_id"] for slot in base):
            states = [launch(slot) for slot in base if slot["task_id"] == task_id]
            if stopped: break
            if "invalid" in states:
                if retry is not None: evidence["errors"].append("second infrastructure-invalid block"); stopped = True; break
                retry = (name, task_id); repeated = [slot for slot in build_schedule(design, evidence["task_ids"], waves=("controls", "real") if name == "real" else ("controls",), retry=retry) if slot["wave"] == name and slot["task_id"] == task_id and slot["block_attempt"] == 2]
                repeated_states = [launch(slot) for slot in repeated]
                if stopped or any(state != "valid" for state in repeated_states): evidence["errors"].append("retry remained infrastructure-invalid"); stopped = True; break
        evidence["wave_hashes"][name]["after"] = tree_sha256(root / design["task_pack"]["path"])
    if not stopped: wave("controls"); control_report = analyze(design, evidence)
    if not stopped:
        if not stopped and control_report["run_status"] == "CONTROL_PASSED": wave("real")
    write_json(run_dir / "raw-evidence.json", evidence); report = analyze(design, evidence); write_reports(run_dir / "reports", report)
    return report
def _tasks(design: dict[str, Any], values: Iterable[Any]) -> tuple[str, ...]:
    task_ids = tuple(values)
    if (len(task_ids) != design["task_pack"]["task_count"] or len(set(task_ids)) != len(task_ids)
            or sorted(task_ids) != design["task_pack"]["task_ids"]):
        raise ValueError("exactly eight unique task IDs are required")
    if any(not isinstance(item, str) or _TASK_ID.fullmatch(item) is None for item in task_ids):
        raise ValueError("task IDs must be lowercase kebab-case")
    return tuple(sorted(task_ids))
def build_schedule(design: dict[str, Any], task_ids: Iterable[str], *, waves: tuple[str, ...] = ("controls", "real"),
                   retry: tuple[str, str] | None = None) -> list[dict[str, Any]]:
    """Return randomized complete blocks; an optional retry repeats one whole block."""
    tasks = _tasks(design, task_ids)
    if waves not in {("controls",), ("controls", "real")}:
        raise ValueError("waves must be controls or controls followed by real")
    if retry is not None and (retry[0] not in waves or retry[1] not in tasks):
        raise ValueError("retry must identify one scheduled task block")
    seed = design["randomization"]["seed"]
    def order(parts: Sequence[str]) -> bytes:
        return hashlib.sha256(":".join((str(seed), *parts)).encode()).digest()
    slots: list[dict[str, Any]] = []
    for wave in waves:
        for task_id in sorted(tasks, key=lambda task: order((wave, task, "0", "block"))):
            attempts = (1, 2) if retry == (wave, task_id) else (1,)
            for attempt in attempts:
                labels = sorted(WAVE_LABELS[wave], key=lambda label: order((wave, task_id, str(attempt), label)))
                for label in labels:
                    slots.append({"launch_index": len(slots) + 1, "wave": wave, "task_id": task_id,
                                  "block_attempt": attempt, "label": label,
                                  "slot_id": f"{wave}:{task_id}:{attempt}:{label}"})
    return slots
def _p_value(differences: Sequence[Fraction]) -> Fraction:
    observed = abs(sum(differences, Fraction()))
    extreme = sum(
        abs(sum((value if mask >> index & 1 else -value for index, value in enumerate(differences)), start=Fraction())) >= observed
        for mask in range(1 << len(differences))
    )
    return Fraction(extreme, 1 << len(differences))
def compare(
    selected: dict[tuple[str, str], dict[str, Any]], task_ids: Sequence[str],
    labels_a: Sequence[str], labels_b: Sequence[str], design: dict[str, Any],
) -> dict[str, Any]:
    rows, differences = [], []
    for task_id in task_ids:
        a = Fraction(sum(selected[task_id, label]["objective_resolved"] for label in labels_a), len(labels_a))
        b = Fraction(sum(selected[task_id, label]["objective_resolved"] for label in labels_b), len(labels_b))
        differences.append(b - a)
        rows.append({"task_id": task_id, "pass_at_1_a": float(a), "pass_at_1_b": float(b), "difference_b_minus_a": float(b - a)})
    effect, probability = sum(differences, Fraction()) / len(task_ids), _p_value(differences)
    delta, alpha = _fraction(design["analysis"]["delta_mvp"], "delta_mvp"), _fraction(design["analysis"]["alpha"], "alpha")
    outcome = "B_BETTER" if effect >= delta and probability <= alpha else "A_BETTER" if effect <= -delta and probability <= alpha else "INCONCLUSIVE"
    return {"outcome": outcome, "macro_pass_at_1": {"A": float(sum(Fraction(row["pass_at_1_a"]) for row in rows) / len(rows)), "B": float(sum(Fraction(row["pass_at_1_b"]) for row in rows) / len(rows))},
            "effect_b_minus_a": float(effect), "p_value": {"numerator": probability.numerator, "denominator": probability.denominator, "value": float(probability)}, "tasks": rows}
@lru_cache(maxsize=1)
def offline_null_calibration() -> dict[str, Any]:
    """Enumerate all 3^8 attainable magnitude patterns and all 2^8 signs."""
    worst = 0
    for magnitudes in itertools.product((0, 1, 2), repeat=8):
        totals = [sum(value if mask >> index & 1 else -value for index, value in enumerate(magnitudes)) for mask in range(256)]
        absolute = sorted(abs(total) for total in totals)
        winners = sum(abs(total) >= 2 and 256 - bisect_left(absolute, abs(total)) <= 12 for total in totals)
        worst = max(worst, winners)
    return {"passed": worst * 20 <= 256, "magnitude_patterns": 3**8, "sign_assignments_per_pattern": 256, "maximum_winner_probability": {"numerator": Fraction(worst, 256).numerator, "denominator": Fraction(worst, 256).denominator, "value": worst / 256}}
def _validate_evidence(design: dict[str, Any], evidence: Any) -> tuple[tuple[str, ...], list[dict[str, Any]], dict[tuple[str, str], dict[str, Any]], str, int]:
    if not isinstance(evidence, dict) or evidence.get("schema_version") != 1 or type(evidence.get("oracle_controls_passed")) is not bool:
        raise ValueError("invalid raw evidence envelope")
    tasks, observations = _tasks(design, evidence.get("task_ids", ())), evidence.get("observations")
    if not isinstance(observations, list) or not observations:
        raise ValueError("raw observations are required")
    if len(observations) > design["calls"]["absolute_cap"]:
        raise ValueError("absolute launched-call cap exceeded")
    retries = {(item.get("wave"), item.get("task_id")) for item in observations if isinstance(item, dict) and item.get("block_attempt") == 2}
    if len(retries) > 1:
        raise ValueError("more than one task block was retried")
    phase = "full" if any(isinstance(item, dict) and item.get("wave") == "real" for item in observations) else "controls"
    retry = next(iter(retries), None)
    expected = build_schedule(design, tasks, waves=("controls", "real") if phase == "full" else ("controls",), retry=retry)
    slot_fields = ("launch_index", "wave", "task_id", "block_attempt", "label", "slot_id")
    if len(expected) != len(observations) or any(not isinstance(item, dict) or tuple(item.get(key) for key in slot_fields) != tuple(slot[key] for key in slot_fields) for item, slot in zip(observations, expected)):
        raise ValueError("launched calls do not match the deterministic complete-block schedule")
    for field in ("session_id", "workspace_id", "raw_artifact_path"):
        values = [item.get(field) for item in observations]
        if any(not isinstance(value, str) or not value for value in values) or len(set(values)) != len(values):
            raise ValueError(f"every launched call requires a unique {field}")
    invalid_blocks: set[tuple[str, str]] = set()
    for item in observations:
        valid, resolved, integrity = item.get("observation_valid"), item.get("objective_resolved"), item.get("subject_integrity")
        if type(valid) is not bool or type(integrity) is not bool or (valid and type(resolved) is not bool) or (not valid and resolved is not None):
            raise ValueError("observation validity fields are malformed")
        if not integrity: raise ValueError("subject integrity disqualified the demonstration")
        if not valid: invalid_blocks.add((item["wave"], item["task_id"]))
        if (item.get("instruction_sha256") != design["bindings"][item["label"]]["sha256"] or
                item.get("task_sha256") != design["task_pack"]["task_hashes"][item["task_id"]]):
            raise ValueError("frozen input hash mismatch")
        duration, usage = item.get("duration_seconds"), item.get("usage")
        if isinstance(duration, bool) or not isinstance(duration, (int, float)) or duration < 0 or not isinstance(usage, dict) or any(type(value) is not int or value < 0 for value in usage.values()):
            raise ValueError("invalid efficiency evidence")
    if invalid_blocks and (len(invalid_blocks) != 1 or retry != next(iter(invalid_blocks))) or retry and not invalid_blocks:
        raise ValueError("infrastructure invalidity was not retried as one whole block")
    chosen: dict[tuple[str, str], dict[str, Any]] = {}; superseded = 0
    for item in observations:
        use = item["block_attempt"] == (2 if retry == (item["wave"], item["task_id"]) else 1)
        if use:
            if not item["observation_valid"]: raise ValueError("retried evidence remains infrastructure-invalid")
            chosen[item["task_id"], item["label"]] = item
        else: superseded += 1
    return tasks, observations, chosen, phase, superseded
def analyze(design: dict[str, Any], evidence: Any) -> dict[str, Any]:
    """Apply the complete frozen gate and chooser to preserved raw observations."""
    base = {"schema_version": 1, "experiment_id": design["experiment_id"], "design_sha256": hashlib.sha256(_canonical(design)).hexdigest(),
            "analysis_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(), "raw_evidence_sha256": hashlib.sha256(_canonical(evidence)).hexdigest()}
    try:
        tasks, observations, selected, phase, superseded = _validate_evidence(design, evidence)
    except (KeyError, TypeError, ValueError) as exc:
        return {**base, "run_status": "INVALID", "verdict": "INVALID", "reasons": [str(exc)]}
    aa = compare(selected, tasks, ("C1",), ("C2",), design)
    harmful = compare(selected, tasks, ("C1",), ("H",), design)
    favorable = sum(row["difference_b_minus_a"] < 0 for row in harmful["tasks"])
    adverse = sum(row["difference_b_minus_a"] > 0 for row in harmful["tasks"])
    gates = {"offline_null": offline_null_calibration()["passed"],
             "oracle_controls": evidence["oracle_controls_passed"],
             "aa": aa["outcome"] == "INCONCLUSIVE",
             "known_better": harmful["outcome"] == "A_BETTER" and favorable >= 6 and adverse == 0}
    controls_passed = all(gates.values())
    real = compare(selected, tasks, ("A1", "A2"), ("B1", "B2"), design) if phase == "full" else None
    if phase == "full" and not controls_passed:
        verdict, status, reasons = "INVALID", "STOP/REDESIGN", ["real wave launched without passing every control gate"]
    else:
        verdict, status, reasons = (real["outcome"], "COMPLETE", []) if real else ("INCONCLUSIVE", "CONTROL_PASSED" if controls_passed else "STOP/REDESIGN", [])
    token_fields = ("input_tokens", "cached_input_tokens", "output_tokens", "reasoning_tokens", "total_tokens")
    efficiency = {field: sum(item["usage"].get(field, 0) for item in observations) for field in token_fields}
    efficiency.update({"launched_calls": len(observations), "superseded_calls": superseded,
                       "duration_seconds": round(sum(item["duration_seconds"] for item in observations), 6),
                       "token_evidence_complete": all(set(item["usage"]) >= set(token_fields) for item in observations)})
    return {**base, "run_status": status, "verdict": verdict, "reasons": reasons,
            "task_ids": list(tasks), "phase": phase, "control_gates": gates,
            "aa_comparison": aa, "known_better_comparison": {**harmful, "favorable_tasks": favorable, "adverse_tasks": adverse},
            "real_comparison": real, "null_calibration": offline_null_calibration(), "efficiency": efficiency,
            "claim_boundary": "This result applies only to the frozen eight-task synthetic Python repository pack and configuration."}
def render_markdown(report: dict[str, Any]) -> str:
    lines = ["# CODER Outcome Evaluator V2 MVP", "", f"Verdict: **{report['verdict']}**", f"Run status: **{report['run_status']}**", ""]
    if report["verdict"] == "INVALID": lines.extend(["Reasons: " + "; ".join(report.get("reasons", ())), ""])
    if "control_gates" in report:
        lines.extend(["## Control gates", "", *[f"- {name}: {'PASS' if passed else 'FAIL'}" for name, passed in report["control_gates"].items()], ""])
        real = report.get("real_comparison")
        if real:
            lines.extend(["## Real comparison", "", f"Macro pass@1: A={real['macro_pass_at_1']['A']:.3f}, B={real['macro_pass_at_1']['B']:.3f}; B−A={real['effect_b_minus_a']:.3f}; exact two-sided p={real['p_value']['numerator']}/{real['p_value']['denominator']}", "", "| Task | A pass@1 | B pass@1 | B−A |", "|---|---:|---:|---:|", *[f"| {row['task_id']} | {row['pass_at_1_a']:.3f} | {row['pass_at_1_b']:.3f} | {row['difference_b_minus_a']:.3f} |" for row in real["tasks"]], ""])
        efficiency = report["efficiency"]
        lines.extend(["## Efficiency", "", f"Launched calls: {efficiency['launched_calls']} (superseded: {efficiency['superseded_calls']}); wall time sum: {efficiency['duration_seconds']:.6f}s; total tokens: {efficiency['total_tokens']}", "", report["claim_boundary"], "", "Non-significance is not equivalence; this intentionally small MVP is likely inconclusive for modest differences.", ""])
    return "\n".join(lines)
def write_reports(output_dir: Path, report: dict[str, Any]) -> None:
    output_dir = Path(output_dir); output_dir.mkdir(parents=True, exist_ok=False)
    (output_dir / "report.json").write_bytes(json.dumps(report, indent=2, sort_keys=True).encode() + b"\n")
    (output_dir / "report.md").write_text(render_markdown(report), encoding="utf-8")
def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Offline boundary for the frozen CODER outcome MVP; it makes no model calls.")
    parser.add_argument("--experiment", type=Path, default=DEFAULT_DESIGN)
    commands = parser.add_subparsers(dest="command", required=True)
    schedule = commands.add_parser("schedule", help="print the deterministic 56-call base schedule")
    schedule.add_argument("tasks", nargs=8)
    replay = commands.add_parser("replay", help="regenerate deterministic reports from raw observations without model calls")
    replay.add_argument("observations", type=Path); replay.add_argument("output_dir", type=Path)
    run = commands.add_parser("run", help="run the authorized bounded live demonstration")
    run.add_argument("run_dir", type=Path); run.add_argument("--dollar-ceiling", type=float, required=True)
    run.add_argument("--max-wall-seconds", type=float, required=True); run.add_argument("--oracle-controls-passed", action="store_true", required=True)
    args = parser.parse_args(argv)
    try:
        design = load_design(args.experiment)
        if args.command == "schedule":
            print(json.dumps(build_schedule(design, args.tasks), indent=2, sort_keys=True))
            return 0
        if args.command == "run": report = run_demonstration(args.experiment, args.run_dir, args.dollar_ceiling, args.max_wall_seconds, args.oracle_controls_passed); print(f"VERDICT: {report['verdict']}\nREPORT: {args.run_dir / 'reports/report.md'}"); return 1 if report["verdict"] == "INVALID" else 0
        evidence = json.loads(args.observations.read_text(encoding="utf-8"))
        report = analyze(design, evidence)
        write_reports(args.output_dir, report)
        print(f"VERDICT: {report['verdict']}\nREPORT: {args.output_dir / 'report.md'}")
        return 1 if report["verdict"] == "INVALID" else 0
    except (OSError, ValueError, RuntimeError, json.JSONDecodeError) as exc:
        parser.error(str(exc))
    return 2
if __name__ == "__main__":
    raise SystemExit(main())
