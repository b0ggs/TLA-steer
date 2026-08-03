"""Qualification, bounded execution, analysis, and replay for the outcome MVP."""
from __future__ import annotations
import argparse, base64, hashlib, itertools, json, os, re, shutil, subprocess, time
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
TOKEN_FIELDS = ("input_tokens", "cached_input_tokens", "output_tokens", "reasoning_tokens", "total_tokens")
CASE_SPECS = (("pristine", "pristine", False), ("correct-a", "correct", True), ("correct-b", "correct", True),
              ("mutant-a", "mutant", False), ("mutant-b", "mutant", False))
RECEIPT_BINDINGS = ("verified_commit", "evaluator_sha256", "design_sha256", "analysis_sha256", "wrapper_sha256",
                    "task_tree_sha256", "checker_hashes", "oracle_sha256", "command_config_sha256", "results_sha256")
QUALIFICATION_COMMAND = {"command": "qualify", "tasks": 8, "cases_per_task": 5, "repeats_per_case": 3, "timeout_seconds": 300}
_TASK_ID = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*")
_SHA256 = re.compile(r"[0-9a-f]{64}")
_GIT_OBJECT_ID = re.compile(r"(?:[0-9a-f]{40}|[0-9a-f]{64})")
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
    runner, packet, analysis, calls, environment, qualification = (design.get(name, {}) for name in
        ("runner", "task_pack", "analysis", "calls", "environment", "qualification"))
    expected = {"model": runner.get("model") == "gpt-5.6-sol", "effort": runner.get("reasoning_effort") == "high", "timeout": runner.get("timeout_seconds") == 300,
                "judge": runner.get("qualitative_judge_calls") == 0, "tasks": packet.get("task_count") == 8, "blocks": analysis.get("task_blocks") == 8,
                "flips": analysis.get("sign_flips") == 256, "outcomes": set(analysis.get("outcomes", ())) == OUTCOMES, "controls": calls.get("controls") == 24,
                "real": calls.get("real") == 32, "base cap": calls.get("base_cap") == 56, "absolute cap": calls.get("absolute_cap") == 60, "retry": calls.get("max_whole_block_retries") == 1,
                "auth": environment.get("authentication_mode") == "chatgpt_oauth", "wall": environment.get("max_wall_seconds") == 10800,
                "clean": environment.get("clean_exact_commit_required") is True, "isolated": environment.get("isolated_runner_preflight_required") is True,
                "repeats": qualification.get("repeats_per_case") == 3, "receipt": qualification.get("authoritative_receipt_required") is True,
                "receipt bindings": tuple(qualification.get("receipt_hash_bindings", ())) == RECEIPT_BINDINGS,
                "legacy controls removed": "live_authorization" not in design and "implementation_paths" not in design}
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
    integrity_paths = environment.get("integrity_paths")
    expected_paths = {"evaluator": "src/mdseval/outcome_mvp.py", "design": "experiments/coder-outcomes-v2-mvp.json",
                      "analysis": "src/mdseval/outcome_mvp.py", "wrapper": "src/mdseval/wrapper.py"}
    if integrity_paths != expected_paths or any(not (root / PurePosixPath(value)).is_file() for value in expected_paths.values()):
        raise ValueError("environment integrity paths mismatch")
    oracle_relative = PurePosixPath(str(qualification.get("oracle_path", "")))
    oracle = root / oracle_relative
    if (oracle_relative.is_absolute() or ".." in oracle_relative.parts or oracle.is_symlink() or not oracle.is_file()
            or not _SHA256.fullmatch(str(qualification.get("oracle_sha256", "")))
            or hashlib.sha256(oracle.read_bytes()).hexdigest() != qualification["oracle_sha256"]):
        raise ValueError("qualification oracle hash mismatch")
    return design


def integrity_snapshot(design_path, design):
    root = Path(design_path).resolve().parent.parent
    return {**{f"{name}_sha256": hashlib.sha256((root / relative).read_bytes()).hexdigest()
               for name, relative in design["environment"]["integrity_paths"].items()},
            "task_tree_sha256": tree_sha256(root / design["task_pack"]["path"]),
            "checker_hashes": {name: hashlib.sha256((root / metadata["checker_path"]).read_bytes()).hexdigest()
                               for name, metadata in design["task_pack"]["repositories"].items()},
            "treatment_hashes": {label: hashlib.sha256((root / binding["path"]).read_bytes()).hexdigest()
                                  for label, binding in design["bindings"].items()}}


