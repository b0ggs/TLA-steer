#!/usr/bin/env python3
"""Queue, run, and verify development attempts for task-layout-v2 tasks."""
from __future__ import annotations
import argparse, json, os, shutil, sys, tempfile, time
from dataclasses import asdict; from pathlib import Path; from typing import Any, Callable
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0, str(ROOT))
from mdseval.capture import Redactor, capture_git, redact_event_stream  # noqa: E402
from mdseval.config import RunnerConfig; from mdseval.fixtures import audit_final_subject_tree  # noqa: E402
from mdseval.gitutils import init_repository, run_git; from mdseval.hashing import sha256_file, tree_sha256  # noqa: E402
from mdseval.processutils import ProcessOutcome, run_process_group  # noqa: E402
from mdseval.runner.codex_cli import build_codex_command, isolated_environment  # noqa: E402
from mdseval.scout import classify_infrastructure_failure; from mdseval.wrapper import WRAPPER_PROMPT  # noqa: E402
from tooling import taskcheck  # noqa: E402
RUNNER = RunnerConfig("codex-cli", "gpt-5.6-sol", "high", "workspace-write", "never", False, True, False, 300, 1)
class BatchError(RuntimeError): pass
def _bytes(value: Any) -> bytes: return (taskcheck.canonical(value) + "\n").encode()
def _write_once(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    try: stream = path.open("xb")
    except FileExistsError as exc: raise BatchError(f"exclusive-create collision: {path}") from exc
    try:
        with stream: stream.write(data)
    except BaseException:
        path.unlink(missing_ok=True); raise
def _json(path: Path, *, canonical: bool = True) -> dict[str, Any]:
    if path.is_symlink() or not path.is_file(): raise BatchError(f"missing or unsafe JSON: {path}")
    raw = path.read_bytes()
    try: value = json.loads(raw)
    except json.JSONDecodeError as exc: raise BatchError(f"malformed JSON: {path}") from exc
    if not isinstance(value, dict) or (canonical and raw != _bytes(value)): raise BatchError(f"noncanonical JSON object: {path}")
    return value
def _relative(path: Path) -> str:
    try: return path.resolve().relative_to(ROOT).as_posix()
    except ValueError as exc: raise BatchError(f"path is outside repository: {path}") from exc
def _resolve(relative: str) -> Path:
    path = (ROOT / relative).resolve()
    if _relative(path) != relative: raise BatchError(f"unsafe repository-relative path: {relative}")
    return path
def _sha(value: Any) -> bool: return isinstance(value, str) and len(value) == 64 and all(c in "0123456789abcdef" for c in value)
def _ledger(batch: Path, *, required: bool = False) -> dict[str, str]:
    rows = taskcheck._read_chain(batch / "evidence-ledger.jsonl", "evidence ledger", required=required); anchored = {}; keys = {"attempt", "manifest_sha256", "prev_sha256"}
    for number, row in enumerate(rows, 1):
        attempt = row.get("attempt"); parts = attempt.split("/") if isinstance(attempt, str) else []
        valid_path = len(parts) == 3 and all(taskcheck.TASK_ID.fullmatch(part) for part in parts[:2]) and parts[2].startswith("attempt-") and parts[2][8:].isdigit()
        if set(row) != keys or not valid_path or not _sha(row.get("manifest_sha256")) or attempt in anchored: raise BatchError(f"invalid evidence ledger schema at line {number}")
        anchored[attempt] = row["manifest_sha256"]
    return anchored
def queue_request(batch_id: str, tasks: list[Path], arm_name: str, arm_file: Path,
                  runs_root: Path = ROOT / "runs" / "dev-v2") -> Path:
    if not taskcheck.TASK_ID.fullmatch(batch_id) or not taskcheck.TASK_ID.fullmatch(arm_name) or not tasks: raise BatchError("batch id, arm name, or task list is invalid")
    arm_file = arm_file.resolve()
    if arm_file.is_symlink() or not arm_file.is_file(): raise BatchError("arm file must be a regular non-symlink")
    if not _relative(arm_file).startswith("controls/"): raise BatchError("arm file must live under controls/")
    if arm_name in {"n", "null"} and arm_file.stat().st_size: raise BatchError("null arm file must be zero bytes")
    rows = []
    for task in tasks:
        result = taskcheck.verify(task)
        rows.append({"task_id": task.name, "task_dir": _relative(task), "manifest_sha256": result["manifest_sha256"]})
    if len({row["task_id"] for row in rows}) != len(rows): raise BatchError("task ids must be unique")
    request = {"batch_id": batch_id, "tasks": rows, "arm": {"name": arm_name, "path": _relative(arm_file), "sha256": sha256_file(arm_file)},
               "call_count": 3 * len(rows), "contingent_replacement_call_cap": len(rows), "runner": asdict(RUNNER)}
    path = runs_root / batch_id / "REQUEST.json"
    data = _bytes(request)
    if path.exists() and path.read_bytes() != data: raise BatchError("existing REQUEST.json differs; evidence is immutable")
    if not path.exists(): _write_once(path, data)
    return path
def _approved(batch: Path) -> dict[str, Any]:
    request_path = batch / "REQUEST.json"
    request = _json(request_path)
    approval = _json(batch / "APPROVED.json", canonical=False)
    if set(approval) != {"request_sha256"} or approval["request_sha256"] != sha256_file(request_path): raise BatchError("APPROVED.json request hash mismatch")
    if request.get("runner") != asdict(RUNNER): raise BatchError("REQUEST runner constants differ from pinned runtime")
    tasks, arm = request.get("tasks"), request.get("arm")
    valid_tasks = isinstance(tasks, list) and bool(tasks) and all(
        isinstance(row, dict) and set(row) == {"task_id", "task_dir", "manifest_sha256"}
        and taskcheck.TASK_ID.fullmatch(str(row["task_id"])) and row["task_dir"] == f"tasks/{row['task_id']}"
        and _sha(row["manifest_sha256"]) for row in tasks)
    valid_arm = isinstance(arm, dict) and set(arm) == {"name", "path", "sha256"} and taskcheck.TASK_ID.fullmatch(str(arm.get("name"))) and str(arm.get("path", "")).startswith("controls/") and _sha(arm.get("sha256"))
    if (request.get("batch_id") != batch.name or not valid_tasks or not valid_arm or len({row["task_id"] for row in tasks}) != len(tasks)
            or request.get("call_count") != 3 * len(tasks) or request.get("contingent_replacement_call_cap") != len(tasks)): raise BatchError("REQUEST schema or batch/call binding is invalid")
    return request
def _auth_home() -> str:
    value = os.environ.get("MDSEVAL_CODEX_HOME")
    auth = Path(value).expanduser() / "auth.json" if value else None
    if not auth or auth.is_symlink() or not auth.is_file() or not auth.stat().st_size: raise BatchError("MDSEVAL_CODEX_HOME must contain a nonempty non-symlink auth.json")
    return str(auth.parent)
def _expose(task: Path, batch_id: str) -> None:
    path = task.parent / "exposures.jsonl"
    rows = taskcheck._verify_exposures(path)
    events = [row for row in rows if row["task_id"] == task.name]
    if any(row["event"] == "retired" for row in events): raise BatchError(f"retired task cannot launch: {task.name}")
    if not events: taskcheck._append_chain(path, {"task_id": task.name, "event": "exposed", "batch_id": batch_id, "reason": None}, "exposures ledger")
def _workspace(task: Path, arm: bytes, parent: Path) -> tuple[Path, str]:
    workspace = parent / "workspace"
    shutil.copytree(task / "public", workspace)
    (workspace / "CODER.md").write_bytes(arm)
    init_repository(workspace); run_git(workspace, "config", "user.name", "MD Eval")
    run_git(workspace, "config", "user.email", "mdseval@invalid.local"); run_git(workspace, "add", "--all")
    run_git(workspace, "commit", "-q", "-m", "baseline")
    return workspace, str(run_git(workspace, "rev-parse", "HEAD")).strip()
def _reserve(path: Path, intent: dict[str, Any]) -> None:
    try:
        path.mkdir(parents=True, exist_ok=False)
    except FileExistsError as exc:
        raise BatchError(f"exclusive-create collision: {path}") from exc
    _write_once(path / "intent.json", _bytes(intent))
def _checker(task: Path, workspace: Path) -> tuple[dict[str, Any], bool, float]:
    with tempfile.TemporaryDirectory(prefix="final-tree-") as temporary:
        clean = Path(temporary) / "tree"; shutil.copytree(workspace, clean, ignore=shutil.ignore_patterns(".git")); started = time.monotonic()
        first, raw = taskcheck.run_checker(task / "check.py", clean); second, raw_two = taskcheck.run_checker(task / "check.py", clean)
        return first, first == second and raw == raw_two, time.monotonic() - started
def _finalize(attempt: Path, ledger: Path) -> None:
    files = {path.relative_to(attempt).as_posix(): sha256_file(path)
             for path in sorted(attempt.rglob("*")) if path.is_file() and path.name != "attempt-manifest.json"}
    manifest = {"files": files, "created": time.time()}
    target = attempt / "attempt-manifest.json"
    _write_once(target, _bytes(manifest))
    taskcheck._append_chain(ledger, {"attempt": attempt.relative_to(ledger.parent).as_posix(),
                                    "manifest_sha256": sha256_file(target)}, "evidence ledger")
def _attempt(task: Path, request: dict[str, Any], arm_row: dict[str, Any], ordinal: int,
             batch: Path, process_runner: Callable[..., ProcessOutcome], codex_home: str) -> bool:
    taskcheck.verify(task)
    manifest_hash = sha256_file(task / "manifest.json")
    contract_hash = sha256_file(task / "public" / ".issue-contract.md")
    expected = next(row["manifest_sha256"] for row in request["tasks"] if row["task_id"] == task.name)
    arm_path = _resolve(arm_row["path"])
    if manifest_hash != expected or sha256_file(arm_path) != arm_row["sha256"]:
        raise BatchError("approved task manifest or arm hash changed")
    destination = batch / task.name / arm_row["name"] / f"attempt-{ordinal}"
    redactor = Redactor()
    with tempfile.TemporaryDirectory(prefix=f"null-batch-{task.name}-") as temporary:
        workspace, baseline = _workspace(task, arm_path.read_bytes(), Path(temporary))
        _reserve(destination, {"task": task.name, "arm": arm_row["name"], "ordinal": ordinal,
                               "task_manifest_sha256": manifest_hash, "arm_sha256": arm_row["sha256"]})
        _expose(task, request["batch_id"])
        final_temp = Path(temporary) / "final.txt"
        command = build_codex_command(RUNNER, workspace, final_temp)
        started = time.monotonic()
        try:
            outcome = process_runner(command, cwd=workspace, input_text=WRAPPER_PROMPT,
                                     timeout=RUNNER.timeout_seconds,
                                     environment=isolated_environment(codex_home))
        except OSError as exc:
            _write_once(destination / "pre-spawn.json", _bytes({"error": f"{type(exc).__name__}: {exc}"}))
            raise BatchError("subject process did not spawn; preserved as pre-spawn failure") from exc
        _write_once(destination / "launch.json", _bytes({"started": time.time(), "command": command, "arm_sha256": arm_row["sha256"],
                                                           "task_manifest_sha256": manifest_hash}))
        duration = time.monotonic() - started
        final = final_temp.read_text(encoding="utf-8", errors="replace") if final_temp.is_file() else ""
        _write_once(destination / "events.jsonl", redact_event_stream(outcome.stdout, redactor).encode())
        _write_once(destination / "stderr.txt", redactor.text(outcome.stderr).encode())
        _write_once(destination / "final.txt", redactor.text(final).encode())
        requirements = _json(task / "manifest.json")["requirements"]
        blank = {"requirements": {key: False for key in requirements}, "regressions": {}, "resolved": False}
        invalid, scoreable, changes, final_hash, checker_duration = "", True, (), "", 0.0
        try:
            audit_final_subject_tree(workspace)
        except Exception as exc:
            invalid, scoreable, checked = f"final tree audit failed: {type(exc).__name__}: {exc}", False, blank
            _write_once(destination / "capture.json", _bytes({"error": invalid}))
            _write_once(destination / "diff.patch", b"")
        else:
          try:
            final_hash = tree_sha256(workspace); capture = capture_git(workspace, baseline, redactor)
            changes = capture.changed_paths
            _write_once(destination / "capture.json", _bytes(asdict(capture)))
            _write_once(destination / "diff.patch", capture.diff.encode())
            if outcome.interrupted or classify_infrastructure_failure(spawn_error=None, timed_out=outcome.timed_out,
                    returncode=outcome.returncode, events_jsonl=outcome.stdout, stderr=outcome.stderr,
                    final_text=final, changed_paths=capture.changed_paths, untracked=capture.untracked):
                _write_once(destination / "infra-invalid.json", _bytes({"error": "runner infrastructure failure"}))
                return False
            coder, contract = workspace / "CODER.md", workspace / ".issue-contract.md"
            if (coder.is_symlink() or not coder.is_file() or sha256_file(coder) != arm_row["sha256"] or contract.is_symlink()
                    or not contract.is_file() or sha256_file(contract) != contract_hash or capture.unauthorized_commit):
                invalid = "protected input changed or subject committed"
          except Exception as exc:  # incomplete capture is replacement-eligible infrastructure
            _write_once(destination / "infra-invalid.json", _bytes({"error": f"{type(exc).__name__}: {exc}"}))
            return False
          try:
            checked, deterministic, checker_duration = _checker(task, workspace); taskcheck.verify(task)
            if not deterministic: invalid = "checker result nondeterministic"
          except Exception as exc:
            invalid, scoreable, checked = f"checker unscoreable: {type(exc).__name__}: {exc}", False, blank
        failed = [key for key, passed in checked["requirements"].items() if not passed]
        omissions = {key: taskcheck._probe_fires(workspace, requirements[key]["omission_probe"], key) if scoreable else False for key in failed}
        target_changes = {key: [path for path in requirements[key]["target_paths"] if path in changes] for key in failed}
        result = {"task_id": task.name, "ordinal": ordinal, "duration_seconds": duration,
                  "checker_duration_seconds": checker_duration, "final_tree_sha256": final_hash,
                  "task_manifest_sha256": manifest_hash, "arm_sha256": arm_row["sha256"],
                  "returncode": outcome.returncode, "timed_out": outcome.timed_out, "interrupted": outcome.interrupted,
                  "requirements": checked["requirements"], "regressions": checked["regressions"],
                  "resolved": checked["resolved"], "omissions": omissions,
                  "omission_only": bool(failed) and all(omissions.values()) and all(checked["regressions"].values()),
                  "target_path_changes": target_changes, "valid": not invalid, "invalid_reason": invalid}
        _write_once(destination / "checker.json", _bytes(checked))
        _write_once(destination / "result.json", _bytes(result))
        _finalize(destination, batch / "evidence-ledger.jsonl")
        return True
def classify(results: list[dict[str, Any]], requirement_count: int, forced_invalid: str = "") -> dict[str, Any]:
    passed = sum(sum(row["requirements"].values()) for row in results)
    q = passed / (3 * requirement_count) if requirement_count else 0.0
    s = sum(row["resolved"] for row in results)
    invalid = forced_invalid or next((row["invalid_reason"] for row in results if not row["valid"]), "")
    wrong = any(row["valid"] and not row["resolved"] and not row["omission_only"] for row in results)
    label = ("invalid" if invalid else "wrong-failure-mode" if wrong else "promising"
             if 0.55 <= q <= 0.90 and s in {1, 2} else "ceiling"
             if s == 3 or (s in {1, 2} and q > 0.90) else "floor")
    return {"q": q, "s": s, "label": label, "fidelity_note": invalid[:200]}
def _retired(task: Path) -> list[str]:
    rows = taskcheck._read_chain(task.parent / "exposures.jsonl", "exposures ledger")
    retired = {row["task_id"] for row in rows if row.get("event") == "retired"}; result = []
    meta = _json(task / "task-meta.json", canonical=False) if (task / "task-meta.json").is_file() else {}
    parent = meta.get("parent_task_id")
    while parent in retired and parent not in result:
        result.append(parent); path = task.parent / parent / "task-meta.json"
        parent = _json(path, canonical=False).get("parent_task_id") if path.is_file() else None
    return result
def _state(base: Path) -> tuple[list[Path], list[dict[str, Any]], int]:
    dirs = sorted(base.glob("attempt-*")) if base.exists() else []
    anchored = _ledger(base.parents[1]); results = []
    for path in dirs:
        manifest = path / "attempt-manifest.json"
        if manifest.is_file():
            relative = path.relative_to(base.parents[1]).as_posix()
            if anchored.get(relative) != sha256_file(manifest): raise BatchError(f"unanchored finalized attempt: {relative}")
            results.append(_json(path / "result.json"))
    return dirs, results, sum((path / "infra-invalid.json").exists() and not (path / "attempt-manifest.json").exists() for path in dirs)
def _disposition(task: Path, results: list[dict[str, Any]], infra: int) -> dict[str, Any]:
    value = classify(results, len(_json(task / "manifest.json")["requirements"]), "second infrastructure failure" if infra >= 2 else "")
    ancestors = _retired(task); value.update({"task_id": task.name, "attempts": [row["ordinal"] for row in results],
                                              "retired_ancestors": ancestors, "task_denominator": 1 + len(ancestors)})
    return value
def launch(batch_id: str, runs_root: Path = ROOT / "runs" / "dev-v2",
           process_runner: Callable[..., ProcessOutcome] = run_process_group,
           require_auth: bool = True) -> None:
    batch = runs_root / batch_id
    request = _approved(batch)
    codex_home = _auth_home() if require_auth else str(Path(tempfile.gettempdir()))
    for row in request["tasks"]:
        task, arm = _resolve(row["task_dir"]), request["arm"]
        base = batch / row["task_id"] / arm["name"]
        dirs, results, infra = _state(base); disposition_path = base / "disposition.json"
        if disposition_path.exists():
            if (len(results) < 3 and infra < 2) or _json(disposition_path) != _disposition(task, results, infra): raise BatchError("premature disposition or recomputation mismatch")
            continue
        while len(results) < 3 and infra < 2:
            ordinal = max([int(path.name.split("-")[-1]) for path in dirs] or [0]) + 1
            usable = _attempt(task, request, arm, ordinal, batch, process_runner, codex_home)
            path = base / f"attempt-{ordinal}"
            dirs.append(path)
            if usable:
                results.append(_json(path / "result.json"))
            else:
                infra += 1
        _write_once(disposition_path, _bytes(_disposition(task, results, infra)))
def verify_batch(batch: Path) -> None:
    anchored = _ledger(batch, required=True)
    manifests = {path.relative_to(batch).as_posix(): path for path in batch.rglob("attempt-manifest.json")}
    anchored = {f"{attempt}/attempt-manifest.json": digest for attempt, digest in anchored.items()}
    if set(manifests) != set(anchored): raise BatchError("finalized attempt set differs from evidence ledger")
    for relative, path in manifests.items():
        if sha256_file(path) != anchored[relative]: raise BatchError(f"attempt manifest hash mismatch: {relative}")
        manifest = _json(path)
        actual = {item.relative_to(path.parent).as_posix(): sha256_file(item)
                  for item in path.parent.rglob("*") if item.is_file() and item != path}
        if manifest.get("files") != actual: raise BatchError(f"attempt evidence differs from manifest: {relative}")
    request = _approved(batch)
    for row in request["tasks"]:
        task = _resolve(row["task_dir"]); verified = taskcheck.verify(task)
        if verified["manifest_sha256"] != row["manifest_sha256"] or sha256_file(_resolve(request["arm"]["path"])) != request["arm"]["sha256"]: raise BatchError("request-bound task or arm hash changed")
        base = batch / row["task_id"] / request["arm"]["name"]; _, results, infra = _state(base)
        path = base / "disposition.json"
        if len(results) < 3 and infra < 2 or not path.is_file() or _json(path) != _disposition(task, results, infra): raise BatchError(f"missing or inconsistent disposition: {task.name}")
def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    queue = commands.add_parser("queue")
    queue.add_argument("batch_id"); queue.add_argument("--task", action="append", type=Path, required=True)
    queue.add_argument("--arm", required=True); queue.add_argument("--arm-file", type=Path, required=True)
    queue.add_argument("--runs-root", type=Path, default=ROOT / "runs" / "dev-v2")
    for name in ("run", "verify"):
        command = commands.add_parser(name); command.add_argument("batch_id")
        command.add_argument("--runs-root", type=Path, default=ROOT / "runs" / "dev-v2")
    args = parser.parse_args(argv)
    try:
        if args.command == "queue":
            path = queue_request(args.batch_id, args.task, args.arm, args.arm_file, args.runs_root); print(json.dumps({"request": str(path), "request_sha256": sha256_file(path)}, sort_keys=True))
        elif args.command == "run": launch(args.batch_id, args.runs_root)
        else: verify_batch(args.runs_root / args.batch_id)
        return 0
    except (BatchError, taskcheck.TaskError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
if __name__ == "__main__":
    raise SystemExit(main())
