from __future__ import annotations

import json
import os
import shutil
import stat
import subprocess
import tempfile
from contextlib import contextmanager
from pathlib import Path, PurePosixPath
from typing import Iterator, Sequence

from mdseval.config import ExperimentConfig, load_experiment

ROOT = Path(__file__).resolve().parents[1]

_CHECKOUT_INPUT_SPECS = (
    ".gitignore",
    "pyproject.toml",
    "mdseval",
    "src/mdseval",
    "experiments",
    "schemas",
    "evals",
    "targets",
    "candidates",
    "controls",
)
_CHECKOUT_REQUIRED_FILES = frozenset(
    {
        ".gitignore",
        "pyproject.toml",
        "mdseval/__init__.py",
        "src/mdseval/__init__.py",
        "src/mdseval/cli.py",
        "src/mdseval/execution.py",
        "experiments/coder-v1.json",
        "schemas/case.schema.json",
        "schemas/experiment.schema.json",
        "schemas/judge-output.schema.json",
        "targets/coder/champion.md",
        "candidates/coder/karpathy-v1.md",
        "controls/coder/deliberately-bad.md",
    }
)
_FORBIDDEN_CHECKOUT_COMPONENTS = frozenset(
    {
        ".git",
        ".mdseval-codex-home",
        ".pytest_cache",
        ".mypy_cache",
        ".ruff_cache",
        "__pycache__",
        "runs",
        "reports",
    }
)
_FORBIDDEN_CHECKOUT_NAMES = frozenset({"auth.json"})
_FORBIDDEN_CHECKOUT_SUFFIXES = (".pyc", ".pyo")


def experiment() -> ExperimentConfig:
    return load_experiment(ROOT / "experiments" / "coder-v1.json")


def git(repo: Path, *args: str) -> str:
    environment = {
        "PATH": os.environ["PATH"],
        "GIT_CONFIG_NOSYSTEM": "1",
        "GIT_CONFIG_GLOBAL": os.devnull,
        "GIT_TERMINAL_PROMPT": "0",
    }
    process = subprocess.run(
        ["git", "-c", "core.fsmonitor=false", *args],
        cwd=repo,
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        env=environment,
    )
    return process.stdout.strip()


def _tracked_evaluator_manifest(source: Path) -> tuple[PurePosixPath, ...]:
    """Return the Git-indexed evaluator inputs, never local untracked state."""

    environment = {
        "PATH": os.environ["PATH"],
        "GIT_CONFIG_NOSYSTEM": "1",
        "GIT_CONFIG_GLOBAL": os.devnull,
        "GIT_TERMINAL_PROMPT": "0",
    }
    process = subprocess.run(
        [
            "git",
            "-c",
            "core.fsmonitor=false",
            "ls-files",
            "-z",
            "--",
            *_CHECKOUT_INPUT_SPECS,
        ],
        cwd=source,
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=environment,
    )
    entries: list[PurePosixPath] = []
    for raw_path in process.stdout.split(b"\0"):
        if not raw_path:
            continue
        try:
            value = raw_path.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise ValueError("test checkout manifest path is not UTF-8") from exc
        relative = PurePosixPath(value)
        if (
            relative.is_absolute()
            or not relative.parts
            or any(part in {"", ".", ".."} for part in relative.parts)
        ):
            raise ValueError(f"unsafe test checkout manifest path: {value!r}")
        if (
            any(part in _FORBIDDEN_CHECKOUT_COMPONENTS for part in relative.parts)
            or relative.name in _FORBIDDEN_CHECKOUT_NAMES
            or relative.name.endswith(_FORBIDDEN_CHECKOUT_SUFFIXES)
        ):
            raise ValueError(f"forbidden test checkout manifest path: {value!r}")
        if not (
            value in {".gitignore", "pyproject.toml"}
            or any(value.startswith(f"{root}/") for root in _CHECKOUT_INPUT_SPECS[1:])
        ):
            raise ValueError(f"unapproved test checkout manifest path: {value!r}")
        entries.append(relative)

    manifest = tuple(sorted(entries, key=PurePosixPath.as_posix))
    if len(manifest) != len(set(manifest)):
        raise ValueError("test checkout manifest contains duplicate paths")
    missing = _CHECKOUT_REQUIRED_FILES - {path.as_posix() for path in manifest}
    if missing:
        raise ValueError(f"test checkout manifest is incomplete: {sorted(missing)}")
    return manifest