def require_environment(design_path, design, observed=None):
    if observed is None:
        root, home = Path(design_path).resolve().parent.parent, (Path(os.environ["MDSEVAL_CODEX_HOME"]).expanduser()
            if os.environ.get("MDSEVAL_CODEX_HOME") else None)
        help_result, login, commit, status = [subprocess.run(command, text=True, capture_output=True, timeout=10,
            env={**os.environ, "CODEX_HOME": str(home)}) for command in (("codex", "exec", "--help"),
            ("codex", "login", "status"), ("git", "-C", str(root), "rev-parse", "HEAD"),
            ("git", "-C", str(root), "status", "--porcelain", "--untracked-files=all"))]
        observed = {"verified_commit": commit.stdout.strip(), "clean": commit.returncode == status.returncode == 0 and not status.stdout.strip(),
                    "authentication_mode": "chatgpt_oauth" if login.returncode == 0 and "chatgpt" in (login.stdout + login.stderr).lower() else "unknown",
                    "isolated_runner_preflight_passed": bool(home and home.is_dir() and shutil.which("codex") and help_result.returncode == 0
                        and all(flag in help_result.stdout + help_result.stderr for flag in ("--strict-config", "--ephemeral", "--sandbox", "--ignore-rules", "--model"))
                        and not (home / "AGENTS.md").exists() and not (home / "AGENTS.override.md").exists())}
    if (not observed.get("clean") or _GIT_OBJECT_ID.fullmatch(str(observed.get("verified_commit", ""))) is None
            or observed.get("authentication_mode") != design["environment"]["authentication_mode"]
            or observed.get("isolated_runner_preflight_passed") is not True):
        raise RuntimeError("ENVIRONMENT_PREFLIGHT_REQUIRED")
    return dict(observed)


def _oracle(design_path, design):
    root = Path(design_path).resolve().parent.parent
    value = json.loads((root / design["qualification"]["oracle_path"]).read_text(encoding="utf-8"))
    tasks = value.get("tasks") if isinstance(value, dict) and value.get("schema_version") == 1 else None
    repositories = {task_id: name for name, metadata in design["task_pack"]["repositories"].items() for task_id in metadata["task_ids"]}
    if (not isinstance(tasks, dict) or set(tasks) != set(repositories)
            or any(not isinstance(task, dict) or task.get("repository") != repositories[task_id]
                   or not isinstance(task.get("cases"), list) for task_id, task in tasks.items())):
        raise ValueError("qualification oracle mismatch")
    return value


def _install_source(path, source):
    path.write_text(path.read_text(encoding="utf-8").rstrip() + "\n\n" + source.rstrip() + "\n", encoding="utf-8")


def _results_pass(design, rows):
    return (isinstance(rows, list) and [(row.get("task_id"), row.get("case_id"), row.get("kind"), row.get("repeat"), row.get("expected"))
            for row in rows if isinstance(row, dict)] == [(task_id, case_id, kind, repeat, outcome)
            for task_id in design["task_pack"]["task_ids"] for case_id, kind, outcome in CASE_SPECS
            for repeat in range(1, design["qualification"]["repeats_per_case"] + 1)]
            and all(row.get("passed") is True and row.get("valid") is True and row.get("integrity") is True
                    and row.get("resolved") is row.get("expected") for row in rows))


def _validate_receipt_payload(design, snapshot, receipt, verified_commit=None):
    command = receipt.get("command_config") if isinstance(receipt, dict) else None
    rows = receipt.get("results") if isinstance(receipt, dict) else None
    if (receipt.get("schema_version") != 1 or receipt.get("status") != "PASS"
            or _GIT_OBJECT_ID.fullmatch(str(receipt.get("verified_commit", ""))) is None
            or receipt.get("authentication_mode") != "chatgpt_oauth" or receipt.get("isolated_runner_preflight_passed") is not True
            or (verified_commit is not None and receipt.get("verified_commit") != verified_commit)
            or any(receipt.get(key) != snapshot[key] for key in RECEIPT_BINDINGS[1:7])
            or receipt.get("oracle_sha256") != design["qualification"]["oracle_sha256"] or command != QUALIFICATION_COMMAND
            or not _results_pass(design, rows)
            or receipt.get("command_config_sha256") != hashlib.sha256(_canonical(command)).hexdigest()
            or receipt.get("results_sha256") != hashlib.sha256(_canonical(rows)).hexdigest()):
        raise RuntimeError("QUALIFICATION_RECEIPT_INVALID")
    return receipt


