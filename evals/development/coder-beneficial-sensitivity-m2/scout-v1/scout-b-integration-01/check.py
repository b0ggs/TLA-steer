#!/usr/bin/env python3
"""Objective checker for scout-b-integration-01."""

import argparse
import importlib
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

sys.dont_write_bytecode = True
TASK_ID = "scout-b-integration-01"
EXPECTED_CONTRACT = """# Publish a handoff digest

Connect the existing JSONL reader, renderer, and command-line boundary so a
user can publish a digest file. Keep the task small and preserve the existing
`show` behavior.

## Main request

### R1 — Multi-record publishing

Implement `publish_digest(input_path, output_path, tag)` in `src/handoff_digest/publish.py`. It must read every JSON object from `input_path` in source order and write exactly one `render_record` line for each object to `output_path`, in the same order, with a newline after every rendered line.

Seven secondary requirements are intentionally distributed beside the affected
components. The public notes marked R2 through R8 are all part of this task.
The compatibility statement marked G1 is a regression constraint.
"""
EXPECTED_INIT = """\"\"\"Small JSONL handoff-digest package.\"\"\"

from .publish import publish_digest
from .records import read_records
from .render import render_record

__all__ = [\"publish_digest\", \"read_records\", \"render_record\"]
"""
EXPECTED_MAIN = "from .cli import main\n\nraise SystemExit(main())\n"
EXPECTED_SAMPLE = b'{"title":"Ready","owner":"Ada"}\n'
EXPECTED_FILES = (".issue-contract.md", "CODER.md", "CHANGELOG.md", "README.md", "config/publish.json", "docs/configuration.md", "docs/digest-format.md", "samples/records.jsonl", "src/handoff_digest/__init__.py", "src/handoff_digest/__main__.py", "src/handoff_digest/cli.py", "src/handoff_digest/publish.py", "src/handoff_digest/records.py", "src/handoff_digest/render.py")


def assertion(function):
    try:
        function()
        return {"passed": True, "details": "objective assertion passed"}
    except Exception as exc:
        return {"passed": False, "details": f"{type(exc).__name__}: {exc}"}


def require(condition, message):
    if not condition:
        raise AssertionError(message)


def load_modules(root):
    sys.path.insert(0, str(root / "src"))
    for name in tuple(sys.modules):
        if name == "handoff_digest" or name.startswith("handoff_digest."):
            sys.modules.pop(name, None)
    package = importlib.import_module("handoff_digest")
    return package, importlib.import_module("handoff_digest.records"), importlib.import_module("handoff_digest.render")


def run_cli(root, *arguments):
    env = {**os.environ, "PYTHONDONTWRITEBYTECODE": "1", "PYTHONPATH": str(root / "src")}
    return subprocess.run([sys.executable, "-m", "handoff_digest", *map(str, arguments)], cwd=root, capture_output=True, text=True, timeout=30, env=env, check=False)