def write_json(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")


def no_ignore_inventory(
    root: Path, relative_roots: Sequence[str]
) -> list[dict[str, object]]:
    """Inventory exact on-disk entries without consulting ignore rules."""

    root = root.resolve()
    records: list[dict[str, object]] = []

    def visit(path: Path) -> None:
        relative = path.relative_to(root).as_posix()
        metadata = path.lstat()
        mode = f"{stat.S_IMODE(metadata.st_mode):04o}"
        if stat.S_ISREG(metadata.st_mode):
            import hashlib

            digest = hashlib.sha256()
            with path.open("rb") as handle:
                for block in iter(lambda: handle.read(1024 * 1024), b""):
                    digest.update(block)
            records.append(
                {
                    "path": relative,
                    "type": "file",
                    "mode": mode,
                    "size": metadata.st_size,
                    "sha256": digest.hexdigest(),
                }
            )
            return
        if not stat.S_ISDIR(metadata.st_mode):
            kind = "symlink" if stat.S_ISLNK(metadata.st_mode) else "special file"
            raise ValueError(f"{kind} is not allowed in an evidence inventory: {relative}")
        records.append(
            {
                "path": relative,
                "type": "directory",
                "mode": mode,
                "size": metadata.st_size,
                "sha256": None,
            }
        )
        with os.scandir(path) as entries:
            children = sorted(entries, key=lambda item: item.name)
        for child in children:
            child.stat(follow_symlinks=False)
            visit(Path(child.path))

    for relative_root in sorted(relative_roots):
        candidate = root / relative_root
        if not candidate.exists() and not candidate.is_symlink():
            raise FileNotFoundError(relative_root)
        visit(candidate)
    return sorted(records, key=lambda item: str(item["path"]))


def _copy_evaluator_checkout(source: Path, destination: Path) -> None:
    """Copy only the explicit tracked evaluator-input manifest."""

    source = source.absolute()
    source_metadata = source.lstat()
    if stat.S_ISLNK(source_metadata.st_mode) or not stat.S_ISDIR(source_metadata.st_mode):
        raise ValueError(f"test checkout source is not a real directory: {source}")
    manifest = _tracked_evaluator_manifest(source)

    directories = {PurePosixPath(".")}
    for relative in manifest:
        directories.update(relative.parents)
    for relative in sorted(directories, key=lambda path: (len(path.parts), path.as_posix())):
        source_dir = source if relative == PurePosixPath(".") else source / relative
        metadata = source_dir.lstat()
        if stat.S_ISLNK(metadata.st_mode) or not stat.S_ISDIR(metadata.st_mode):
            raise ValueError(f"test checkout source contains an unsafe directory: {source_dir}")
        target_dir = destination if relative == PurePosixPath(".") else destination / relative
        target_dir.mkdir(exist_ok=relative != PurePosixPath("."))
        os.chmod(target_dir, stat.S_IMODE(metadata.st_mode))

    for relative in manifest:
        source_path = source / relative
        metadata = source_path.lstat()
        if stat.S_ISLNK(metadata.st_mode):
            raise ValueError(f"test checkout source contains a symlink: {source_path}")
        if not stat.S_ISREG(metadata.st_mode):
            raise ValueError(f"test checkout source contains a special file: {source_path}")
        shutil.copy2(source_path, destination / relative, follow_symlinks=False)

    (destination / "runs").mkdir()
    (destination / "reports").mkdir()


@contextmanager
def temporary_evaluator_checkout(
    experiment_relative: str = "experiments/coder-v1.json",
) -> Iterator[tuple[Path, ExperimentConfig]]:
    """Yield an isolated, committed evaluator checkout and loaded experiment."""

    with tempfile.TemporaryDirectory() as temporary:
        checkout = Path(temporary) / "repo"
        _copy_evaluator_checkout(ROOT, checkout)
        git(checkout, "init", "-q")
        git(checkout, "config", "user.name", "MD Eval Tests")
        git(checkout, "config", "user.email", "mdseval-tests@example.invalid")
        git(checkout, "add", ".")
        git(checkout, "commit", "-q", "-m", "isolated evaluator fixture")
        yield checkout, load_experiment(checkout / experiment_relative)
