from __future__ import annotations

import json
import os
import subprocess
import tempfile
from pathlib import Path

from mdseval.config import ExperimentConfig, load_experiment

ROOT = Path(__file__).resolve().parents[1]


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


def write_json(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")