def default_checker(checker_path: Path, task_id: str, workspace: Path, timeout_seconds: float) -> dict[str, Any]:
    stdout = stderr = ""
    try:
        process = subprocess.run(["python3", str(checker_path), task_id, str(workspace)], text=True, capture_output=True, timeout=timeout_seconds); stdout, stderr, payload = process.stdout, process.stderr, json.loads(process.stdout)
        codes = {"PASS": 0, "SUBJECT_TIMEOUT": 1, "PUBLIC_REGRESSION_FAILURE": 1, "HIDDEN_ACCEPTANCE_FAILURE": 1, "INTEGRITY_FAILURE": 3}; code = payload.get("code") if isinstance(payload, dict) else None
        valid = code in codes and payload.get("task") == task_id and type(payload.get("ok")) is bool and payload["ok"] == (code == "PASS") and process.returncode == codes[code]
        return {"valid": valid, "resolved": code == "PASS" if valid else None, "integrity": not (valid and code == "INTEGRITY_FAILURE"), "stdout": stdout, "stderr": stderr, "exit_code": process.returncode, "payload": payload}
    except (OSError, subprocess.SubprocessError, TypeError, ValueError, json.JSONDecodeError) as exc: return {"valid": False, "resolved": None, "integrity": True, "stdout": stdout, "stderr": stderr, "error": type(exc).__name__}


def qualify(design_path, output_dir, *, authoritative=False, checker=default_checker, observed_environment=None):
    design = load_design(Path(design_path))
    oracle = _oracle(design_path, design)
    environment = require_environment(design_path, design, observed_environment) if authoritative else None
    start, root, output = integrity_snapshot(design_path, design), Path(design_path).resolve().parent.parent, Path(output_dir)
    output.mkdir(parents=True, exist_ok=False)
    rows: list[dict[str, Any]] = []
    for task_id, oracle_task, case, repeat in ((task_id, oracle["tasks"][task_id], case, repeat)
            for task_id in design["task_pack"]["task_ids"] for case in oracle["tasks"][task_id]["cases"]
            for repeat in range(1, design["qualification"]["repeats_per_case"] + 1)):
        metadata = design["task_pack"]["repositories"][oracle_task["repository"]]
        case_dir, workspace = output / "raw" / task_id / case["id"] / f"repeat-{repeat}", output / "raw" / task_id / case["id"] / f"repeat-{repeat}" / "workspace"
        case_dir.mkdir(parents=True)
        shutil.copytree(root / metadata["fixture_path"], workspace)
        if "source" in case:
            _install_source(workspace / metadata["subject_file"], case["source"])
        checked = checker(root / metadata["checker_path"], task_id, workspace, design["runner"]["timeout_seconds"])
        rows.append({"task_id": task_id, "case_id": case["id"], "kind": case["kind"], "repeat": repeat,
                     "expected": case["expected"], "valid": checked.get("valid"), "resolved": checked.get("resolved"),
                     "integrity": checked.get("integrity"), "passed": checked.get("valid") is True and checked.get("integrity") is True
                     and checked.get("resolved") is case["expected"], "checker": checked})
    end = integrity_snapshot(design_path, design)
    result = {"schema_version": 1, "authoritative": authoritative, "passed": _results_pass(design, rows) and start == end,
              "execution_count": len(rows), "integrity_hashes": {"start": start, "end": end}, "results": rows}
    write_json(output / "qualification-results.json", result)
    if authoritative and result["passed"]:
        receipt = {"schema_version": 1, "status": "PASS", "verified_commit": environment["verified_commit"],
                   "authentication_mode": environment["authentication_mode"], "isolated_runner_preflight_passed": True,
                   **{key: start[key] for key in RECEIPT_BINDINGS[1:7]},
                   "oracle_sha256": design["qualification"]["oracle_sha256"], "command_config": QUALIFICATION_COMMAND,
                   "command_config_sha256": hashlib.sha256(_canonical(QUALIFICATION_COMMAND)).hexdigest(),
                   "results": (bound := [{key: row[key] for key in ("task_id", "case_id", "kind", "repeat", "expected", "valid", "resolved", "integrity", "passed")} for row in rows]),
                   "results_sha256": hashlib.sha256(_canonical(bound)).hexdigest()}
        write_json(output / "qualification-receipt.json", receipt)
    return result