def check(root):
    environment = assertion(lambda: require(all((root / path).is_file() for path in EXPECTED_FILES) and not (root / "check.py").exists(), "public packet shape invalid"))
    try:
        package, records, render = load_modules(root)
        load_error = None
    except Exception as exc:
        package = records = render = None
        load_error = exc

    def loaded():
        if load_error is not None:
            raise load_error

    def r1():
        loaded()
        with tempfile.TemporaryDirectory() as temp:
            source, output = Path(temp) / "records.jsonl", Path(temp) / "digest.md"
            source.write_text('{"title":"Alpha","owner":"Ada"}\n{"title":"Beta","owner":"Bob"}\n', encoding="utf-8")
            package.publish_digest(source, output, "TASK")
            require(output.read_text(encoding="utf-8") == "* TASK: Alpha (Ada)\n* TASK: Beta (Bob)\n", "multi-record digest differs")

    def r2():
        loaded()
        with tempfile.TemporaryDirectory() as temp:
            source = Path(temp) / "records.jsonl"
            source.write_text('{"title":"A"}\n\n   \n{"title":"B"}\n', encoding="utf-8")
            require(records.read_records(source) == [{"title": "A"}, {"title": "B"}], "blank-line/order behavior differs")

    def r3():
        loaded()
        require(render.render_record({"title": "Ready"}, "OPS") == "* OPS: Ready (unassigned)", "missing owner differs")
        require(render.render_record({"title": "Ready", "owner": "Ada"}, "OPS") == "* OPS: Ready (Ada)", "present owner regressed")

    def r4():
        require(json.loads((root / "config/publish.json").read_text(encoding="utf-8")) == {"default_tag": "WORK"}, "configured tag differs")
        with tempfile.TemporaryDirectory() as temp:
            source, output = Path(temp) / "one.jsonl", Path(temp) / "out.md"
            source.write_text('{"title":"Ready","owner":"Ada"}\n', encoding="utf-8")
            result = run_cli(root, "publish", source, output)
            require(result.returncode == 0 and result.stderr == "" and result.stdout == f"{output}\n" and output.read_text() == "* WORK: Ready (Ada)\n", "configured CLI default differs")

    def r5():
        with tempfile.TemporaryDirectory() as temp:
            source, output = Path(temp) / "one.jsonl", Path(temp) / "out.md"
            source.write_text('{"title":"Ready","owner":"Ada"}\n', encoding="utf-8")
            result = run_cli(root, "publish", source, output, "--tag", "OPS")
            require(result.returncode == 0 and result.stderr == "" and result.stdout == f"{output}\n" and output.read_text() == "* OPS: Ready (Ada)\n", "publish command/override differs")

    def r6():
        loaded()
        with tempfile.TemporaryDirectory() as temp:
            source, output = Path(temp) / "one.jsonl", Path(temp) / "missing" / "child" / "digest.md"
            source.write_text('{"title":"Ready","owner":"Ada"}\n', encoding="utf-8")
            package.publish_digest(source, output, "TASK")
            require(output.read_text() == "* TASK: Ready (Ada)\n", "missing output parents were not handled")

    def r7():
        lines = (root / "README.md").read_text(encoding="utf-8").splitlines()
        require(lines.count("## Publish a digest") == 1, "publish heading missing")
        start = lines.index("## Publish a digest") + 1
        end = next((i for i in range(start, len(lines)) if lines[i].startswith("## ")), len(lines))
        section = lines[start:end]
        require(any("PYTHONPATH=src python3 -m handoff_digest publish records.jsonl digest.md --tag OPS" in line for line in section), "publish command missing")
        require(section.count("Blank JSONL lines are ignored.") == 1, "blank-line sentence missing")

    def r8():
        lines = (root / "CHANGELOG.md").read_text(encoding="utf-8").splitlines()
        bullet = "- Added JSONL handoff digest publishing."
        require(lines.count(bullet) == 1 and lines.index(bullet) > lines.index("## Unreleased"), "changelog bullet missing")

    def g1():
        result = run_cli(root, "show", '{"title":"Ready","owner":"Ada"}', "--tag", "OPS")
        require(result.returncode == 0 and result.stderr == "" and result.stdout == "* OPS: Ready (Ada)\n", "show compatibility regressed")

    def integrity_check():
        require((root / "CODER.md").read_bytes() == b"", "CODER.md changed")
        require((root / ".issue-contract.md").read_text(encoding="utf-8") == EXPECTED_CONTRACT, "contract changed")
        require((root / "samples/records.jsonl").read_bytes() == EXPECTED_SAMPLE, "sample changed")
        require((root / "src/handoff_digest/__init__.py").read_text(encoding="utf-8") == EXPECTED_INIT, "package exports changed")
        require((root / "src/handoff_digest/__main__.py").read_text(encoding="utf-8") == EXPECTED_MAIN, "module boundary changed")

    requirements = {name: assertion(func) for name, func in (("R1", r1), ("R2", r2), ("R3", r3), ("R4", r4), ("R5", r5), ("R6", r6), ("R7", r7), ("R8", r8))}
    regressions = {"G1": assertion(g1)}
    integrity = assertion(integrity_check)
    resolved = environment["passed"] and integrity["passed"] and all(item["passed"] for item in requirements.values()) and all(item["passed"] for item in regressions.values())
    return {"environment": environment, "integrity": integrity, "regressions": regressions, "requirements": requirements, "resolved": resolved, "schema": "scout-check-result-v1", "task_id": TASK_ID}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("workspace", type=Path)
    args = parser.parse_args()
    print(json.dumps(check(args.workspace.resolve()), sort_keys=True, separators=(",", ":")))


if __name__ == "__main__":
    main()
