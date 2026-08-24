#!/usr/bin/env python3
"""Phase 3 preflight and blinded treatment-packet builder."""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import re
import shutil
import stat
import subprocess
import sys
from pathlib import Path, PurePosixPath

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from mdseval.fixtures import FORBIDDEN_SUBJECT_INPUTS  # noqa: E402

SOURCE_KEYS = {
    "source_url", "issue_url", "base_sha", "fix_sha",
    "solution_patch_sha256", "fix_test_patch_sha256", "checker_command",
    "spdx_id", "license_paths", "removed_instruction_paths", "extraction_note",
}
SOURCE_KEYS_V14 = SOURCE_KEYS | {"issue_closed_at"}
SHA256 = re.compile(r"[0-9a-f]{64}")
GIT_SHA = re.compile(r"[0-9a-f]{40}")
INSTRUCTION_NAMES = set(FORBIDDEN_SUBJECT_INPUTS) | {"CODER.md"}
BUILD_NAMES = {
    "setup.py", "setup.cfg", "pyproject.toml", "tox.ini", "noxfile.py",
    "Pipfile", "Pipfile.lock", "poetry.lock", "uv.lock", ".gitmodules",
}
NATIVE_SUFFIXES = {".c", ".cc", ".cpp", ".h", ".hpp", ".so", ".dylib", ".dll", ".pyd", ".o", ".a"}
CACHE_NAMES = {"__pycache__", ".pytest_cache", ".mypy_cache", ".ruff_cache", ".tox", ".nox", ".cache"}
NETWORK_TEST_MARKERS = (
    "urllib.request", "http.client", "socket.", "urlopen(", "requests.",
)
PREFLIGHT_NOTE = (
    "phase3-preflight-v1: no inherited evaluator instructions, installs, build "
    "hooks, native code, pytest plugins, submodules, LFS pointers, symlinks, "
    "networked tests, bytecode, hidden Git trees, or hiding .gitignore files"
)
FULL_SCALE_NOTE = (
    "section14-full-scale-preflight-v1: no inherited evaluator instructions, "
    "hidden Git trees/submodules, cache artifacts, symlinks, LFS pointers, or "
    "leaked private fix tests; full-repository build metadata, native content, "
    "pytest/network-test source, .gitattributes, and non-hiding .gitignore "
    "files are retained; every included task file passes git check-ignore"
)


class PreflightError(RuntimeError):
    pass

def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()