def _workspace_files(root):
    return {path.relative_to(root).as_posix(): {"base64": base64.b64encode(data).decode("ascii")}
            for path in sorted(root.rglob("*")) if path.is_file() and not path.is_symlink()
            and "__pycache__" not in path.parts and path.suffix not in {".pyc", ".pyo"} for data in (path.read_bytes(),)}


def _contract_hashes(workspace):
    return {name: hashlib.sha256((workspace / name).read_bytes()).hexdigest() if (workspace / name).is_file() else ""
            for name in ("CODER.md", ".issue-contract.md")}
def _bound(design_path: Path, design: dict[str, Any], label: str, task_id: str) -> tuple[Path, dict[str, Any], dict[str, Any], dict[str, str]]:
    root = Path(design_path).resolve().parent.parent; binding = design["bindings"][label]; metadata = next(value for value in design["task_pack"]["repositories"].values() if task_id in value["task_ids"]); manifest = root / metadata["tasks_path"]
    actual = {"tasks_sha256": hashlib.sha256(manifest.read_bytes()).hexdigest(), "checker_sha256": hashlib.sha256((root / metadata["checker_path"]).read_bytes()).hexdigest(), "fixture_sha256": tree_sha256(root / metadata["fixture_path"])}
    entries = json.loads(manifest.read_text(encoding="utf-8")); task = next(item for item in entries if item.get("id") == task_id)
    hashes = {"instruction_sha256": hashlib.sha256((root / binding["path"]).read_bytes()).hexdigest(), "task_sha256": hashlib.sha256(_canonical({"task": task, **actual})).hexdigest(), **actual}
    return root, metadata, task, hashes
