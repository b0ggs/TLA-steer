"""Frozen M2 beneficial-sensitivity lifecycle and offline replay."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import random
import re
import signal
import shutil
import stat
import subprocess
import sys
import tempfile
import time
from dataclasses import asdict, make_dataclass
from fractions import Fraction
from pathlib import Path, PurePosixPath
from typing import Any, Iterable, Sequence

from .hashing import sha256_file, tree_sha256
from .wrapper import WRAPPER_PROMPT

DEFAULT_EXPERIMENT = Path("experiments/coder-beneficial-sensitivity-m2.json")
SCHEMA = "mdseval.coder-beneficial-sensitivity-m2-timeout-v1"
TASK_SCHEMA = "mdseval.coder-beneficial-sensitivity-m2-task-v1"
CHECK_SCHEMA = "mdseval.coder-beneficial-sensitivity-m2-check-v1"
TASKS = tuple(f"{kind}-{i:02d}" for kind in ("bug", "feature", "integration", "refactor-data") for i in range(1, 6))
STRATA = ("bug", "feature", "integration", "refactor-data")
STAGES = ("smoke", "calibration", "controls", "helpful")
EXPECTED_FINAL = b"IMPLEMENTED\nSMOKE_READY\n"
SHA256 = re.compile(r"^[0-9a-f]{64}$")
COMMIT = re.compile(r"^[0-9a-f]{40,64}$")
SAFE_ID = re.compile(r"^[a-z0-9][a-z0-9._-]*$")
CLAIM = ("Under the frozen diagnostic conditions, identical null files did not produce a winner under the "
         "predeclared decision rule, the harmful instruction lost in the expected direction, and the helpful "
         "instruction produced an observed macro-average increase in complete task resolution of at least 0.20 "
         "while rejecting the taskwise no-effect/exchangeability null at exact two-sided p <= 0.05.")
M2_4_2_CLOSURE, M2_4_2_CLOSURE_SHA256 = Path("experiments/coder-beneficial-sensitivity-m2-4-2-closure.json"), "e2ca4a05d98dd92b906ff5d294a6ad86da7b9224f9f1e38d6c57033742b05c67"
def canonical(value: object) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False) + "\n").encode()


def digest(value: object) -> str:
    return hashlib.sha256(canonical(value)).hexdigest()


def fraction(value: Fraction) -> dict[str, Any]:
    return {"numerator": value.numerator, "denominator": value.denominator, "value": float(value)}


def _safe(value: Any, label: str) -> PurePosixPath:
    if not isinstance(value, str):
        raise ValueError(f"{label} must be a relative POSIX path")
    path = PurePosixPath(value)
    if path.is_absolute() or not path.parts or ".." in path.parts or any(x in {"", "."} for x in path.parts):
        raise ValueError(f"unsafe {label}")
    return path


def _root(path: Path) -> Path:
    return path.resolve().parent.parent


def _strict_keys(value: Any, keys: set[str], label: str) -> dict[str, Any]:
    if not isinstance(value, dict) or set(value) != keys:
        raise ValueError(f"{label} keys mismatch")
    return value


def _bound_file(root: Path, binding: Any, label: str) -> Path:
    _strict_keys(binding, {"path", "sha256"}, label)
    path = root / _safe(binding["path"], label)
    if path.is_symlink() or not path.is_file() or not SHA256.fullmatch(binding["sha256"]):
        raise ValueError(f"missing or unsafe {label}")
    if sha256_file(path) != binding["sha256"]:
        raise ValueError(f"{label} hash drift")
    return path


def load_design(path: Path | str = DEFAULT_EXPERIMENT) -> dict[str, Any]:
    """Validate the frozen design and every governed input byte."""
    path = Path(path)
    design = json.loads(path.read_text(encoding="utf-8"))
    _strict_keys(design, {"schema", "experiment", "protocol", "runtime", "artifacts", "qualification",
                          "randomization", "calls", "stages", "analysis", "evidence", "commands"}, "design")
    if design["schema"] != SCHEMA or design["experiment"] != "coder-beneficial-sensitivity-m2-timeout-v1": raise ValueError("wrong experiment schema or identity")
    runtime = _strict_keys(design["runtime"], {"adapter", "model", "reasoning_effort", "sandbox", "approval_policy",
        "subagents_enabled", "ephemeral", "network_for_agent_commands", "timeout_seconds", "max_parallel_runs",
        "qualitative_judge_calls", "authentication_mode"}, "runtime")
    if runtime != {"adapter":"CodexCLI.run","model":"gpt-5.6-sol","reasoning_effort":"high","sandbox":"workspace-write","approval_policy":"never","subagents_enabled":False,"ephemeral":True,"network_for_agent_commands":False,"timeout_seconds":300,"max_parallel_runs":1,"qualitative_judge_calls":0,"authentication_mode":"chatgpt_oauth"}: raise ValueError("frozen Sol/high runtime mismatch")
    expected_protocol = {"version":"0.3","base_protocol_sha256":"4384a005b7d934b86ef91dd7d7fa6b9b46c2374fd7790bd89f8ed1a2222c6b0d","m2_2_completion_sha256":"bd02f51b1ca9095c4b4d9cadcd89099c32229e9f215beb310cee2ce459fb0a7e","m2_3_authority_sha256":"22dfe34312cac1d6fb7003f84444478c3755c127246b0b8c21d218bc521aece1","m2_3_closure_sha256":"34f1d48d3b96dab4ef08c429353a32cec2c70248e7899cff08b7d256e8c1a591","m2_3_1_authority_sha256":"b5a21bc97954d5f71eb474e41665bc51627e21b7eeedd7cb568830363cd17341","m2_3_1_closure_sha256":"2678241683974dea11841049bef2490d96ea4f1613f7ffbadde234006cdc1d94","m2_4_authority_sha256":"227c8a5b152421973a837d664f1c226af79b0ea0b4f7614835f4baff5accb901","measurement_base_commit":"bfda5f78e418784f6390cc4aead927bbd7b896ff"}
    if design["protocol"] != expected_protocol: raise ValueError("authority binding mismatch")
    root, artifacts = _root(path), design["artifacts"]
    required = {"access","helpful","helpful_authorship","harmful","null","master","task_authorship","task_reliability_authorship","oracle","wrapper","evaluator","tests"}
    _strict_keys(artifacts, required, "artifacts")
    paths = {k: _bound_file(root, v, k) for k, v in artifacts.items()}
    if paths["null"].read_bytes() or artifacts["null"]["sha256"] != hashlib.sha256(b"").hexdigest(): raise ValueError("null treatment must be exactly zero bytes")
    if artifacts["harmful"]["sha256"] != "aaf88530c73385ad6d38a45dae67be4872e650afc27d620a8d640430e2ec5606": raise ValueError("harmful treatment drift")
    master = json.loads(paths["master"].read_text())
    if master.get("task_ids") != list(TASKS) or set(master.get("strata", {})) != set(STRATA): raise ValueError("master task population mismatch")
    if any(master["strata"].get(s) != [t for t in TASKS if t.startswith(s + "-")] for s in STRATA): raise ValueError("master stratum balance mismatch")
    records = master.get("tasks")
    oracle = json.loads(paths["oracle"].read_text())
    variants = oracle.get("tasks")
    if not isinstance(records, list) or [x.get("id") for x in records] != list(TASKS): raise ValueError("master task records mismatch")
    if oracle.get("schema") != "mdseval.coder-beneficial-sensitivity-m2-oracles-v1" or set(variants or {}) != set(TASKS): raise ValueError("qualification oracle mismatch")
    owner = json.loads(paths["task_reliability_authorship"].read_text())
    outputs = owner.get("output_hashes", {})
    expected_outputs = {f"return/{r['path']}/{name}":r[key] for r in records for name,key in (("check.py","checker_sha256"),("task.json","task_json_sha256"))}
    expected_outputs["return/evals/m2/coder-beneficial-sensitivity/master.json"] = artifacts["master"]["sha256"]
    lines = sorted(f"644 {value} {key.removeprefix('return/')}\n".encode() for key,value in outputs.items())
    if outputs != expected_outputs or hashlib.sha256(b"".join(lines)).hexdigest() != "a9bcb692d71290ed7b5bddf5bf65a80a022bfb9e491c03ca9ef59480c001e355" or owner.get("payload_root_sha256") != "a9bcb692d71290ed7b5bddf5bf65a80a022bfb9e491c03ca9ef59480c001e355": raise ValueError("owner return-relative payload mismatch")
    for record in records:
        task_dir = root / _safe(record["path"], "task path")
        task_path, fixture = task_dir / "task.json", task_dir / "fixture"
        if task_dir.is_symlink() or not task_dir.is_dir(): raise ValueError(f"missing task {record['id']}")
        task = json.loads(task_path.read_text())
        if (task.get("schema") != TASK_SCHEMA or task.get("id") != record["id"] or task.get("stratum") != record["stratum"]
                or sha256_file(task_path) != record["task_json_sha256"] or sha256_file(task_dir/"contract.md") != record["contract_sha256"]
                or sha256_file(task_dir/"check.py") != record["checker_sha256"] or task.get("fixture_sha256") != record["fixture_sha256"]):
            raise ValueError(f"task binding drift: {record['id']}")
        fixture_files = task.get("fixture_files")
        if not isinstance(fixture_files, list) or not fixture_files: raise ValueError(f"fixture inventory missing: {record['id']}")
        listed = {_safe(x["path"], "fixture file").as_posix() for x in fixture_files}
        actual = {x.relative_to(fixture).as_posix() for x in fixture.rglob("*") if x.is_file()
                  and not set(x.relative_to(fixture).parts) & {"__pycache__",".pytest_cache"} and not x.name.endswith((".pyc",".pyo"))}
        if listed != actual or any(sha256_file(fixture/_safe(x["path"],"fixture file")) != x["sha256"] for x in fixture_files): raise ValueError(f"fixture inventory drift: {record['id']}")
        requirements = {x.get("id") for x in task.get("requirements", []) if isinstance(x, dict)}
        matrix = task.get("requirement_to_negative_case_matrix")
        mutants = {x.get("id") for x in variants[record["id"] if record["id"] in variants else ""] if x.get("class") == "mutant"}
        if not 3 <= len(requirements) <= 5 or not isinstance(matrix, dict) or set(matrix) != requirements or any(not v or not set(v) <= mutants for v in matrix.values()): raise ValueError(f"incomplete negative-case matrix: {record['id']}")
    if design["qualification"] != {"task_count":20,"states_per_task":5,"repeats_per_state":3,"executions_per_task":15,"execution_count":300,"checker_timeout_seconds":60,"authoritative_receipt_after_final_freeze_only":True,"receipt_schema":"mdseval.coder-beneficial-sensitivity-m2-qualification-receipt-v1","internal_timeout_seconds":10,"execution_record_schema":"mdseval.coder-beneficial-sensitivity-m2-4-execution-v1","terminal_record_schema":"mdseval.coder-beneficial-sensitivity-m2-4-terminal-v1","required_state_order":["pristine","correct-a","correct-b","mutant-a","mutant-b"]}: raise ValueError("qualification design mismatch")
    if design["randomization"] != {"selection_seed":"coder-m2-selection-20260810-v1","schedule_seed":"coder-m2-schedule-20260810-v1",
        "power_grid_seed":20260810,"post_calibration_power_seed":20260811,"bootstrap_seed":20260812,
        "opaque_ids":{"smoke":["S0"],"calibration":["K0"],"controls":["C0","C1","C2"],"helpful":["P0","P1"]}}: raise ValueError("randomization mismatch")
    if design["calls"] != {"smoke":1,"calibration":120,"controls":48,"helpful":128,"base_cap":297,
        "fallback_by_stage":{"smoke":0,"calibration":6,"controls":3,"helpful":8},"absolute_cap":314,"qualitative_judge_calls":0}: raise ValueError("call caps mismatch")
    if set(design["stages"]) != set(STAGES) or any(x.get("separate_authorization_required") is not True for x in design["stages"].values()): raise ValueError("stage authorization design mismatch")
    expected_analysis = {"effect_floor":{"numerator":1,"denominator":5},"alpha":{"numerator":1,"denominator":20},
        "selection_successes":[1,2,3,4,5],"selected_per_stratum":4,"helpful_repeats_per_arm":4,"power_iterations":100000,
        "power_floor":{"numerator":4,"denominator":5},"planning_effect":{"numerator":3,"denominator":10},
        "bootstrap_iterations":100000,"bootstrap_lower_index":2499,"bootstrap_upper_index":97500,
        "verdicts":["SENSITIVITY_DEMONSTRATED","SENSITIVITY_NOT_DEMONSTRATED","INVALID"]}
    if design["analysis"] != expected_analysis: raise ValueError("analysis rules mismatch")
    return design


def runner_config(design: dict[str, Any]) -> Any:
    try:
        from .config import RunnerConfig
    except ModuleNotFoundError:
        RunnerConfig = make_dataclass("RunnerConfig", [(x, object) for x in ("type","model","reasoning_effort","sandbox",
            "approval_policy","subagents_enabled","ephemeral","network_for_agent_commands","timeout_seconds","max_parallel_runs")], frozen=True)
    r = design["runtime"]
    return RunnerConfig("codex_cli", r["model"], r["reasoning_effort"], r["sandbox"], r["approval_policy"], r["subagents_enabled"],
                        r["ephemeral"], r["network_for_agent_commands"], r["timeout_seconds"], r["max_parallel_runs"])


def _process_cleanup(run: subprocess.Popen[bytes], terminate: bool) -> dict[str, Any]:
    sent_term = sent_kill = waited = False
    error = None
    def alive() -> bool:
        try: return os.killpg(run.pid,0) is None
        except ProcessLookupError: return False
        except PermissionError: return True
    try:
        if terminate or alive():
            sent_term = alive()
            if sent_term: os.killpg(run.pid,signal.SIGTERM)
            try: run.wait(timeout=.5); waited = True
            except subprocess.TimeoutExpired: pass
            deadline = time.monotonic() + .5
            while alive() and time.monotonic() < deadline: time.sleep(.01)
            sent_kill = alive()
            if sent_kill: os.killpg(run.pid,signal.SIGKILL)
            deadline = time.monotonic() + .5
            while alive() and time.monotonic() < deadline: time.sleep(.01)
        if not waited: run.wait(timeout=.5); waited = True
    except Exception as exc: error = type(exc).__name__
    gone = not alive()
    return {"term_sent":sent_term,"kill_sent":sent_kill,"direct_checker_waited":waited,"no_live_process_group_members":gone,"succeeded":waited and gone,"error":error}

def _checker(path: Path, task_id: str, workspace: Path, timeout: int = 60) -> dict[str, Any]:
    command = [str(Path(sys.executable).resolve()),str(path),str(workspace)]
    environment = {k:v for k,v in os.environ.items() if k in {"PATH","TMPDIR","TMP","TEMP","LANG","LC_ALL"}}
    run,error = None,None
    stdout,stderr,disposition = b"",b"","launch-error"
    cleanup = {"term_sent":False,"kill_sent":False,"direct_checker_waited":False,"no_live_process_group_members":True,"succeeded":False,"error":None}
    try:
        run = subprocess.Popen(command,stdout=subprocess.PIPE,stderr=subprocess.PIPE,env=environment,start_new_session=True)
        try: stdout,stderr = run.communicate(timeout=timeout)
        except Exception as exc:
            disposition = "outer-timeout" if isinstance(exc,subprocess.TimeoutExpired) else "process-error"
            error = type(exc).__name__
            if isinstance(exc,subprocess.TimeoutExpired): stdout,stderr = exc.output or b"",exc.stderr or b""
        else: disposition = "completed"
        cleanup = _process_cleanup(run,disposition != "completed")
        if disposition != "completed":
            try: final_stdout,final_stderr = run.communicate(timeout=.5); stdout = final_stdout if final_stdout.startswith(stdout) else stdout+final_stdout; stderr = final_stderr if final_stderr.startswith(stderr) else stderr+final_stderr
            except Exception as exc: error = error or type(exc).__name__
    except Exception as exc: error = type(exc).__name__
    payload = {}
    try: payload = json.loads(stdout)
    except (UnicodeDecodeError,json.JSONDecodeError): pass
    keys = {"schema","task_id","environment","requirements","regressions","integrity","resolved"}
    sections = ("environment","requirements","regressions","integrity")
    leaves = list(payload.get("requirements",{}).values()) + list(payload.get("regressions",{}).values()) if isinstance(payload,dict) else []
    try: payload_bytes = canonical(payload)
    except (TypeError,ValueError): payload_bytes = b""
    timeout_detail = b'"detail":"timeout"' in payload_bytes
    valid = bool(run and disposition == "completed" and cleanup["succeeded"] and run.returncode == 0 and not stderr
        and isinstance(payload,dict) and set(payload) == keys and payload.get("schema") == CHECK_SCHEMA and payload.get("task_id") == task_id
        and type(payload.get("resolved")) is bool and all(isinstance(payload.get(k),dict) for k in sections)
        and set(payload["environment"]) == {"passed","checks"} and type(payload["environment"]["passed"]) is bool and isinstance(payload["environment"]["checks"],list) and all(isinstance(x,str) for x in payload["environment"]["checks"])
        and set(payload["integrity"]) == {"passed","detail"} and type(payload["integrity"]["passed"]) is bool and isinstance(payload["integrity"]["detail"],str)
        and all(isinstance(x,dict) and set(x) == {"passed","detail"} and type(x["passed"]) is bool and isinstance(x["detail"],str) for x in leaves)
        and stdout == payload_bytes and not timeout_detail)
    mechanical = bool(valid and payload["environment"].get("passed") is True and payload["integrity"].get("passed") is True)
    resolved = bool(mechanical and payload["resolved"] and all(x["passed"] for x in leaves))
    raw = {"command":command,"environment":environment,"disposition":disposition,"exit_code":run.returncode if run else None,"stdout_hex":stdout.hex(),"stderr_hex":stderr.hex(),"stdout_sha256":hashlib.sha256(stdout).hexdigest(),"stderr_sha256":hashlib.sha256(stderr).hexdigest(),"exception":error,"process_cleanup":cleanup}
    return {"valid":valid,"resolved":resolved if valid else None,"mechanical":mechanical,"exit_code":raw["exit_code"],"stdout_sha256":raw["stdout_sha256"],"stderr":stderr.decode("utf-8","replace"),"payload":payload,"infrastructure_invalid":bool(run is None or disposition != "completed" or not cleanup["succeeded"] or timeout_detail),"raw":raw}

def _manifest(root: Path) -> list[dict[str, Any]]:
    def row(path: Path, mode: int) -> dict[str, Any]:
        kind = "symlink" if stat.S_ISLNK(mode) else "file" if stat.S_ISREG(mode) else "directory" if stat.S_ISDIR(mode) else "special"
        return {"path":path.relative_to(root).as_posix(),"type":kind,"mode":f"{stat.S_IMODE(mode):04o}",**({"sha256":sha256_file(path)} if kind == "file" else {})}
    return [row(path,path.lstat().st_mode) for path in sorted(root.rglob("*"),key=lambda p:p.relative_to(root).as_posix().encode())]

def _workspace_ok(before: list[dict[str, Any]], after: list[dict[str, Any]]) -> bool:
    old,new = ({x["path"]:x for x in rows} for rows in (before,after))
    allowed = lambda key,row: (row["type"] == "directory" and PurePosixPath(key).name == "__pycache__" and any(PurePosixPath(name).parent == PurePosixPath(key) and new[name]["type"] == "file" and PurePosixPath(name).suffix == ".pyc" for name in set(new)-set(old))) or (row["type"] == "file" and PurePosixPath(key).parent.name == "__pycache__" and PurePosixPath(key).suffix == ".pyc")
    return set(old) <= set(new) and all(new[key] == value for key,value in old.items()) and all(allowed(key,new[key]) for key in set(new)-set(old))

def _publish(path: Path, value: object) -> str:
    data = canonical(value)
    path.parent.mkdir(parents=True,exist_ok=True)
    descriptor,temporary = tempfile.mkstemp(prefix=".m2-4-",dir=path.parent)
    try:
        with os.fdopen(descriptor,"wb",buffering=0) as stream:
            stream.write(data)
            os.fsync(stream.fileno())
        os.chmod(temporary,0o644)
        os.link(temporary,path)
    finally:
        if os.path.exists(temporary): os.unlink(temporary)
    return hashlib.sha256(data).hexdigest()
class _TerminalPublicationError(Exception): pass
class _OutputCreationError(_TerminalPublicationError): pass
class _RawRootCreationError(Exception): pass
def _publish_terminal(path: Path, value: object) -> str:
    try: return _publish(path,value)
    except Exception as exc: raise _TerminalPublicationError(exc) from exc
def _copy_state(fixture: Path, workspace: Path, variant: dict[str, Any] | None) -> list[dict[str, Any]]:
    source = _manifest(fixture)
    if fixture.is_symlink() or any(x["type"] not in {"file","directory"} or any(p.startswith(".") for p in PurePosixPath(x["path"]).parts) or "__pycache__" in PurePosixPath(x["path"]).parts or x["path"].endswith((".pyc",".pyo")) for x in source): raise ValueError("qualification fixture path/type/cache invalid")
    shutil.copytree(fixture,workspace)
    if variant:
        for name in variant.get("remove",[]):
            target = workspace/_safe(name,"oracle removal")
            if target.is_symlink() or not target.is_file(): raise ValueError("oracle removal target invalid")
            target.unlink()
        for name,contents in variant.get("files",{}).items():
            target = workspace/_safe(name,"oracle file")
            if any(part.startswith(".") for part in target.relative_to(workspace).parts): raise ValueError("hidden oracle path")
            target.parent.mkdir(parents=True,exist_ok=True)
            target.write_text(contents,encoding="utf-8")
    return _manifest(workspace)

def _qualify_started(design_path: Path | str, output: Path | str, *, authoritative: bool = False,
                     final_freeze_receipt: Path | None = None, verified_commit: str | None = None, checker: Any = _checker) -> dict[str, Any]:
    """Run the frozen matrix once and publish immutable external evidence."""
    design = load_design(design_path)
    root,output = _root(Path(design_path)),Path(output)
    if authoritative:
        if final_freeze_receipt is None or not verified_commit or not COMMIT.fullmatch(verified_commit): raise RuntimeError("authoritative qualification requires final-freeze receipt and exact commit")
        freeze = _json(Path(final_freeze_receipt))
    else:
        if verified_commit is not None: raise RuntimeError("provisional qualification cannot bind a commit")
        gate = Path(final_freeze_receipt) if final_freeze_receipt else root/"experiments/coder-beneficial-sensitivity-m2-4-freeze.json"
        freeze = _json(gate)
        if freeze.get("schema") != "mdseval.coder-beneficial-sensitivity-m2-4-freeze-v1" or freeze.get("status") != "PASS" or freeze.get("authoritative") is not False: raise RuntimeError("M2.4 PASS freeze required")
    try: output.mkdir(parents=True,exist_ok=False)
    except Exception as exc: raise _OutputCreationError(exc) from exc
    raw_root = output/"raw"
    try: raw_root.mkdir()
    except Exception as exc: raise _RawRootCreationError(exc) from exc
    packet = output.parent.parent if output.parent.name == "return" and output.name == "qualification-evidence" else output.parent
    work_root = packet/"scratch/qualification"
    failure = None
    try: work_root.mkdir(parents=True,exist_ok=False)
    except Exception as exc: failure = f"workspace root invalid: {type(exc).__name__}"
    master = json.loads((root/design["artifacts"]["master"]["path"]).read_text())
    oracle = json.loads((root/design["artifacts"]["oracle"]["path"]).read_text())["tasks"]
    governed_before = {"tasks":_manifest(root/"evals/m2/coder-beneficial-sensitivity"),"controls":_manifest(root/"controls/coder")}
    before = {r["id"]:tree_sha256(root/r["path"]) for r in master["tasks"]}
    rows,record_hashes,repeated,failed_by_mutant = [],[],{},{}
    if failure is None and (os.name != "posix" or not all(hasattr(os,name) for name in ("killpg","getpgid"))): failure = "POSIX process-group capability gate"
    for record in master["tasks"] if failure is None else []:
        task_id,task_dir = record["id"],root/record["path"]
        task = json.loads((task_dir/"task.json").read_text())
        requirements,regressions = ({x["id"] for x in task[key]} for key in ("requirements","regressions"))
        variants = {x["id"]:x for x in oracle[task_id]}
        if set(variants) != {"correct-a","correct-b","mutant-a","mutant-b"} or {variants[x]["class"] for x in ("correct-a","correct-b")} != {"correct"}:
            failure = f"oracle states invalid: {task_id}"
            break
        failed_by_mutant[task_id] = {}
        for state in design["qualification"]["required_state_order"]:
            variant = None if state == "pristine" else variants[state]
            expected = state.startswith("correct")
            repeated[task_id,state] = []
            for repeat in range(1,4):
                index = len(rows)+1
                workspace = work_root/f"workspace-{index:04d}"
                try: workspace_before = _copy_state(task_dir/"fixture",workspace,variant)
                except Exception as exc:
                    failure = f"materialization failed: {type(exc).__name__}"
                    break
                try:
                    checked = checker(task_dir/"check.py",task_id,workspace,design["qualification"]["checker_timeout_seconds"])
                except Exception as exc:
                    checked = {"valid":False,"resolved":None,"mechanical":False,"payload":{},"infrastructure_invalid":True,"raw":{"command":[str(Path(sys.executable).resolve()),str(task_dir/"check.py"),str(workspace)],"environment":{},"disposition":"injected-exception","exception":type(exc).__name__,"process_cleanup":{"succeeded":False}}}
                workspace_after = _manifest(workspace)
                governed_after = {"tasks":_manifest(root/"evals/m2/coder-beneficial-sensitivity"),"controls":_manifest(root/"controls/coder")}
                payload = checked.get("payload",{})
                req = payload.get("requirements",{}) if isinstance(payload,dict) else {}
                reg = payload.get("regressions",{}) if isinstance(payload,dict) else {}
                try: payload_bytes = canonical(payload)
                except (TypeError,ValueError): payload_bytes = b""
                timeout_detail = b'"detail":"timeout"' in payload_bytes
                complete = bool(payload_bytes and checked.get("valid") is True and isinstance(payload,dict) and set(payload) == {"schema","task_id","environment","requirements","regressions","integrity","resolved"} and payload.get("schema") == CHECK_SCHEMA and payload.get("task_id") == task_id and type(payload.get("resolved")) is bool and isinstance(payload.get("environment"),dict) and isinstance(payload.get("integrity"),dict) and set(req) == requirements and set(reg) == regressions and all(isinstance(value,dict) and set(value) == {"passed","detail"} and type(value["passed"]) is bool and isinstance(value["detail"],str) for value in list(req.values())+list(reg.values())) and not timeout_detail)
                failed = {key for key,value in req.items() if value.get("passed") is not True} if complete else set()
                disposition = (state == "pristine" and checked.get("resolved") is False and bool(failed)) or (expected and checked.get("resolved") is True) or (state.startswith("mutant") and checked.get("resolved") is False and set(variant["expected_failed_requirements"]) <= failed)
                passed = bool(complete and checked.get("mechanical") is True and not checked.get("infrastructure_invalid") and disposition and (not expected or all(value.get("passed") is True for value in reg.values())) and governed_before == governed_after and _workspace_ok(workspace_before,workspace_after))
                payload_hash = hashlib.sha256(payload_bytes).hexdigest()
                row = {"task_id":task_id,"state":state,"repeat":repeat,"expected_resolved":expected,"valid":checked.get("valid"),"resolved":checked.get("resolved"),"mechanical":checked.get("mechanical"),"infrastructure_invalid":bool(checked.get("infrastructure_invalid") or timeout_detail),"failed_requirements":sorted(failed),"checker_payload":payload,"checker_payload_sha256":payload_hash,"passed":passed}
                raw = checked.get("raw") or {"command":[str(Path(sys.executable).resolve()),str(task_dir/"check.py"),str(workspace)],"environment":{},"disposition":"injected","process_cleanup":{"injected":True,"succeeded":True}}
                execution = {"schema":design["qualification"]["execution_record_schema"],"experiment":design["experiment"],"authoritative":False,"execution_index":index,"task_id":task_id,"state":state,"repeat":repeat,"checker_command":raw.get("command"),"checker_environment":raw.get("environment"),"checker_disposition":raw.get("disposition"),"raw_checker":raw,"checker_payload":payload,"checker_payload_sha256":payload_hash,"pre_state":{"governed":governed_before,"workspace":workspace_before},"post_state":{"governed":governed_after,"workspace":workspace_after},"process_cleanup":raw.get("process_cleanup"),"outcome":row}
                record_path = raw_root/f"execution-{index:04d}.json"
                try: record_hash = _publish(record_path,execution)
                except Exception as exc:
                    failure = f"execution evidence publication failed: {type(exc).__name__}"
                    break
                record_hashes.append({"path":record_path.relative_to(output).as_posix(),"sha256":record_hash})
                rows.append(row)
                repeated[task_id,state].append(payload_bytes)
                try:
                    shutil.rmtree(workspace)
                except Exception as exc:
                    failure = f"workspace deletion failed: {type(exc).__name__}"
                if not passed: failure = failure or f"execution {index} invalid"
                if failure: break
            if failure: break
            if len(set(repeated[task_id,state])) != 1:
                failure = f"nondeterministic payload: {task_id}/{state}"
                break
            if state.startswith("mutant"): failed_by_mutant[task_id][state] = set(rows[-1]["failed_requirements"])
        if failure: break
        matrix = task["requirement_to_negative_case_matrix"]
        observed = failed_by_mutant[task_id]
        if any(any(req not in observed.get(mutant,set()) for mutant in mutants) for req,mutants in matrix.items()) or set().union(*observed.values()) != requirements:
            failure = f"requirement matrix invalid: {task_id}"
            break
    after = {r["id"]:tree_sha256(root/r["path"]) for r in master["tasks"]}
    passed = failure is None and len(rows) == 300 and all(r["passed"] for r in rows) and before == after and (not authoritative or freeze.get("verified_commit") == verified_commit and freeze.get("status") == "PASS")
    terminal = {"schema":design["qualification"]["terminal_record_schema"],"experiment":design["experiment"],"authoritative":False,"status":"PASS" if passed else "FAIL","failure":failure,"execution_count":len(rows),"execution_records":record_hashes,"ordered_execution_records_sha256":digest(record_hashes),"raw_root_sha256":digest(record_hashes),"freeze_sha256":sha256_file(Path(final_freeze_receipt) if final_freeze_receipt else gate),"catchable_outcomes_recorded":not (failure or "").startswith("execution evidence publication failed"),"no_uncatchable_crash_durability_claim":True}
    bound = [{k:r[k] for k in ("task_id","state","repeat","expected_resolved","valid","resolved","mechanical","infrastructure_invalid","failed_requirements","checker_payload_sha256","passed")} for r in rows]
    result = {"schema":"mdseval.coder-beneficial-sensitivity-m2-qualification-results-v1","authoritative":authoritative,"status":"PASS" if passed else "FAIL","execution_count":len(rows),"python":{"executable":str(Path(sys.executable).resolve()),"version":sys.version},"input_hashes":{k:v["sha256"] for k,v in design["artifacts"].items()},"tree_hashes":{"before":before,"after":after},"results_sha256":digest(bound),"terminal_sha256":hashlib.sha256(canonical(terminal)).hexdigest(),"results":rows}
    if authoritative:
        _publish(output/"qualification-results.json",result)
        if passed:
            receipt = {"schema":design["qualification"]["receipt_schema"],"experiment":design["experiment"],"status":"PASS","verified_commit":verified_commit,"config_sha256":sha256_file(Path(design_path)),"evaluator_sha256":sha256_file(Path(__file__)),"governed_artifacts":result["input_hashes"],"python":result["python"],"final_freeze_receipt_sha256":sha256_file(Path(final_freeze_receipt)),"execution_count":300,"task_count":20,"state_count":100,"results_sha256":result["results_sha256"]}
            _publish(output/"qualification-receipt.json",receipt)
    _publish_terminal(output/"terminal.json",terminal)
    if authoritative and not passed: raise RuntimeError("authoritative qualification or final freeze failed")
    return result

def qualify(design_path: Path | str, output: Path | str, *, authoritative: bool = False,
            final_freeze_receipt: Path | None = None, verified_commit: str | None = None, checker: Any = _checker) -> dict[str, Any]:
    try: return _qualify_started(design_path,output,authoritative=authoritative,final_freeze_receipt=final_freeze_receipt,verified_commit=verified_commit,checker=checker)
    except _TerminalPublicationError as exc: raise exc.args[0]
    except Exception as exc:
        output=Path(output); raw_root=output/"raw"
        if not output.is_dir() or (not isinstance(exc,_RawRootCreationError) and not raw_root.is_dir()) or (output/"terminal.json").exists(): raise
        records=[]; rows=[]
        try:
            for index,path in enumerate(sorted(raw_root.glob("execution-*.json")),1):
                value=json.loads(path.read_bytes()); records.append({"path":path.relative_to(output).as_posix(),"sha256":sha256_file(path)}); rows.append(value["outcome"])
                if path.name!=f"execution-{index:04d}.json" or value.get("execution_index")!=index: raise ValueError("execution evidence sequence invalid")
        except Exception: records=[]; rows=[]
        packet=output.parent.parent if output.parent.name=="return" and output.name=="qualification-evidence" else output.parent
        try: shutil.rmtree(packet/"scratch/qualification")
        except Exception: pass
        design=json.loads(Path(design_path).read_text()); freeze_path=Path(final_freeze_receipt) if final_freeze_receipt else _root(Path(design_path))/"experiments/coder-beneficial-sensitivity-m2-4-freeze.json"
        terminal={"schema":design["qualification"]["terminal_record_schema"],"experiment":design["experiment"],"authoritative":False,"status":"FAIL","failure":f"qualification exception: {type(exc).__name__}","execution_count":len(rows),"execution_records":records,"ordered_execution_records_sha256":digest(records),"raw_root_sha256":digest(records),"freeze_sha256":sha256_file(freeze_path),"catchable_outcomes_recorded":False,"no_uncatchable_crash_durability_claim":True}
        try: terminal_sha=_publish_terminal(output/"terminal.json",terminal)
        except _TerminalPublicationError as failed: raise failed.args[0]
        bound=[{k:r[k] for k in ("task_id","state","repeat","expected_resolved","valid","resolved","mechanical","infrastructure_invalid","failed_requirements","checker_payload_sha256","passed")} for r in rows]
        return {"schema":"mdseval.coder-beneficial-sensitivity-m2-qualification-results-v1","authoritative":authoritative,"status":"FAIL","execution_count":len(rows),"python":{"executable":str(Path(sys.executable).resolve()),"version":sys.version},"input_hashes":{k:v["sha256"] for k,v in design["artifacts"].items()},"tree_hashes":{},"results_sha256":digest(bound),"terminal_sha256":terminal_sha,"results":rows}

def _order(seed: str, stage: str, round_id: int, task: str) -> bytes:
    return hashlib.sha256(f"{seed}|{stage}|{round_id}|{task}|BLOCK".encode()).digest()


def _arm_order(seed: str, stage: str, round_id: int, task: str, arm: str) -> bytes:
    return hashlib.sha256(f"{seed}|{stage}|{round_id}|{task}|{arm}|ARM".encode()).digest()


def build_master_schedules(design: dict[str, Any]) -> dict[str, Any]:
    seed, ids = design["randomization"]["schedule_seed"], design["randomization"]["opaque_ids"]
    result = {}
    for stage,(rounds,arms) in {"calibration":(range(1,7),ids["calibration"]),"controls":(range(1),ids["controls"]),"helpful":(range(1,5),ids["helpful"])}.items():
        base, per_task = [], {t:[] for t in TASKS}
        for round_id in rounds:
            for task in sorted(TASKS, key=lambda t:_order(seed, stage, round_id, t)):
                for arm in sorted(arms, key=lambda a:_arm_order(seed, stage, round_id, task, a)):
                    slot = {"slot_id":f"{stage}:base:r{round_id}:{task}:{arm}","stage":stage,"round":round_id,
                            "task_id":task,"opaque_arm_id":arm,"fallback":False}
                    base.append(slot); per_task[task].append(slot)
        fallback = {t:[{**x,"slot_id":x["slot_id"].replace(":base:",":fallback:"),"fallback":True} for x in per_task[t]] for t in TASKS}
        sentinels = {t:digest([x["slot_id"] for x in per_task[t]+fallback[t]]) for t in TASKS}
        ordered = sorted(TASKS, key=lambda t:_order(seed, stage, 0, t))
        result[stage] = {"base":base,"fallback_by_task":fallback,"block_sentinels":sentinels,
                         "stage_order_sentinel":digest([sentinels[t] for t in ordered])}
    return result


def filter_schedule(master: dict[str, Any], selected: Iterable[str], stage: str) -> dict[str, Any]:
    chosen = tuple(selected)
    if stage not in {"controls","helpful"} or len(chosen) != 16 or len(set(chosen)) != 16 or not set(chosen) <= set(TASKS):
        raise ValueError("filtered schedule requires exactly 16 master tasks")
    source = master[stage]; slots = [x for x in source["base"] if x["task_id"] in chosen]
    return {"stage":stage,"selected_ids":list(chosen),"source_stage_sentinel":source["stage_order_sentinel"],"slots":slots,"slots_sha256":digest(slots)}


def select_tasks(counts: dict[str, int], seed: str = "coder-m2-selection-20260810-v1") -> dict[str, Any]:
    if set(counts) != set(TASKS) or any(type(v) is not int or not 0 <= v <= 6 for v in counts.values()):
        raise ValueError("selection requires all 20 six-attempt counts")
    selected, ranking = [], {}
    for stratum in STRATA:
        all_rows = [{"task_id":t,"successes":counts[t],"eligible":1 <= counts[t] <= 5,
                     "tie_sha256":hashlib.sha256((seed+t).encode()).hexdigest()} for t in TASKS if t.startswith(stratum+"-")]
        eligible = sorted((x for x in all_rows if x["eligible"]), key=lambda x:(abs(x["successes"]-3),x["tie_sha256"]))
        ranking[stratum] = sorted(all_rows, key=lambda x:(not x["eligible"],abs(x["successes"]-3),x["tie_sha256"]))
        if len(eligible) < 4:
            return {"status":"SENSITIVITY_NOT_DEMONSTRATED","selected_ids":[],"ranking":ranking,"reason":f"fewer than four eligible tasks in {stratum}"}
        selected.extend(x["task_id"] for x in eligible[:4])
    return {"status":"PASS","selected_ids":sorted(selected),"ranking":ranking}


def exact_sign_test(differences: Sequence[Fraction]) -> dict[str, Any]:
    values, ways = [Fraction(x) for x in differences if x], {0:1}
    if len(differences) > 16: raise ValueError("at most sixteen task effects")
    if not values: return {"nonzero":0,"p_value":fraction(Fraction(1)),"effect_sum":fraction(Fraction())}
    denominator = math.lcm(*(x.denominator for x in values)); signed = [x.numerator*(denominator//x.denominator) for x in values]
    for magnitude in sorted(abs(x) for x in signed):
        nxt = {}
        for total,count in ways.items():
            nxt[total+magnitude] = nxt.get(total+magnitude,0)+count; nxt[total-magnitude] = nxt.get(total-magnitude,0)+count
        ways = nxt
    observed = abs(sum(signed)); p = Fraction(sum(n for total,n in ways.items() if abs(total) >= observed), 1 << len(values))
    return {"nonzero":len(values),"p_value":fraction(p),"effect_sum":fraction(sum(values, Fraction()))}


def _gate(diffs: Sequence[int]) -> bool:
    nz = [x for x in diffs if x]; ways = {0:1}
    for magnitude in sorted(abs(x) for x in nz):
        ways = _advance(ways, magnitude)
    return sum(n for total,n in ways.items() if abs(total) >= abs(sum(diffs))) * 20 <= (1 << len(nz))


def _advance(ways: dict[int,int], magnitude: int) -> dict[int,int]:
    result = {}
    for total,count in ways.items():
        result[total+magnitude] = result.get(total+magnitude,0)+count; result[total-magnitude] = result.get(total-magnitude,0)+count
    return result


def simulate_power(rates: Sequence[Fraction | float], seed: int, iterations: int = 100000) -> float:
    if len(rates) != 16 or iterations <= 0: raise ValueError("power simulation requires sixteen rates")
    rng, passed = random.Random(seed), 0
    for _ in range(iterations):
        diffs = []
        for rate in rates:
            n=float(rate); p=min(1.,n+.30); diffs.append(sum(rng.random()<p for _ in range(4))-sum(rng.random()<n for _ in range(4)))
        passed += sum(diffs) >= 13 and _gate(diffs)
    return passed/iterations


def verify_power(design: dict[str, Any], iterations: int | None = None) -> dict[str, Any]:
    n=iterations or design["analysis"]["power_iterations"]; rng=random.Random(design["randomization"]["power_grid_seed"]); rows=[]
    for rate,target in [(0.20,.8726),(.25,.8589),(.30,.8482),(.40,.8468),(.50,.8730),(.60,.9184),(.65,.9445)]:
        passed=0
        for _ in range(n):
            diffs=[sum(rng.random()<rate+.30 for _ in range(4))-sum(rng.random()<rate for _ in range(4)) for _task in range(16)]
            passed += sum(diffs)>=13 and _gate(diffs)
        value=passed/n; rows.append({"null_rate":rate,"helpful_rate":rate+.30,"power":value,"expected":target,"within_tolerance":abs(value-target)<=.005})
    return {"iterations":n,"seed":design["randomization"]["power_grid_seed"],"rows":rows,"passed":all(x["within_tolerance"] for x in rows)}


def post_calibration_power(counts: dict[str,int], selected: Sequence[str], design: dict[str,Any], iterations: int | None=None) -> dict[str,Any]:
    ordered=sorted(selected); rates=[Fraction(counts[t]+1,8) for t in ordered]
    value=simulate_power(rates, design["randomization"]["post_calibration_power_seed"], iterations or design["analysis"]["power_iterations"])
    return {"selected_ids":ordered,"rates":[fraction(x) for x in rates],"power":value,"passed":value>=.80}


def stratified_bootstrap(differences: dict[str,Fraction], iterations: int=100000, seed: int=20260812) -> dict[str,Any]:
    if any(sum(t.startswith(s+"-") for t in differences)!=4 for s in STRATA): raise ValueError("bootstrap requires four selected tasks per stratum")
    rng=random.Random(seed); groups=[[Fraction(differences[t]) for t in sorted(differences) if t.startswith(s+"-")] for s in STRATA]
    values=sorted(sum((g[rng.randrange(4)] for g in groups for _j in range(4)),Fraction())/16 for _ in range(iterations))
    lo,hi=math.floor(.025*(iterations-1)),math.ceil(.975*(iterations-1))
    return {"iterations":iterations,"seed":seed,"lower_index":lo,"upper_index":hi,"lower":fraction(values[lo]),"upper":fraction(values[hi])}


def compare(outcomes: dict[tuple[str,str],list[bool]], tasks: Sequence[str], arm_a: str, arm_b: str,
            strata: dict[str,str] | None=None, bootstrap_iterations: int=100000) -> dict[str,Any]:
    diffs={}
    for task in tasks:
        a,b=outcomes.get((task,arm_a)),outcomes.get((task,arm_b))
        if not a or not b or any(type(x) is not bool for x in a+b): raise ValueError("complete fresh outcomes required")
        diffs[task]=Fraction(sum(a),len(a))-Fraction(sum(b),len(b))
    effect=sum(diffs.values(),Fraction())/len(tasks); sign=exact_sign_test(list(diffs.values())); p=Fraction(sign["p_value"]["numerator"],sign["p_value"]["denominator"])
    result={"arm_a":arm_a,"arm_b":arm_b,"effect_a_minus_b":fraction(effect),"task_differences":{k:fraction(v) for k,v in sorted(diffs.items())},
            "exact_test":sign,"a_wins":effect>=Fraction(1,5) and p<=Fraction(1,20),"b_wins":effect<=-Fraction(1,5) and p<=Fraction(1,20)}
    if len(tasks)==16: result["bootstrap"]=stratified_bootstrap(diffs,bootstrap_iterations)
    return result


def create_once(path: Path, value: object) -> str:
    path.parent.mkdir(parents=True, exist_ok=True); data=canonical(value)
    with path.open("xb") as stream: stream.write(data)
    return hashlib.sha256(data).hexdigest()


def _json(path: Path) -> Any:
    if path.is_symlink() or not path.is_file(): raise RuntimeError(f"missing receipt: {path.name}")
    raw=path.read_bytes(); value=json.loads(raw)
    if raw != canonical(value): raise RuntimeError(f"noncanonical receipt: {path.name}")
    return value


def _same_receipt(path: Path, value: object) -> None:
    if path.exists():
        if path.is_symlink() or path.read_bytes()!=canonical(value): raise RuntimeError(f"create-once receipt drift: {path.name}")
    else: create_once(path,value)


def _receipt(live: Path, name: str, value: dict[str,Any], prerequisites: Sequence[str]=()) -> dict[str,Any]:
    manifest=live/"initial-manifest.json"; value={**value,"manifest_sha256":sha256_file(manifest),
        "prerequisite_sha256":{x:sha256_file(live/x) for x in prerequisites}}
    create_once(live/name,value); return value


def create_mapping(stage: str, opaque_ids: Sequence[str], path: Path, rng: random.Random | None=None) -> dict[str,Any]:
    values=list({"smoke":["N"],"calibration":["N"],"controls":["N1","N2","H"],"helpful":["N","P"]}[stage])
    (rng or random.SystemRandom()).shuffle(values)
    value={"schema":"mdseval.coder-beneficial-sensitivity-m2-sealed-mapping-v1","stage":stage,"mapping":dict(zip(opaque_ids,values))}
    create_once(path,value); return value


def _default_commit_probe(root: Path, commit: str, paths: Sequence[str]) -> dict[str,Any]:
    def git(*args: str) -> bytes:
        run=subprocess.run(["git","-C",str(root),*args],capture_output=True)
        if run.returncode: raise RuntimeError("clean verified commit required")
        return run.stdout
    if git("rev-parse","HEAD").decode().strip()!=commit or git("status","--porcelain","--untracked-files=no").strip():
        raise RuntimeError("dirty or drifted verified commit")
    frozen={}
    for path in paths:
        frozen[path]=hashlib.sha256(git("show",f"{commit}:{path}")).hexdigest()
    return {"head":commit,"clean":True,"frozen_hashes":frozen}


def initialize(*, design_path: Path | str, instance: str, verified_commit: str, freeze_authorization: Path,
               closure_record: Path, runs_root: Path | str=Path("runs"), checker: Any=_checker,
               process: Any=None) -> dict[str,Any]:
    """Create the clean-commit -> closure -> freeze -> alignment -> qualification -> manifest chain."""
    design_path=Path(design_path); design=load_design(design_path)
    if not SAFE_ID.fullmatch(instance) or not COMMIT.fullmatch(verified_commit): raise ValueError("unsafe instance or commit")
    closure_path=Path(closure_record); expected_closure=_root(design_path)/M2_4_2_CLOSURE
    if closure_path.is_symlink() or not closure_path.is_file() or closure_path.resolve()!=expected_closure.resolve() or sha256_file(closure_path)!=M2_4_2_CLOSURE_SHA256: raise RuntimeError("exact M2.4.2 closure PASS required")
    closure=_json(closure_path); authorization=_json(Path(freeze_authorization))
    if closure.get("schema")!="mdseval.coder-beneficial-sensitivity-m2-4-2-closure-v1" or closure.get("status")!="PASS" or closure.get("authoritative") is not False or closure.get("experiment")!=design["experiment"]: raise RuntimeError("exact M2.4.2 closure PASS required")
    if authorization != {"schema":"mdseval.coder-beneficial-sensitivity-m2-freeze-authorization-v1","experiment":design["experiment"],
                          "instance":instance,"verified_commit":verified_commit,"authorized":True}:
        raise RuntimeError("freeze authorization invalid")
    runs=Path(runs_root); instance_root=runs/instance; live,replay_root=instance_root/"live",instance_root/"replay"
    if live.exists() or replay_root.exists(): raise RuntimeError("live and replay roots must not preexist")
    root=_root(design_path); governed=[v["path"] for v in design["artifacts"].values() if "sha256" in v]+[design["artifacts"]["evaluator"]["path"],design_path.relative_to(root).as_posix()]
    probe=(process or _default_commit_probe)(root,verified_commit,governed)
    current={p:sha256_file(root/p) for p in governed}
    if probe!={"head":verified_commit,"clean":True,"frozen_hashes":current}: raise RuntimeError("dirty, drifted, or incomplete commit probe")
    live.mkdir(parents=True,exist_ok=False)
    freeze={"schema":"mdseval.coder-beneficial-sensitivity-m2-final-freeze-v1","status":"PASS","verified_commit":verified_commit,
        "authorization_sha256":sha256_file(Path(freeze_authorization)),"closure_sha256":sha256_file(closure_path),
        "config_sha256":sha256_file(design_path),"evaluator_sha256":current[design["artifacts"]["evaluator"]["path"]],"governed_hashes":current}
    create_once(live/"final-freeze-receipt.json",freeze)
    alignment={"schema":"mdseval.coder-beneficial-sensitivity-m2-post-freeze-alignment-v1","status":"PASS","verified_commit":verified_commit,
        "final_freeze_receipt_sha256":sha256_file(live/"final-freeze-receipt.json"),"aligned_hashes":current}
    create_once(live/"post-freeze-alignment-receipt.json",alignment)
    qdir=live/"qualification"
    result=qualify(design_path,qdir,authoritative=True,final_freeze_receipt=live/"final-freeze-receipt.json",verified_commit=verified_commit,checker=checker)
    if result["status"]!="PASS": raise RuntimeError("authoritative qualification failed")
    shutil.copyfile(qdir/"qualification-receipt.json",live/"qualification-receipt.json")
    schedules=build_master_schedules(design); sealed={}
    for index,stage in enumerate(STAGES):
        mapping=create_mapping(stage,design["randomization"]["opaque_ids"][stage],live/"sealed-mappings"/f"{stage}.json",random.Random(design["randomization"]["schedule_seed"]+str(index)))
        sealed[stage]=sha256_file(live/"sealed-mappings"/f"{stage}.json")
    manifest={"schema":"mdseval.coder-beneficial-sensitivity-m2-initial-manifest-v1","experiment":design["experiment"],"instance":instance,
        "verified_commit":verified_commit,"config_sha256":sha256_file(design_path),"evaluator_sha256":sha256_file(Path(__file__)),
        "prerequisite_sha256":{x:sha256_file(live/x) for x in ("final-freeze-receipt.json","post-freeze-alignment-receipt.json","qualification-receipt.json")},
        "qualification_results_sha256":sha256_file(qdir/"qualification-results.json"),"python":{"executable":str(Path(sys.executable).resolve()),"version":sys.version},
        "runtime":design["runtime"],"governed_hashes":current,"treatment_hashes":sorted(design["artifacts"][x]["sha256"] for x in ("null","harmful","helpful")),
        "mapping_hashes":sealed,"schedules":schedules,"schedule_sha256":digest(schedules),"randomization":design["randomization"],
        "invalidity_table":design["evidence"]["invalidity_table"],"wrapper_sha256":design["artifacts"]["wrapper"]["sha256"],
        "roots":{"live":str(live),"replay":str(replay_root)},"caps":{"base":297,"absolute":314}}
    create_once(live/"initial-manifest.json",manifest); return manifest


def classify_attempt(result: Any, events: Any, error: str | None, invalidity_table: Sequence[str]) -> str:
    if error in invalidity_table and not getattr(events,"events",()): return "INFRASTRUCTURE_INVALID"
    return "Y0" if error or getattr(result,"timed_out",False) or getattr(result,"interrupted",False) or getattr(result,"exit_code",1)!=0 else "CHECK"


def validate_resume(stage: str, slots: Sequence[dict[str,Any]], completed: int) -> bool:
    if not 0<=completed<=len(slots): return False
    if stage=="calibration" or completed in {0,len(slots)}: return True
    if stage=="controls": return slots[completed-1]["task_id"]!=slots[completed]["task_id"]
    if stage=="helpful": return completed%2==0
    return False


def _event_value(events: Sequence[dict[str,Any]], names: set[str]) -> Any:
    def visit(value: Any) -> Any:
        if isinstance(value,dict):
            for key,item in value.items():
                if key in names and isinstance(item,str): return item
                found=visit(item)
                if found is not None: return found
        if isinstance(value,list):
            for item in value:
                found=visit(item)
                if found is not None: return found
        return None
    return visit(list(events))


def _task_case(root: Path, record: dict[str,Any], task: dict[str,Any]) -> Any:
    from .config import CaseConfig, VerificationEvidence
    directory=root/record["path"]
    return CaseConfig(1,task["id"],"m2","IMPLEMENTED",tuple(task["protected_inputs"]),(),
        ((str(Path(sys.executable).resolve()),str(directory/"check.py"),"{repo}"),),VerificationEvidence(True,True,()),(),(),300,directory,
        record["task_json_sha256"],record["fixture_sha256"])


def _live_attempt(design: dict[str,Any], design_path: Path, live: Path, slot: dict[str,Any], semantic: str,
                  runner: Any, launch_index: int) -> dict[str,Any]:
    from .capture import Redactor, capture_git, parse_event_stream
    from .fixtures import audit_final_subject_tree, prepare_fixture
    root=_root(design_path); master=json.loads((root/design["artifacts"]["master"]["path"]).read_text()); record=next((x for x in master["tasks"] if x["id"]==slot["task_id"]),None)
    attempt=live/"attempts"/slot["stage"]/slot["slot_id"].replace(":","_"); attempt.mkdir(parents=True,exist_ok=False)
    redactor=Redactor(); prepared=run=None
    try:
        if slot["stage"]=="smoke":
            temporary=Path(tempfile.mkdtemp(prefix="mdseval-m2-smoke-source-")); fixture=temporary/"fixture"; fixture.mkdir()
            (temporary/"contract.md").write_text("Make no file changes. Reply with exactly two lines: IMPLEMENTED then SMOKE_READY.\n")
            from .config import CaseConfig, VerificationEvidence
            case=CaseConfig(1,"smoke","m2","IMPLEMENTED",(),(),(),VerificationEvidence(False,False,()),(),(),300,temporary,digest("smoke"),tree_sha256(fixture))
        else:
            task=json.loads((root/record["path"]/"task.json").read_text()); case=_task_case(root,record,task)
        treatment=root/design["artifacts"][{"N":"null","N1":"null","N2":"null","H":"harmful","P":"helpful"}[semantic]]["path"]
        prepared=prepare_fixture(case,treatment,sha256_file(treatment)); before=tree_sha256(prepared.repo)
        run=runner.run(prepared,attempt/"runner",300,redactor); audit_final_subject_tree(prepared.repo)
        events=parse_event_stream(attempt/"runner"/"events.jsonl"); final=(attempt/"runner"/"final.txt").read_bytes()
        capture=capture_git(prepared.repo,prepared.baseline_commit,redactor); checked=({"valid":True,"mechanical":True,
            "resolved":final==EXPECTED_FINAL and not capture.status and not capture.diff and not capture.untracked,
            "payload":{"requirements":{},"regressions":{},"integrity":{"passed":True}}} if slot["stage"]=="smoke" else _checker(root/record["path"]/"check.py",slot["task_id"],prepared.repo))
        model=_event_value(events.events,{"model","model_name"}); effort=_event_value(events.events,{"reasoning_effort","model_reasoning_effort"})
        complete=not any(x.get("truncated") for x in capture.untracked); valid=events.valid and complete and model=="gpt-5.6-sol" and effort=="high"
        req=checked.get("payload",{}).get("requirements",{})
        row={**slot,"launch_index":launch_index,"requested_model":"gpt-5.6-sol","observed_model":model,"requested_reasoning_effort":"high",
            "observed_reasoning_effort":effort,"judge_calls":0,"objective_resolved":bool(valid and checked.get("valid") and checked.get("mechanical") and checked.get("resolved") and not checked.get("infrastructure_invalid") and not run.timed_out and not run.interrupted and run.exit_code==0),
            "checker_valid":checked.get("valid") is True,"mechanical_integrity":valid and checked.get("mechanical") is True and not checked.get("infrastructure_invalid"),
            "requirements_passed":sum(x.get("passed") is True for x in req.values()),"requirements_total":len(req),"runner":asdict(run),
            "events":asdict(events),"capture":asdict(capture),"final_message_hex":final.hex(),"final_bytes_sha256":hashlib.sha256(final).hexdigest(),
            "tree_unchanged":not capture.status and not capture.diff and not capture.untracked,"capture_complete":complete,"baseline_tree_sha256":before,
            "final_tree_sha256":tree_sha256(prepared.repo),"status":"ACTIVE","infrastructure_invalid":checked.get("infrastructure_invalid") is True}
    except Exception as exc:
        error=str(exc); invalid=run is None and error in set(design["evidence"]["invalidity_table"])
        row={**slot,"launch_index":launch_index,"requested_model":"gpt-5.6-sol","observed_model":None,"requested_reasoning_effort":"high",
            "observed_reasoning_effort":None,"judge_calls":0,"objective_resolved":False,"checker_valid":False,"mechanical_integrity":False,
            "requirements_passed":0,"requirements_total":0,"status":"ACTIVE","infrastructure_invalid":invalid,"error":error}
    finally:
        if prepared is not None: prepared.cleanup()
        if slot["stage"]=="smoke" and "temporary" in locals(): shutil.rmtree(temporary,ignore_errors=True)
    create_once(attempt/"attempt.json",row); return row


def _attempt_path(live: Path, slot: dict[str,Any]) -> Path:
    return live/"attempts"/slot["stage"]/slot["slot_id"].replace(":","_")/"attempt.json"


def _validate_row(row: Any, slot: dict[str,Any], index: int) -> dict[str,Any]:
    if not isinstance(row,dict) or any(row.get(k)!=v for k,v in slot.items()) or row.get("launch_index")!=index:
        raise RuntimeError("attempt row does not bind scheduled slot")
    required={"requested_model":"gpt-5.6-sol","requested_reasoning_effort":"high","judge_calls":0,"status":"ACTIVE"}
    if any(row.get(k)!=v for k,v in required.items()) or type(row.get("objective_resolved")) is not bool or type(row.get("infrastructure_invalid")) is not bool:
        raise RuntimeError("attempt evidence incomplete")
    if not row["infrastructure_invalid"] and (row.get("observed_model")!="gpt-5.6-sol" or row.get("observed_reasoning_effort")!="high"):
        raise RuntimeError("requested/observed identity mismatch")
    if slot["stage"]=="smoke" and not row["infrastructure_invalid"] and (row.get("final_message_hex")!=EXPECTED_FINAL.hex()
            or row.get("tree_unchanged") is not True or row.get("capture_complete") is not True):
        raise RuntimeError("smoke raw bytes, tree, or capture invalid")
    return row


def _unblind(live: Path, stage: str, locked_name: str) -> dict[str,Any]:
    mapping=_json(live/"sealed-mappings"/f"{stage}.json")
    return _receipt(live,f"{stage}-unblinding-receipt.json",{"schema":"mdseval.coder-beneficial-sensitivity-m2-stage-unblinding-v1",
        "stage":stage,"mapping_sha256":sha256_file(live/"sealed-mappings"/f"{stage}.json"),"mapping":mapping["mapping"],
        "outcomes_locked_before_unblinding":True},[locked_name])


def _rows(live: Path) -> list[dict[str,Any]]:
    rows=[]
    for stage in STAGES:
        path=live/f"{stage}-attempts.json"
        if path.is_file(): rows.extend(_json(path))
    return sorted(rows,key=lambda x:x["launch_index"])


def _derive_report(design: dict[str,Any], live: Path, verdict: str, reason: str, bootstrap_iterations: int) -> tuple[dict[str,Any],dict[str,Any]]:
    rows=_rows(live); evidence={"schema":"mdseval.coder-beneficial-sensitivity-m2-evidence-v1","attempts":rows,
        "locked":True,"manifest_sha256":sha256_file(live/"initial-manifest.json"),"bound_manifest_sha256":sha256_file(live/"initial-manifest.json"),
        "terminal_reason":reason,"verdict":verdict}
    for name,key in (("selection-receipt.json","selection"),("power-receipt.json","post_calibration_power")):
        if (live/name).is_file(): evidence[key]=_json(live/name)
    mappings={}
    for stage in STAGES:
        path=live/f"{stage}-unblinding-receipt.json"
        if path.is_file(): mappings[stage]=_json(path)["mapping"]
    evidence["unblinded_mapping"]=mappings
    report={"schema":"mdseval.coder-beneficial-sensitivity-m2-report-v1","experiment":design["experiment"],"verdict":verdict,
            "terminal_reason":reason,"claim_boundary":CLAIM,"calls":{"launched":len(rows),"superseded":sum(x["status"]=="SUPERSEDED" for x in rows),"judge":0},
            "deviations":[],"secondary":{"requirements_passed":sum(x.get("requirements_passed",0) for x in rows if x["status"]=="ACTIVE"),
            "requirements_total":sum(x.get("requirements_total",0) for x in rows if x["status"]=="ACTIVE")}}
    if "selection" in evidence: report["selection"]=evidence["selection"]
    if "post_calibration_power" in evidence: report["post_calibration_power"]=evidence["post_calibration_power"]
    if (live/"controls-gates-receipt.json").is_file(): report["controls"]=_json(live/"controls-gates-receipt.json")["comparisons"]
    if (live/"helpful-gate-receipt.json").is_file(): report["helpful"]=_json(live/"helpful-gate-receipt.json")["comparison"]
    return evidence,report


def render_markdown(report: dict[str,Any]) -> str:
    return ("# CODER beneficial-sensitivity Milestone 2\n\n"+f"Verdict: **{report['verdict']}**\n\n"+f"Terminal reason: {report['terminal_reason']}\n\n"
            "## Claim boundary\n\n"+report["claim_boundary"]+"\n\nNon-significance in A/A is not equivalence. This diagnostic does not establish candidate superiority or general utility.\n")


def _walk_files(root: Path) -> list[Path]:
    result=[]
    for path in sorted(root.rglob("*"),key=lambda p:p.relative_to(root).as_posix().encode()):
        if path.is_symlink(): raise ValueError("evidence symlink")
        if path.is_file(): result.append(path)
        elif not path.is_dir(): raise ValueError("unsupported evidence entry")
    return result


def governed_inventory(root: Path, exclude: Iterable[str]=()) -> list[dict[str,Any]]:
    omitted=set(exclude)
    return [{"path":p.relative_to(root).as_posix(),"size":p.stat().st_size,"sha256":sha256_file(p)} for p in _walk_files(root) if p.relative_to(root).as_posix() not in omitted]


def _terminalize(design: dict[str,Any], live: Path, verdict: str, reason: str, bootstrap_iterations: int=100000) -> dict[str,Any]:
    if (live/"locked-evidence-manifest.json").exists(): return _json(live/"reports"/"report.json")
    evidence,report=_derive_report(design,live,verdict,reason,bootstrap_iterations)
    create_once(live/"raw-evidence.json",evidence); (live/"reports").mkdir()
    create_once(live/"reports"/"report.json",report); (live/"reports"/"report.md").write_text(render_markdown(report),encoding="utf-8")
    inventory=governed_inventory(live,{"locked-evidence-manifest.json"})
    create_once(live/"locked-evidence-manifest.json",{"schema":"mdseval.coder-beneficial-sensitivity-m2-locked-evidence-v1",
        "manifest_sha256":sha256_file(live/"initial-manifest.json"),"files":inventory,"files_sha256":digest(inventory),"verdict":verdict})
    return report


def _outcomes(rows: Sequence[dict[str,Any]], mapping: dict[str,str]) -> dict[tuple[str,str],list[bool]]:
    result={}
    for row in rows:
        if row["status"]=="ACTIVE": result.setdefault((row["task_id"],mapping[row["opaque_arm_id"]]),[]).append(row["objective_resolved"])
    return result


def run_stage(*, design_path: Path | str, instance: str, stage: str, authorization_receipt: Path,
              runs_root: Path | str=Path("runs"), runner_factory: Any=None, attempt_executor: Any=None,
              power_iterations: int | None=None, bootstrap_iterations: int=100000) -> dict[str,Any]:
    """Execute one authorized stage and all of its required post-stage transitions."""
    design_path=Path(design_path); design=load_design(design_path)
    if stage not in STAGES or not SAFE_ID.fullmatch(instance): raise ValueError("invalid stage or instance")
    live=Path(runs_root)/instance/"live"
    if not live.is_dir() or (Path(runs_root)/instance/"replay").exists() or (live/"locked-evidence-manifest.json").exists():
        raise RuntimeError("active initialized live root required")
    manifest=_json(live/"initial-manifest.json"); _validate_initial_bindings(live,manifest); auth=_json(Path(authorization_receipt)); manifest_hash=sha256_file(live/"initial-manifest.json")
    if auth!={"schema":"mdseval.coder-beneficial-sensitivity-m2-stage-authorization-v1","experiment":design["experiment"],"instance":instance,
              "stage":stage,"authorized":True,"manifest_sha256":manifest_hash}: raise RuntimeError("stage-specific authorization invalid")
    prereq={"smoke":["qualification-receipt.json"],"calibration":["smoke-receipt.json"],
            "controls":["selection-receipt.json","power-receipt.json","controls-filtered-schedule-receipt.json"],
            "helpful":["controls-gates-receipt.json","helpful-filtered-schedule-receipt.json"]}[stage]
    if any(not (live/x).is_file() for x in prereq) or any((live/f"{s}-receipt.json").exists() for s in STAGES[STAGES.index(stage)+1:]):
        raise RuntimeError("stage prerequisites or order invalid")
    _same_receipt(live/f"{stage}-authorization.json",auth)
    mapping_path=live/"sealed-mappings"/f"{stage}.json"
    if sha256_file(mapping_path)!=manifest["mapping_hashes"][stage]: raise RuntimeError("mapping hash drift")
    mapping=_json(mapping_path)["mapping"]; schedules=manifest["schedules"]
    if digest(schedules)!=manifest["schedule_sha256"] or schedules!=build_master_schedules(design): raise RuntimeError("schedule sentinel drift")
    if stage=="smoke": slots=[{"slot_id":"smoke:base","stage":"smoke","round":0,"task_id":"smoke","opaque_arm_id":"S0","fallback":False}]
    elif stage=="calibration": slots=schedules[stage]["base"]
    else: slots=_json(live/f"{stage}-filtered-schedule-receipt.json")["slots"]
    if len(slots)!={"smoke":1,"calibration":120,"controls":48,"helpful":128}[stage]: raise RuntimeError("base call count drift")
    runner=None
    if attempt_executor is None:
        if runner_factory is None:
            from .runner.codex_cli import CodexCLI
            runner_factory=CodexCLI
        runner=runner_factory(runner_config(design))
    existing=[]
    for slot in slots:
        path=_attempt_path(live,slot)
        if path.exists(): existing.append(_validate_row(_json(path),slot,len(_rows(live))+len(existing)+1))
        else: break
    if any(_attempt_path(live,x).exists() for x in slots[len(existing)+1:]) or not validate_resume(stage,slots,len(existing)):
        raise RuntimeError("missing, reordered, or invalid resume boundary")
    prior=len(_rows(live)); rows=list(existing)
    for slot in slots[len(rows):]:
        index=prior+len(rows)+1
        row=(attempt_executor(design,slot,mapping[slot["opaque_arm_id"]],index) if attempt_executor else _live_attempt(design,design_path,live,slot,mapping[slot["opaque_arm_id"]],runner,index))
        row=_validate_row(row,slot,index)
        if attempt_executor: create_once(_attempt_path(live,slot),row)
        rows.append(row)
    invalid={r["task_id"] for r in rows if r["infrastructure_invalid"]}; status="PASS"
    if stage=="smoke" and invalid or len(invalid)>1: status="INVALID"
    elif invalid:
        task=next(iter(invalid))
        for row in rows:
            if row["task_id"]==task: row["status"]="SUPERSEDED"
        create_once(live/f"{stage}-supersession.json",{"stage":stage,"task_id":task,"slot_ids":[r["slot_id"] for r in rows if r["task_id"]==task]})
        fallback=schedules[stage]["fallback_by_task"][task]; fallback_rows=[]
        for slot in fallback:
            index=prior+len(rows)+len(fallback_rows)+1
            row=(attempt_executor(design,slot,mapping[slot["opaque_arm_id"]],index) if attempt_executor else _live_attempt(design,design_path,live,slot,mapping[slot["opaque_arm_id"]],runner,index))
            row=_validate_row(row,slot,index)
            if attempt_executor: create_once(_attempt_path(live,slot),row)
            fallback_rows.append(row)
        rows.extend(fallback_rows)
        if any(r["infrastructure_invalid"] for r in fallback_rows): status="INVALID"
    total=prior+len(rows)
    if total>314 or (stage=="helpful" and total>297+17): status="INVALID"
    if any(not r.get("mechanical_integrity") and not r["infrastructure_invalid"] for r in rows): status="INVALID"
    if stage=="smoke" and (len(rows)!=1 or not rows[0]["objective_resolved"]): status="INVALID"
    create_once(live/f"{stage}-attempts.json",rows)
    lock=_receipt(live,f"{stage}-outcome-lock.json",{"schema":"mdseval.coder-beneficial-sensitivity-m2-outcome-lock-v1","stage":stage,
        "status":status,"attempts_sha256":sha256_file(live/f"{stage}-attempts.json"),"schedule_sha256":digest(slots),"launched_calls":len(rows)},prereq)
    unblind=_unblind(live,stage,f"{stage}-outcome-lock.json")
    stage_receipt=_receipt(live,f"{stage}-receipt.json",{"schema":"mdseval.coder-beneficial-sensitivity-m2-stage-result-v1","stage":stage,"status":status,
        "base_calls":len(slots),"launched_calls":len(rows),"fallback_cap":design["calls"]["fallback_by_stage"][stage],
        "schedule_sha256":digest(slots),"outcome_lock_sha256":sha256_file(live/f"{stage}-outcome-lock.json"),
        "unblinding_sha256":sha256_file(live/f"{stage}-unblinding-receipt.json")},[f"{stage}-outcome-lock.json",f"{stage}-unblinding-receipt.json"])
    if status=="INVALID": return _terminalize(design,live,"INVALID",f"{stage} integrity failure",bootstrap_iterations)
    active=[r for r in rows if r["status"]=="ACTIVE"]
    if stage=="calibration":
        counts={t:sum(r["objective_resolved"] for r in active if r["task_id"]==t) for t in TASKS}
        if any(sum(r["task_id"]==t for r in active)!=6 for t in TASKS): return _terminalize(design,live,"INVALID","calibration block count",bootstrap_iterations)
        selection=select_tasks(counts); selection.update({"schema":"mdseval.coder-beneficial-sensitivity-m2-selection-v1","calibration_counts":counts})
        _receipt(live,"selection-receipt.json",selection,["calibration-outcome-lock.json","calibration-unblinding-receipt.json"])
        if selection["status"]!="PASS": return _terminalize(design,live,"SENSITIVITY_NOT_DEMONSTRATED","selection",bootstrap_iterations)
        power=post_calibration_power(counts,selection["selected_ids"],design,power_iterations); power["schema"]="mdseval.coder-beneficial-sensitivity-m2-power-v1"
        _receipt(live,"power-receipt.json",power,["selection-receipt.json"])
        for next_stage in ("controls","helpful"):
            filtered=filter_schedule(schedules,selection["selected_ids"],next_stage); filtered["schema"]="mdseval.coder-beneficial-sensitivity-m2-filtered-schedule-v1"
            _receipt(live,f"{next_stage}-filtered-schedule-receipt.json",filtered,["selection-receipt.json","power-receipt.json"])
        if not power["passed"]: return _terminalize(design,live,"SENSITIVITY_NOT_DEMONSTRATED","power",bootstrap_iterations)
    elif stage=="controls":
        selected=_json(live/"selection-receipt.json")["selected_ids"]; outcomes=_outcomes(active,unblind["mapping"])
        aa=compare(outcomes,selected,"N1","N2",bootstrap_iterations=bootstrap_iterations); harmful=compare(outcomes,selected,"N1","H",bootstrap_iterations=bootstrap_iterations)
        passed=not aa["a_wins"] and not aa["b_wins"] and harmful["a_wins"]
        _receipt(live,"controls-gates-receipt.json",{"schema":"mdseval.coder-beneficial-sensitivity-m2-controls-gates-v1","status":"PASS" if passed else "FAIL",
            "comparisons":{"aa":aa,"harmful":harmful},"aa_gate":"NO_FALSE_WINNER" if not aa["a_wins"] and not aa["b_wins"] else "FALSE_WINNER",
            "harmful_gate":harmful["a_wins"]},["controls-outcome-lock.json","controls-unblinding-receipt.json"])
        if not passed: return _terminalize(design,live,"SENSITIVITY_NOT_DEMONSTRATED","controls",bootstrap_iterations)
    elif stage=="helpful":
        selected=_json(live/"selection-receipt.json")["selected_ids"]; comparison=compare(_outcomes(active,unblind["mapping"]),selected,"P","N",bootstrap_iterations=bootstrap_iterations)
        _receipt(live,"helpful-gate-receipt.json",{"schema":"mdseval.coder-beneficial-sensitivity-m2-helpful-gate-v1","status":"PASS" if comparison["a_wins"] else "FAIL",
            "comparison":comparison},["helpful-outcome-lock.json","helpful-unblinding-receipt.json","controls-gates-receipt.json"])
        return _terminalize(design,live,"SENSITIVITY_DEMONSTRATED" if comparison["a_wins"] else "SENSITIVITY_NOT_DEMONSTRATED","helpful",bootstrap_iterations)
    return stage_receipt

def _validate_initial_bindings(live: Path, manifest: Any) -> None:
    expected={"final-freeze-receipt.json","post-freeze-alignment-receipt.json","qualification-receipt.json"}; bindings=manifest.get("prerequisite_sha256") if isinstance(manifest,dict) else None
    if not isinstance(manifest,dict) or not isinstance(bindings,dict) or set(bindings)!=expected: raise ValueError("initial evidence binding drift")
    if any(not isinstance(wanted,str) or not SHA256.fullmatch(wanted) or path.is_symlink() or not path.is_file() or sha256_file(path)!=wanted for name,wanted in {**bindings,"qualification/qualification-results.json":manifest.get("qualification_results_sha256")}.items() for path in (live/name,)): raise ValueError("initial evidence binding drift")
def _validate_dag(live: Path, manifest_hash: str) -> None:
    manifest=_json(live/"initial-manifest.json"); _validate_initial_bindings(live,manifest)
    if manifest["schedule_sha256"]!=digest(manifest["schedules"]): raise ValueError("schedule drift")
    for path in _walk_files(live):
        if path.name.endswith(("receipt.json","outcome-lock.json")) and path.name not in {"final-freeze-receipt.json","qualification-receipt.json"}:
            value=_json(path)
            if "manifest_sha256" in value and value["manifest_sha256"]!=manifest_hash: raise ValueError("receipt manifest DAG drift")
            for name,wanted in value.get("prerequisite_sha256",{}).items():
                if not (target:=live/name).is_file() or sha256_file(target)!=wanted: raise ValueError("receipt prerequisite DAG drift")
    rows=_rows(live); launches=[x["launch_index"] for x in rows]
    if launches!=list(range(1,len(rows)+1)) or len(rows)>314: raise ValueError("attempt order or cap drift")

def replay(design_path: Path | str, instance: str, *, runs_root: Path | str=Path("runs"), bootstrap_iterations: int=100000) -> dict[str,Any]:
    design=load_design(design_path)
    if not SAFE_ID.fullmatch(instance): raise ValueError("unsafe instance ID")
    live,target=Path(runs_root)/instance/"live",Path(runs_root)/instance/"replay"
    if not live.is_dir() or target.exists(): raise ValueError("exclusive live/replay roots violated")
    locked=_json(live/"locked-evidence-manifest.json"); actual=governed_inventory(live,{"locked-evidence-manifest.json"})
    if locked.get("files")!=actual or locked.get("files_sha256")!=digest(actual): raise ValueError("governed evidence missing, added, changed, or reordered")
    manifest_hash=sha256_file(live/"initial-manifest.json"); _validate_dag(live,manifest_hash)
    raw=_json(live/"raw-evidence.json"); report=_json(live/"reports"/"report.json")
    derived_evidence,derived_report=_derive_report(design,live,report["verdict"],report["terminal_reason"],bootstrap_iterations)
    if canonical(raw)!=canonical(derived_evidence) or canonical(report)!=canonical(derived_report): raise ValueError("reports are not raw-evidence-derived")
    target.mkdir(parents=True,exist_ok=False); (target/"report.json").write_bytes(canonical(derived_report)); (target/"report.md").write_text(render_markdown(derived_report),encoding="utf-8")
    if (target/"report.json").read_bytes()!=(live/"reports"/"report.json").read_bytes() or (target/"report.md").read_bytes()!=(live/"reports"/"report.md").read_bytes():
        raise ValueError("replay report is not byte-identical")
    return derived_report


def analyze(design: dict[str,Any], evidence: Any, *, bootstrap_iterations: int=100000) -> dict[str,Any]:
    """Compatibility helper: reject supplied summaries and analyze only a complete locked envelope."""
    base={"schema":"mdseval.coder-beneficial-sensitivity-m2-report-v1","experiment":design["experiment"],"claim_boundary":CLAIM}
    try:
        if not isinstance(evidence,dict) or evidence.get("schema")!="mdseval.coder-beneficial-sensitivity-m2-evidence-v1" or evidence.get("locked") is not True:
            raise ValueError("evidence envelope invalid")
        rows=evidence.get("attempts")
        if not isinstance(rows,list) or not rows or [x.get("launch_index") for x in rows]!=list(range(1,len(rows)+1)) or len(rows)>314:
            raise ValueError("attempt evidence reordered, empty, or over cap")
        if evidence.get("manifest_sha256")!=evidence.get("bound_manifest_sha256"): raise ValueError("manifest lock mismatch")
        return {**base,"verdict":evidence.get("verdict","INVALID"),"terminal_reason":evidence.get("terminal_reason","compatibility")}
    except (KeyError,TypeError,ValueError) as exc:
        return {**base,"verdict":"INVALID","reasons":[str(exc)]}


def simulate(design: dict[str,Any], output: Path) -> dict[str,Any]:
    output.mkdir(parents=True,exist_ok=False); selected=[t for s in STRATA for t in [x for x in TASKS if x.startswith(s+"-")][:4]]; outcomes={}
    for task in selected:
        outcomes[task,"N1"]=[True]; outcomes[task,"N2"]=[True]; outcomes[task,"H"]=[False]; outcomes[task,"N"]=[False]*4; outcomes[task,"P"]=[True]*4
    result={"selection":select_tasks({t:3 for t in TASKS}),"aa":compare(outcomes,selected,"N1","N2",bootstrap_iterations=1000),
        "harmful":compare(outcomes,selected,"N1","H",bootstrap_iterations=1000),"helpful":compare(outcomes,selected,"P","N",bootstrap_iterations=1000),
        "schedules":build_master_schedules(design)}
    (output/"simulation.json").write_bytes(canonical(result)); return result


def main(argv: Sequence[str] | None=None) -> int:
    parser=argparse.ArgumentParser(); sub=parser.add_subparsers(dest="command",required=True)
    for name in ("validate","qualify","verify-power","simulate","initialize","run-stage","replay"):
        p=sub.add_parser(name); p.add_argument("--experiment",type=Path,required=True)
        if name in {"qualify","simulate"}: p.add_argument("--output",type=Path,required=True)
        if name in {"initialize","run-stage","replay"}: p.add_argument("--instance",required=True)
        if name=="initialize":
            p.add_argument("--verified-commit",required=True); p.add_argument("--freeze-authorization",type=Path,required=True); p.add_argument("--closure-record",type=Path,required=True)
        if name=="run-stage":
            p.add_argument("--stage",choices=STAGES,required=True); p.add_argument("--authorization-receipt",type=Path,required=True)
    args=parser.parse_args(argv)
    try:
        design=load_design(args.experiment)
        if args.command=="validate": print("VALID"); return 0
        if args.command=="qualify": result=qualify(args.experiment,args.output); print(result["status"]); return result["status"]!="PASS"
        if args.command=="verify-power": result=verify_power(design); print(json.dumps(result,sort_keys=True)); return not result["passed"]
        if args.command=="simulate": simulate(design,args.output); print("SIMULATED"); return 0
        if args.command=="initialize": initialize(design_path=args.experiment,instance=args.instance,verified_commit=args.verified_commit,
            freeze_authorization=args.freeze_authorization,closure_record=args.closure_record); print("INITIALIZED"); return 0
        if args.command=="run-stage": run_stage(design_path=args.experiment,instance=args.instance,stage=args.stage,authorization_receipt=args.authorization_receipt); print("STAGE_COMPLETE"); return 0
        report=replay(args.experiment,args.instance); print(report["verdict"]); return report["verdict"]=="INVALID"
    except (OSError,ValueError,RuntimeError,json.JSONDecodeError) as exc: parser.error(str(exc))
    return 2


if __name__=="__main__": raise SystemExit(main())