def load_object(path: Path) -> dict:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise PreflightError(f"invalid JSON {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise PreflightError(f"JSON must be an object: {path}")
    return value

def safe_relative(value: object, label: str) -> str:
    if not isinstance(value, str) or not value:
        raise PreflightError(f"{label} must be a nonempty relative path")
    path = PurePosixPath(value)
    if path.is_absolute() or ".." in path.parts or path.as_posix() != value:
        raise PreflightError(f"unsafe {label}: {value!r}")
    return value

def files(root: Path):
    if root.is_symlink() or not root.is_dir():
        raise PreflightError(f"missing or unsafe directory: {root}")
    for path in sorted(root.rglob("*")):
        relative = path.relative_to(root)
        mode = path.lstat().st_mode
        if stat.S_ISLNK(mode) or not (stat.S_ISDIR(mode) or stat.S_ISREG(mode)):
            raise PreflightError(f"symlink or special file: {root.name}/{relative}")
        if path.is_file():
            yield path, relative

def rejection_scan(task: Path, *, include_blind: bool = True, full_scale: bool = False) -> None:
    private_relatives: set[str] = set()
    tree_names = ("public", "reference", "private") + (("blind",) if include_blind else ())
    for tree_name in tree_names:
        tree = task / tree_name
        for entry in tree.rglob("*"):
            relative = entry.relative_to(tree)
            if set(relative.parts) & (INSTRUCTION_NAMES | CACHE_NAMES | {".git"}):
                raise PreflightError(f"forbidden or junk path: {tree_name}/{relative}")
        for path, relative in files(tree):
            parts = set(relative.parts)
            name = path.name
            if name in INSTRUCTION_NAMES or parts & INSTRUCTION_NAMES:
                raise PreflightError(f"forbidden subject input: {tree_name}/{relative}")
            if name == ".gitmodules" or (not full_scale and (
                    name in {".gitignore", ".gitattributes"} or name in BUILD_NAMES)):
                raise PreflightError(f"hiding/build/submodule file: {tree_name}/{relative}")
            if not full_scale and name.startswith("requirements") and name.endswith((".txt", ".in")):
                raise PreflightError(f"install input: {tree_name}/{relative}")
            if name in CACHE_NAMES | {".git"} or path.suffix in {".pyc", ".pyo"}:
                raise PreflightError(f"junk path: {tree_name}/{relative}")
            if not full_scale and path.suffix.lower() in NATIVE_SUFFIXES:
                raise PreflightError(f"native code: {tree_name}/{relative}")
            data = path.read_bytes()
            if data.startswith(b"version https://git-lfs.github.com/spec/v1"):
                raise PreflightError(f"Git LFS pointer: {tree_name}/{relative}")
            if path.suffix == ".py" and not full_scale:
                text = data.decode("utf-8", errors="replace")
                if name == "conftest.py" or "pytest_plugins" in text or re.search(
                    r"(^|\n)\s*(import pytest|from pytest\b)", text
                ):
                    raise PreflightError(f"pytest input: {tree_name}/{relative}")
                if "test" in relative.as_posix().lower() and any(
                    marker in text for marker in NETWORK_TEST_MARKERS
                ):
                    raise PreflightError(f"networked test: {tree_name}/{relative}")
            if tree_name == "private":
                private_relatives.add(relative.as_posix())
    leaked = sorted(relative for relative in private_relatives
                    if (task / "public" / relative).is_file()
                    and (not full_scale or sha256(task / "private" / relative)
                         == sha256(task / "public" / relative)))
    if leaked:
        raise PreflightError(f"private fix tests leaked into public: {leaked}")

def validate_trackable(task: Path) -> None:
    top = subprocess.run(["git", "-C", str(task), "rev-parse", "--show-toplevel"],
                         capture_output=True, text=True, check=False)
    if top.returncode:
        raise PreflightError("full-scale task is not inside a Git worktree")
    root = Path(top.stdout.strip()).resolve()
    try:
        included = [path for path, _ in files(task)]
        if task / "manifest.json" not in included: included.append(task / "manifest.json")
        relatives = [path.relative_to(root).as_posix() for path in included]
    except ValueError as exc:
        raise PreflightError("full-scale task files escape the Git worktree") from exc
    checked = subprocess.run(
        ["git", "-C", str(root), "check-ignore", "--no-index", "-z", "--stdin"],
        input=("\0".join(relatives) + "\0").encode(), capture_output=True, check=False)
    if (checked.returncode, bool(checked.stdout)) not in {(0, True), (1, False)}:
        raise PreflightError(f"git check-ignore failed: {checked.stderr.decode(errors='replace').strip()}")
    ignored = sorted(item.decode(errors="replace") for item in checked.stdout.split(b"\0") if item)
    if ignored:
        raise PreflightError(f".gitignore would omit task bytes: {ignored[:20]}")

def validate_source(task: Path, *, finalize: bool, section14: bool = False) -> dict:
    source_path = task / "failure-source.json"
    source = load_object(source_path)
    full_scale = section14 or "issue_closed_at" in source
    note = FULL_SCALE_NOTE if full_scale else PREFLIGHT_NOTE
    expected = SOURCE_KEYS_V14 if full_scale else SOURCE_KEYS
    if set(source) != expected:
        raise PreflightError(f"failure-source keys differ: {sorted(set(source) ^ expected)}")
    if finalize and not str(source.get("extraction_note", "")).startswith(note):
        detail = str(source.get("extraction_note", "")).strip()
        if full_scale and detail.startswith(PREFLIGHT_NOTE):
            detail = detail[len(PREFLIGHT_NOTE):].removeprefix(";").strip()
        source["extraction_note"] = note + (f"; {detail}" if detail else "")
        source_path.write_text(
            json.dumps(source, sort_keys=True, separators=(",", ":")) + "\n",
            encoding="utf-8",
        )
    if full_scale:
        closed = source["issue_closed_at"]
        try:
            if not isinstance(closed, str) or not re.fullmatch(
                    r"\d{4}-\d{2}-\d{2}(?:T.*(?:Z|[+-]\d{2}:\d{2}))?", closed):
                raise ValueError
            parsed = (dt.datetime.fromisoformat(closed.replace("Z", "+00:00"))
                      if "T" in closed else dt.date.fromisoformat(closed))
            if isinstance(parsed, dt.datetime) and parsed.utcoffset() is None:
                raise ValueError
        except ValueError as exc:
            raise PreflightError("issue_closed_at must be an ISO-8601 date or zoned timestamp") from exc
    for key in ("source_url", "issue_url"):
        if not isinstance(source[key], str) or not source[key].startswith("https://"):
            raise PreflightError(f"{key} must be an https URL")
    for key in ("base_sha", "fix_sha"):
        if not isinstance(source[key], str) or not GIT_SHA.fullmatch(source[key]):
            raise PreflightError(f"{key} must be a full Git SHA")
    for key in ("solution_patch_sha256", "fix_test_patch_sha256"):
        if not isinstance(source[key], str) or not SHA256.fullmatch(source[key]):
            raise PreflightError(f"{key} must be sha256")
    if source["checker_command"] != "python3 check.py WORKSPACE":
        raise PreflightError("unexpected checker_command")
    if not isinstance(source["spdx_id"], str) or not source["spdx_id"]:
        raise PreflightError("spdx_id must be nonempty")
    licenses = source["license_paths"]
    if not isinstance(licenses, list) or not licenses:
        raise PreflightError("license_paths must be nonempty")
    for index, row in enumerate(licenses):
        if not isinstance(row, dict) or set(row) != {"path", "sha256"}:
            raise PreflightError(f"license_paths[{index}] schema")
        relative = safe_relative(row["path"], f"license_paths[{index}].path")
        path = task / relative
        if not path.is_file() or row["sha256"] != sha256(path):
            raise PreflightError(f"license hash mismatch: {relative}")
    removed = source["removed_instruction_paths"]
    if not isinstance(removed, list) or not all(isinstance(item, str) for item in removed):
        raise PreflightError("removed_instruction_paths must be a string list")
    if not isinstance(source["extraction_note"], str) or not source["extraction_note"].startswith(note):
        raise PreflightError("preflight output is not recorded in extraction_note")
    return source


def preflight(task: Path, *, finalize: bool, section14: bool = False) -> dict:
    task = task.resolve()
    source = validate_source(task, finalize=finalize, section14=section14)
    full_scale = section14 or "issue_closed_at" in source
    rejection_scan(task, full_scale=full_scale)
    if full_scale:
        validate_trackable(task)
    meta = load_object(task / "task-meta.json")
    requirements = load_object(task / "requirements.json")
    if meta != {"layout_version": 3, "parent_task_id": None, "salience": "enumerated"}:
        raise PreflightError("Phase 3 task-meta must be enumerated task-layout-v3")
    if not 1 <= len(requirements) <= 3:
        raise PreflightError("Phase 3 tasks require one to three requirements")
    if full_scale and load_object(task / "blind-calibration.json") != {
            "seal_status": "UNSEALED", "use": "calibration-only"}:
        raise PreflightError("Section 14 blind-calibration.json contract is invalid")
    checker = (task / "check.py").read_text(encoding="utf-8")
    for token in ("TemporaryDirectory", "copytree", "copy2", "PYTHONDONTWRITEBYTECODE"):
        if token not in checker:
            raise PreflightError(f"checker lacks private-overlay mechanic: {token}")
    result = {"task_id": task.name, "preflight": "pass", "source": source}
    if full_scale:
        result["full_scale"] = True
    if section14:
        result["section14_mode"] = True
    return result


def packet(task: Path, output: Path) -> dict:
    preflight(task, finalize=False)
    if output.exists() or output.is_symlink():
        raise PreflightError(f"refusing to overwrite packet: {output}")
    output.mkdir(parents=True)
    for path, relative in files(task / "public"):
        if relative.as_posix() == ".issue-contract.md":
            continue
        target = output / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, target)
    if (output / ".issue-contract.md").exists():
        raise PreflightError("issue contract leaked into packet")
    return {"task_id": task.name, "packet": str(output.resolve()), "files": sum(1 for _ in files(output))}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    check = commands.add_parser("preflight")
    check.add_argument("task", type=Path)
    check.add_argument("--finalize", action="store_true")
    scan = commands.add_parser("scan")
    scan.add_argument("task", type=Path)
    for command in (check, scan): command.add_argument(
        "--section14", action="store_true", help="force Section 14 schema and gates")
    build = commands.add_parser("packet")
    build.add_argument("task", type=Path)
    build.add_argument("output", type=Path)
    args = parser.parse_args()
    try:
        if args.command == "preflight":
            result = preflight(args.task, finalize=args.finalize, section14=args.section14)
        elif args.command == "scan":
            task = args.task.resolve()
            source = validate_source(task, finalize=False, section14=args.section14)
            full_scale = args.section14 or "issue_closed_at" in source
            rejection_scan(task, include_blind=False, full_scale=full_scale)
            if full_scale:
                validate_trackable(task)
            result = {"task_id": args.task.name, "pre_blind_scan": "pass"}
            if args.section14:
                result["section14_mode"] = True
        else:
            result = packet(args.task, args.output)
        print(json.dumps(result, sort_keys=True, separators=(",", ":")))
        return 0
    except (OSError, UnicodeError, PreflightError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
