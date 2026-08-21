#!/usr/bin/env python3
"""Produce a provenance-bound blind solution in an isolated scratch tree."""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import os
import shutil
import stat
import subprocess
import tempfile
import uuid
from pathlib import Path

try:
    from . import taskcheck
except ImportError:  # direct script execution
    import taskcheck  # type: ignore

DEFAULT_PROMPT = Path(__file__).with_name("prompts") / "blindsolve-v1.txt"


class BlindsolveError(RuntimeError):
    """The blind-solve contract was violated."""


def _safe_tree(root: Path) -> None:
    if root.is_symlink() or not root.is_dir():
        raise BlindsolveError("solver output root is missing or unsafe")
    for path in root.rglob("*"):
        mode = path.lstat().st_mode
        if not (stat.S_ISDIR(mode) or stat.S_ISREG(mode)):
            raise BlindsolveError(f"solver emitted symlink or special file: {path.relative_to(root)}")


def _replace_tree(source: Path, destination: Path) -> None:
    token = uuid.uuid4().hex
    stage_root = Path(tempfile.mkdtemp(prefix=f".{destination.parent.name}-blind-stage-",
                                      dir=destination.parent.parent))
    staged = stage_root / "blind"
    backup = destination.parent.parent / f".{destination.parent.name}-blind-old-{token}"
    shutil.copytree(source, staged)
    moved_old = False
    try:
        if destination.exists():
            if destination.is_symlink() or not destination.is_dir():
                raise BlindsolveError("existing blind output is unsafe")
            os.replace(destination, backup)
            moved_old = True
        os.replace(staged, destination)
    except BaseException:
        if moved_old and backup.exists() and not destination.exists():
            os.replace(backup, destination)
        raise
    finally:
        shutil.rmtree(stage_root, ignore_errors=True)
    if moved_old:
        shutil.rmtree(backup)


def solve(task_dir: Path, command_template: list[str], solver_agent: str,
          sandbox_flags: list[str], prompt_path: Path = DEFAULT_PROMPT,
          timeout: int = 900, exposures: Path | None = None) -> Path:
    task = task_dir.resolve()
    if not taskcheck.TASK_ID.fullmatch(task.name):
        raise BlindsolveError("invalid task id")
    exposure_path = (exposures or task.parent / "exposures.jsonl").resolve()
    if any(row["task_id"] == task.name for row in taskcheck._verify_exposures(exposure_path)):
        raise BlindsolveError(f"task is frozen by exposures ledger: {task.name}")
    if not solver_agent.strip() or not sandbox_flags:
        raise BlindsolveError("solver identity and sandbox flags are required")
    try:
        prompt = prompt_path.read_text(encoding="utf-8").replace("{task_id}", task.name)
    except (OSError, UnicodeError) as exc:
        raise BlindsolveError(f"cannot read prompt: {exc}") from exc
    if not command_template or not any("{prompt}" in item for item in command_template):
        raise BlindsolveError("solver command must contain {prompt}")
    command = [item.replace("{prompt}", prompt) for item in command_template]
    public_hash = taskcheck.tree_sha256(task / "public")
    with tempfile.TemporaryDirectory(prefix=f"blindsolve-{task.name}-") as temporary:
        workspace = Path(temporary) / "workspace"
        shutil.copytree(task / "public", workspace)
        try:
            environment = os.environ.copy()
            environment["PYTHONDONTWRITEBYTECODE"] = "1"
            result = subprocess.run(command, cwd=workspace, env=environment,
                                    capture_output=True, text=True, timeout=timeout, check=False)
        except (OSError, subprocess.TimeoutExpired) as exc:
            raise BlindsolveError(f"solver invocation failed: {type(exc).__name__}: {exc}") from exc
        if result.returncode:
            raise BlindsolveError(f"solver exited {result.returncode}: {(result.stderr or result.stdout)[-500:]}")
        _safe_tree(workspace)
        if taskcheck.tree_sha256(task / "public") != public_hash:
            raise BlindsolveError("solver mutated the public task tree")
        _replace_tree(workspace, task / "blind")
    if taskcheck.tree_sha256(task / "public") != public_hash:
        raise BlindsolveError("public task tree changed during blind replacement")
    provenance = {
        "solver_agent": solver_agent,
        "solver_command_sha256": hashlib.sha256(taskcheck.canonical(command).encode()).hexdigest(),
        "sandbox_flags": sandbox_flags,
        "timestamp": dt.datetime.now(dt.timezone.utc).isoformat(),
        "input_tree_sha256": public_hash,
    }
    target = task / "blind.provenance.json"
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=task, delete=False) as stream:
        stream.write(taskcheck.canonical(provenance) + "\n")
        temporary_path = Path(stream.name)
    os.replace(temporary_path, target)
    return target


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("task", type=Path)
    parser.add_argument("--solver-agent", required=True)
    parser.add_argument("--sandbox-flag", action="append", required=True)
    parser.add_argument("--prompt", type=Path, default=DEFAULT_PROMPT)
    parser.add_argument("--timeout", type=int, default=900)
    parser.add_argument("--exposures", type=Path)
    parser.add_argument("--agent-command", nargs=argparse.REMAINDER, required=True)
    args = parser.parse_args(argv)
    try:
        path = solve(args.task, args.agent_command, args.solver_agent, args.sandbox_flag,
                     args.prompt, args.timeout, args.exposures)
        print(taskcheck.canonical({"provenance": str(path)}))
        return 0
    except (BlindsolveError, taskcheck.TaskError) as exc:
        print(f"ERROR: {exc}", file=__import__("sys").stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
