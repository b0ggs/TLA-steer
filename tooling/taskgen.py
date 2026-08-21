#!/usr/bin/env python3
"""Generate an untrusted task tree from a versioned recipe and agent command."""

from __future__ import annotations

import argparse
import json
import shutil
import stat
import subprocess
import tempfile
from pathlib import Path
from typing import Any

try:
    from . import taskcheck
except ImportError:  # direct script execution
    import taskcheck  # type: ignore

RECIPE_KEYS = {"task_id", "family", "theme", "requirement_count", "salience", "md_filename"}
FAMILIES = {"bug", "feature", "refactor", "cli"}
OUTPUTS = ("public", "check.py", "reference", "requirements.json", "task-meta.json")
FORBIDDEN = ("blind", "blind.provenance.json", "manifest.json")
DEFAULT_PROMPT = Path(__file__).with_name("prompts") / "taskgen-v1.txt"


class TaskgenError(RuntimeError):
    """The recipe, agent, or generated tree violated the factory contract."""


def _recipe(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise TaskgenError(f"invalid recipe: {exc}") from exc
    if not isinstance(value, dict) or set(value) != RECIPE_KEYS:
        raise TaskgenError("recipe must contain exactly the v1 keys")
    count = value["requirement_count"]
    strings = ("task_id", "family", "theme", "salience", "md_filename")
    if (not all(isinstance(value[key], str) for key in strings)
            or not taskcheck.TASK_ID.fullmatch(value["task_id"])
            or value["family"] not in FAMILIES
            or not value["theme"].strip()
            or isinstance(count, bool) or not isinstance(count, int) or not 8 <= count <= 12
            or value["salience"] not in {"enumerated", "pointer", "none"}):
        raise TaskgenError("recipe values are invalid")
    try:
        taskcheck._md_filename(value["md_filename"])
    except taskcheck.TaskError as exc:
        raise TaskgenError(str(exc)) from exc
    return value


def _regular_tree(root: Path) -> None:
    if root.is_symlink() or not root.is_dir():
        raise TaskgenError(f"generated directory is missing or unsafe: {root.name}")
    for path in root.rglob("*"):
        mode = path.lstat().st_mode
        if not (stat.S_ISDIR(mode) or stat.S_ISREG(mode)):
            raise TaskgenError(f"generated path is not a regular file/directory: {path.relative_to(root)}")


def _render(prompt_path: Path, recipe: dict[str, Any]) -> str:
    public_recipe = {key: value for key, value in recipe.items() if key != "md_filename"}
    requirement_ids = ", ".join(f"R{index}" for index in range(1, recipe["requirement_count"] + 1))
    try:
        template = prompt_path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        raise TaskgenError(f"cannot read prompt: {exc}") from exc
    return (template.replace("{recipe_json}", taskcheck.canonical(public_recipe))
            .replace("{requirement_count}", str(recipe["requirement_count"]))
            .replace("{requirement_ids}", requirement_ids))


def generate(recipe_path: Path, tasks_root: Path, command_template: list[str],
             prompt_path: Path = DEFAULT_PROMPT, timeout: int = 900) -> Path:
    recipe = _recipe(recipe_path)
    destination = tasks_root.resolve() / recipe["task_id"]
    if destination.exists():
        raise TaskgenError(f"destination already exists: {destination}")
    prompt = _render(prompt_path, recipe)
    if not command_template or not any("{prompt}" in item for item in command_template):
        raise TaskgenError("agent command must contain {prompt}")
    command = [item.replace("{prompt}", prompt) for item in command_template]
    with tempfile.TemporaryDirectory(prefix="taskgen-") as temporary:
        scratch = Path(temporary)
        try:
            result = subprocess.run(command, cwd=scratch, capture_output=True, text=True,
                                    timeout=timeout, check=False)
        except (OSError, subprocess.TimeoutExpired) as exc:
            raise TaskgenError(f"agent invocation failed: {type(exc).__name__}: {exc}") from exc
        if result.returncode:
            raise TaskgenError(f"agent exited {result.returncode}: {(result.stderr or result.stdout)[-500:]}")
        emitted = [name for name in FORBIDDEN if (scratch / name).exists()]
        if emitted:
            raise TaskgenError(f"agent emitted forbidden output: {emitted}")
        if any(not (scratch / name).exists() for name in OUTPUTS):
            raise TaskgenError("agent did not emit the complete task tree")
        _regular_tree(scratch / "public")
        _regular_tree(scratch / "reference")
        meta = taskcheck._json_file(scratch / "task-meta.json", "generated task-meta.json")
        requirements = taskcheck._json_file(scratch / "requirements.json", "generated requirements.json")
        if meta != {"layout_version": 3, "salience": recipe["salience"], "parent_task_id": None}:
            raise TaskgenError("generated task-meta.json does not match the recipe")
        if len(requirements) != recipe["requirement_count"]:
            raise TaskgenError("generated requirement count does not match the recipe")
        if not (scratch / "public" / ".issue-contract.md").is_file():
            raise TaskgenError("generated public tree lacks .issue-contract.md")
        try:
            public, public_raw = taskcheck.run_checker(scratch / "check.py", scratch / "public")
            sentinel, sentinel_raw = taskcheck.run_checker(
                scratch / "check.py", scratch / "public", coder_sentinel=True,
                md_filename=recipe["md_filename"])
            reference, reference_raw = taskcheck.run_checker(scratch / "check.py", scratch / "reference")
            repeated, repeated_raw = taskcheck.run_checker(scratch / "check.py", scratch / "reference")
            taskcheck._validate_requirements(
                scratch, requirements, set(public["requirements"]), 3,
                recipe["salience"], 3, 4)
        except taskcheck.TaskError as exc:
            raise TaskgenError(f"generated task fails preflight: {exc}") from exc
        if (public["resolved"] or not all(public["regressions"].values())
                or public != sentinel or public_raw != sentinel_raw or not reference["resolved"]
                or reference != repeated or reference_raw != repeated_raw
                or set(reference["requirements"]) != set(public["requirements"])):
            raise TaskgenError("generated task fails pristine/reference preflight")
        try:
            destination.mkdir(parents=True, exist_ok=False)
        except FileExistsError as exc:
            raise TaskgenError(f"destination already exists: {destination}") from exc
        try:
            for name in OUTPUTS:
                source = scratch / name
                if source.is_symlink() or not (source.is_dir() or source.is_file()):
                    raise TaskgenError(f"unsafe generated output: {name}")
                shutil.copytree(source, destination / name) if source.is_dir() else shutil.copy2(source, destination / name)
        except BaseException:
            shutil.rmtree(destination, ignore_errors=True)
            raise
    return destination


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("recipe", type=Path)
    parser.add_argument("--tasks-root", type=Path, default=Path("tasks"))
    parser.add_argument("--prompt", type=Path, default=DEFAULT_PROMPT)
    parser.add_argument("--timeout", type=int, default=900)
    parser.add_argument("--agent-command", nargs=argparse.REMAINDER, required=True)
    args = parser.parse_args(argv)
    try:
        path = generate(args.recipe, args.tasks_root, args.agent_command, args.prompt, args.timeout)
        print(taskcheck.canonical({"task": str(path)}))
        return 0
    except (TaskgenError, taskcheck.TaskError) as exc:
        print(f"ERROR: {exc}", file=__import__("sys").stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