def run_demonstration(design_path: Path, run_dir: Path, qualification_receipt: Path, *, runner: Any = None,
                      checker: Any = default_checker, clock: Any = time.monotonic,
                      observed_environment: dict[str, Any] | None = None) -> dict[str, Any]:
    design = load_design(Path(design_path))
    environment = require_environment(design_path, design, observed_environment)
    receipt = json.loads(Path(qualification_receipt).read_text(encoding="utf-8"))
    start = integrity_snapshot(design_path, design)
    _validate_receipt_payload(design, start, receipt, environment["verified_commit"])
    run_dir = Path(run_dir)
    run_dir.mkdir(parents=True, exist_ok=False)
    config = RunnerConfig("codex_cli", design["runner"]["model"], design["runner"]["reasoning_effort"], "workspace-write", "never", False, True, False, design["runner"]["timeout_seconds"], 1)
    write_json(run_dir / "authorization.json", {"authentication_mode": environment["authentication_mode"],
               "verified_commit": environment["verified_commit"], "isolated_runner_preflight_passed": True,
               "max_wall_seconds": design["environment"]["max_wall_seconds"], "absolute_call_cap": 60,
               "qualification_receipt_sha256": hashlib.sha256(_canonical(receipt)).hexdigest(), "runner": config.__dict__})
    evidence: dict[str, Any] = {"schema_version": 2, "task_ids": design["task_pack"]["task_ids"],
                                "qualification_receipt": receipt, "integrity_hashes": {"start": start, "end": start},
                                "observations": [], "errors": []}
    live, deadline, retry, stopped = (runner if runner is not None else CodexCLI(config)), clock() + design["environment"]["max_wall_seconds"], None, False
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
        (workspace / "CODER.md").write_bytes((bound_root / design["bindings"][slot["label"]]["path"]).read_bytes())
        (workspace / ".issue-contract.md").write_text(task["prompt"] + "\n", encoding="utf-8")
        baseline_files, baseline_tree, contracts_before = _workspace_files(workspace), tree_sha256(workspace), _contract_hashes(workspace)
        artifacts = directory / "runner"; artifacts.mkdir(); write_json(directory / "launch.json", {**slot, "timeout_seconds": min(300, remaining), "input": before})
        started, result, error = clock(), None, None
        try: result = live.run(argparse.Namespace(repo=workspace, case=argparse.Namespace(id=slot["task_id"])), artifacts, min(300, remaining), Redactor())
        except Exception as exc: error = f"{type(exc).__name__}: {exc}"
        for name in ("events.jsonl", "stderr.txt", "final.txt"): (artifacts / name).touch(exist_ok=True)
        contracts_after = _contract_hashes(workspace)
        final_files, final_tree = _workspace_files(workspace), tree_sha256(workspace)
        patch = {"baseline_tree_sha256": baseline_tree, "final_tree_sha256": final_tree,
                 "files": {path: {"before": baseline_files.get(path), "after": final_files.get(path)}
                           for path in sorted(set(baseline_files) | set(final_files)) if baseline_files.get(path) != final_files.get(path)}}
        events = parse_event_stream(artifacts / "events.jsonl")
        try: checked = checker(bound_root / metadata["checker_path"], slot["task_id"], workspace, min(300, max(0.001, deadline - clock()))) if error is None else {"valid": False, "resolved": None, "integrity": True, "stdout": "", "stderr": ""}
        except Exception as exc: checked = {"valid": False, "resolved": None, "integrity": True, "stdout": "", "stderr": "", "error": type(exc).__name__}
        try: after = _bound(design_path, design, slot["label"], slot["task_id"])[3]
        except (OSError, ValueError, KeyError, StopIteration, json.JSONDecodeError): after = {}
        shape = isinstance(checked, dict) and type(checked.get("valid")) is bool and type(checked.get("integrity")) is bool and isinstance(checked.get("stdout"), str) and isinstance(checked.get("stderr"), str) and ((checked["valid"] and type(checked.get("resolved")) is bool) or (not checked["valid"] and checked.get("resolved") is None))
        integrity = bool(shape and checked["integrity"] and after == before and contracts_before == contracts_after)
        valid = bool(shape and checked["valid"] and result is not None and not result.interrupted and error is None)
        resolved = (False if result and result.timed_out else checked["resolved"]) if valid else None
        usage_reported = events.usage.get("usage_reported") is True
        usage = {name: events.usage.get("reasoning_output_tokens" if name == "reasoning_tokens" else name) if usage_reported else None for name in TOKEN_FIELDS}
        row = {**slot, "session_id": f"session:{slot['slot_id']}", "workspace_id": f"workspace:{slot['slot_id']}", "raw_artifact_path": str(directory.relative_to(run_dir)), **before,
               "observation_valid": valid, "objective_resolved": resolved, "subject_integrity": integrity, "duration_seconds": max(0.0, clock() - started),
               "usage": usage, "usage_reported": usage_reported, "tool_calls": len(events.commands) if events.valid else None,
               "tool_events_reported": events.valid, "raw_capture_path": str((artifacts / "events.jsonl").relative_to(run_dir)),
               "baseline_tree_sha256": baseline_tree, "final_tree_sha256": final_tree, "workspace_patch": patch,
               "workspace_snapshot_path": str(workspace.relative_to(run_dir)), "workspace_contract_hashes": {"before": contracts_before, "after": contracts_after},
               "runner": {"status": getattr(result, "status", "EXCEPTION"), "exit_code": getattr(result, "exit_code", None), "timed_out": bool(result and result.timed_out), "interrupted": bool(result and result.interrupted), "error": error}, "checker": checked,
               }
        write_json(directory / "slot.json", row); evidence["observations"].append(row)
        if not integrity: evidence["errors"].append("mechanical input or checker integrity drift"); stopped = True; return "stopped"
        return "valid" if valid else "invalid"
    def wave(name: str) -> None:
        nonlocal retry, stopped
        scheduled = build_schedule(design, evidence["task_ids"], waves=("controls", "real") if name == "real" else ("controls",), retry=retry); base = [slot for slot in scheduled if slot["wave"] == name and slot["block_attempt"] == 1]
        for task_id in dict.fromkeys(slot["task_id"] for slot in base):
            states = [launch(slot) for slot in base if slot["task_id"] == task_id]
            if stopped: break
            if "invalid" in states:
                if retry is not None: evidence["errors"].append("second infrastructure-invalid block"); stopped = True; break
                retry = (name, task_id); repeated = [slot for slot in build_schedule(design, evidence["task_ids"], waves=("controls", "real") if name == "real" else ("controls",), retry=retry) if slot["wave"] == name and slot["task_id"] == task_id and slot["block_attempt"] == 2]
                repeated_states = [launch(slot) for slot in repeated]
                if stopped or any(state != "valid" for state in repeated_states): evidence["errors"].append("retry remained infrastructure-invalid"); stopped = True; break
    if not stopped: wave("controls")
    evidence["integrity_hashes"]["end"] = integrity_snapshot(design_path, design)
    control_report = analyze(design, evidence)
    if not stopped and control_report["run_status"] == "CONTROL_PASSED": wave("real")
    evidence["integrity_hashes"]["end"] = integrity_snapshot(design_path, design)
    if evidence["integrity_hashes"]["start"] != evidence["integrity_hashes"]["end"]:
        evidence["errors"].append("protected input hash drift")
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


def _artifact_evidence_valid(item):
    return ("git_integrity" not in item and isinstance((patch := item.get("workspace_patch")), dict)
            and _SHA256.fullmatch(str(item.get("baseline_tree_sha256", ""))) is not None
            and _SHA256.fullmatch(str(item.get("final_tree_sha256", ""))) is not None
            and patch.get("baseline_tree_sha256") == item["baseline_tree_sha256"]
            and patch.get("final_tree_sha256") == item["final_tree_sha256"] and isinstance(patch.get("files"), dict)
            and isinstance((contracts := item.get("workspace_contract_hashes")), dict)
            and isinstance(contracts.get("before"), dict) and contracts.get("before") == contracts.get("after")
            and not isinstance(item.get("duration_seconds"), bool) and isinstance(item.get("duration_seconds"), (int, float))
            and item["duration_seconds"] >= 0 and isinstance((usage := item.get("usage")), dict)
            and ((item.get("usage_reported") is True and all(type(usage.get(field)) is int and usage[field] >= 0 for field in TOKEN_FIELDS))
                 or (item.get("usage_reported") is False and all(usage.get(field) is None for field in TOKEN_FIELDS)))
            and ((item.get("tool_events_reported") is True and type(item.get("tool_calls")) is int and item["tool_calls"] >= 0)
                 or (item.get("tool_events_reported") is False and item.get("tool_calls") is None)))


def _validate_evidence(design: dict[str, Any], evidence: Any) -> tuple[tuple[str, ...], list[dict[str, Any]], dict[tuple[str, str], dict[str, Any]], str, int]:
    if (not isinstance(evidence, dict) or evidence.get("schema_version") != 2
            or "wave_hashes" in evidence or "oracle_controls_passed" in evidence):
        raise ValueError("raw evidence envelope invalid")
    hashes = evidence.get("integrity_hashes")
    if not isinstance(hashes, dict) or not isinstance(hashes.get("start"), dict) or hashes.get("start") != hashes.get("end"):
        raise ValueError("integrity start/end hash drift")
    start = hashes["start"]
    if (start.get("task_tree_sha256") != design["task_pack"]["tree_sha256"]
            or start.get("checker_hashes") != {name: item["checker_sha256"] for name, item in design["task_pack"]["repositories"].items()}
            or start.get("treatment_hashes") != {label: item["sha256"] for label, item in design["bindings"].items()}
            or any(_SHA256.fullmatch(str(start.get(f"{name}_sha256", ""))) is None for name in ("evaluator", "design", "analysis", "wrapper"))):
        raise ValueError("frozen integrity hash mismatch")
    _validate_receipt_payload(design, start, evidence.get("qualification_receipt"))
    if evidence.get("errors"):
        raise ValueError("; ".join(str(value) for value in evidence["errors"]))
    tasks, observations = _tasks(design, evidence.get("task_ids", ())), evidence.get("observations")
    if not isinstance(observations, list) or not observations or len(observations) > design["calls"]["absolute_cap"]:
        raise ValueError("raw observations missing or absolute call cap exceeded")
    retries = {(item.get("wave"), item.get("task_id")) for item in observations if isinstance(item, dict) and item.get("block_attempt") == 2}
    if len(retries) > 1:
        raise ValueError("more than one task block was retried")
    phase = "full" if any(isinstance(item, dict) and item.get("wave") == "real" for item in observations) else "controls"
    retry = next(iter(retries), None)
    expected = build_schedule(design, tasks, waves=("controls", "real") if phase == "full" else ("controls",), retry=retry)
    slot_fields = ("launch_index", "wave", "task_id", "block_attempt", "label", "slot_id")
    if len(expected) != len(observations) or any(not isinstance(item, dict) or tuple(item.get(key) for key in slot_fields) != tuple(slot[key] for key in slot_fields) for item, slot in zip(observations, expected)):
        raise ValueError("launched calls do not match the deterministic complete-block schedule")
    if any(any(not isinstance(value, str) or not value for value in (item.get(field) for item in observations))
           or len({item.get(field) for item in observations}) != len(observations)
           for field in ("session_id", "workspace_id", "raw_artifact_path", "raw_capture_path", "workspace_snapshot_path")):
        raise ValueError("raw and snapshot paths must be unique")
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
        if not _artifact_evidence_valid(item):
            raise ValueError("observation evidence invalid")
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
    except (KeyError, TypeError, ValueError, RuntimeError) as exc:
        return {**base, "run_status": "INVALID", "verdict": "INVALID", "reasons": [str(exc)]}
    aa = compare(selected, tasks, ("C1",), ("C2",), design)
    harmful = compare(selected, tasks, ("C1",), ("H",), design)
    favorable = sum(row["difference_b_minus_a"] < 0 for row in harmful["tasks"])
    adverse = sum(row["difference_b_minus_a"] > 0 for row in harmful["tasks"])
    gates = {"offline_null": offline_null_calibration()["passed"],
             "oracle_qualification": True,
             "aa": aa["outcome"] == "INCONCLUSIVE",
             "known_better": harmful["outcome"] == "A_BETTER" and favorable >= 6 and adverse == 0}
    controls_passed = all(gates.values())
    real = compare(selected, tasks, ("A1", "A2"), ("B1", "B2"), design) if phase == "full" else None
    if phase == "full" and not controls_passed:
        verdict, status, reasons = "INVALID", "STOP/REDESIGN", ["real wave launched without passing every control gate"]
    else:
        verdict, status, reasons = (real["outcome"], "COMPLETE", []) if real else ("INCONCLUSIVE", "CONTROL_PASSED" if controls_passed else "STOP/REDESIGN", [])
    token_complete = all(item["usage_reported"] for item in observations)
    tool_complete = all(item["tool_events_reported"] for item in observations)
    efficiency = {field: sum(item["usage"][field] for item in observations) if token_complete else None for field in TOKEN_FIELDS}
    efficiency.update({"launched_calls": len(observations), "superseded_calls": superseded,
                       "duration_seconds": round(sum(item["duration_seconds"] for item in observations), 6),
                       "token_evidence_complete": token_complete, "tool_evidence_complete": tool_complete,
                       "tool_calls": sum(item["tool_calls"] for item in observations) if tool_complete else None})
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
    parser = argparse.ArgumentParser(description="Qualify, run, or replay the frozen CODER outcome MVP. Only run makes model calls.")
    parser.add_argument("--experiment", type=Path, default=DEFAULT_DESIGN)
    commands = parser.add_subparsers(dest="command", required=True)
    qualification = commands.add_parser("qualify", help="run all 120 deterministic offline oracle checks")
    qualification.add_argument("output_dir", type=Path)
    qualification.add_argument("--authoritative", action="store_true", help="require clean OAuth preflight and issue a commit-bound receipt")
    replay = commands.add_parser("replay", help="regenerate deterministic reports from raw observations without model calls")
    replay.add_argument("observations", type=Path); replay.add_argument("output_dir", type=Path)
    run = commands.add_parser("run", help="run the separately authorized, receipt-gated live demonstration")
    run.add_argument("run_dir", type=Path)
    run.add_argument("qualification_receipt", type=Path)
    args = parser.parse_args(argv)
    try:
        design = load_design(args.experiment)
        if args.command == "qualify":
            result = qualify(args.experiment, args.output_dir, authoritative=args.authoritative)
            print(f"QUALIFICATION: {'PASS' if result['passed'] else 'FAIL'}\nRESULTS: {args.output_dir / 'qualification-results.json'}")
            return 0 if result["passed"] else 1
        if args.command == "run":
            report = run_demonstration(args.experiment, args.run_dir, args.qualification_receipt)
            print(f"VERDICT: {report['verdict']}\nREPORT: {args.run_dir / 'reports/report.md'}")
            return 1 if report["verdict"] == "INVALID" else 0
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
