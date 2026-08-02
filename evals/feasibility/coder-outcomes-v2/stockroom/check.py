from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Callable


ROOT = Path(__file__).resolve().parent
FIXTURE = ROOT / "fixture"
TASKS = (
    "stockroom-failed-reservation-atomic",
    "stockroom-low-stock-query",
)
WORKER = r'''
import importlib.util, json, sys

def capture(call):
    try:
        return {"value": call()}
    except BaseException as exc:
        return {"error": type(exc).__name__}

def load(path):
    spec = importlib.util.spec_from_file_location("stockroom_subject", path)
    if spec is None or spec.loader is None:
        raise RuntimeError("subject loader unavailable")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

try:
    module = load(sys.argv[1])
    task = sys.argv[2]
    def common():
        room = module.Stockroom({"bolt": 5})
        lookup = room.available("missing")
        reserved = room.reserve("bolt", 2)
        remaining = room.available("bolt")
        invalid = capture(lambda: room.reserve("bolt", 0))
        return {"lookup": lookup, "reserved": reserved, "remaining": remaining, "invalid": invalid}
    def bug():
        room = module.Stockroom({"bolt": 3, "nut": 8})
        before = room.snapshot()
        result = room.reserve("bolt", 5)
        return {"before": before, "result": result, "after": room.snapshot()}
    def feature():
        room = module.Stockroom({"zinc": 2, "apple": 5, "bolt": 1})
        before = room.snapshot()
        result = capture(lambda: room.low_stock(2))
        negative = capture(lambda: room.low_stock(-1))
        return {"before": before, "result": result, "negative": negative, "after": room.snapshot()}
    probe = bug if task == "stockroom-failed-reservation-atomic" else feature
    print(json.dumps({"facts": {"common": capture(common), "task": capture(probe)}}, sort_keys=True))
except BaseException as exc:
    print(json.dumps({"worker_error": type(exc).__name__}, sort_keys=True))
'''


def subject_facts(repo: Path, task: str) -> tuple[dict[str, object] | None, str | None]:
    command = [sys.executable, "-I", "-B", "-c", WORKER, str(repo / "stockroom.py"), task]
    try:
        process = subprocess.run(
            command, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            text=True, timeout=3, check=False,
        )
    except subprocess.TimeoutExpired:
        return None, "SUBJECT_TIMEOUT"
    if process.returncode != 0:
        return None, "SUBJECT_WORKER_CRASH"
    try:
        payload = json.loads(process.stdout)
    except (TypeError, json.JSONDecodeError):
        return None, "MALFORMED_SUBJECT_OUTPUT"
    if not isinstance(payload, dict) or not isinstance(payload.get("facts"), dict):
        return None, str(payload.get("worker_error", "MALFORMED_SUBJECT_OUTPUT"))
    return payload["facts"], None


def value(facts: dict[str, object], key: str) -> dict[str, object] | None:
    item = facts.get(key)
    if not isinstance(item, dict) or not isinstance(item.get("value"), dict):
        return None
    return item["value"]


def bug_acceptance(facts: dict[str, object]) -> bool:
    task = value(facts, "task")
    return bool(task and task.get("result") is False and task.get("before") == task.get("after"))


def feature_acceptance(facts: dict[str, object]) -> bool:
    task = value(facts, "task")
    if not task:
        return False
    result = task.get("result")
    negative = task.get("negative")
    return bool(
        isinstance(result, dict)
        and result.get("value") == [["bolt", 1], ["zinc", 2]]
        and isinstance(negative, dict)
        and negative.get("error") == "ValueError"
        and task.get("before") == task.get("after")
    )


def regressions(facts: dict[str, object]) -> bool:
    common = value(facts, "common")
    if not common:
        return False
    invalid = common.get("invalid")
    return bool(
        common.get("lookup") == 0
        and common.get("reserved") is True
        and common.get("remaining") == 3
        and isinstance(invalid, dict)
        and invalid.get("error") == "ValueError"
    )


def evaluate(repo: Path, task: str) -> dict[str, object]:
    try:
        facts, subject_error = subject_facts(repo, task)
        if facts is None:
            return {"task": task, "acceptance": False, "regressions": False,
                    "resolved": False, "subject_error": subject_error}
        acceptance = bug_acceptance(facts) if task == TASKS[0] else feature_acceptance(facts)
        regression = regressions(facts)
        return {"task": task, "acceptance": acceptance, "regressions": regression,
                "resolved": acceptance and regression}
    except Exception as exc:
        return {"task": task, "acceptance": False, "regressions": False,
                "resolved": False, "evaluator_error": type(exc).__name__}


def replace_once(path: Path, old: str, new: str) -> None:
    source = path.read_text(encoding="utf-8")
    if source.count(old) != 1:
        raise AssertionError("authoring transformation anchor mismatch")
    path.write_text(source.replace(old, new), encoding="utf-8")


def transform_bug(repo: Path, wrong: bool) -> None:
    old = """        current = self._stock.get(sku, 0)\n        self._stock[sku] = max(0, current - quantity)\n        return current >= quantity\n"""
    correct = """        current = self._stock.get(sku, 0)\n        if current < quantity:\n            return False\n        self._stock[sku] = current - quantity\n        return True\n"""
    partial = """        current = self._stock.get(sku, 0)\n        if current < quantity:\n            self._stock[sku] = max(0, current - 1)\n            return False\n        self._stock[sku] = current - quantity\n        return True\n"""
    replace_once(repo / "stockroom.py", old, partial if wrong else correct)


def transform_feature(repo: Path, wrong: bool) -> None:
    correct = """\n    def low_stock(self, threshold: int) -> list[tuple[str, int]]:\n        if threshold < 0:\n            raise ValueError(\"threshold must be non-negative\")\n        return sorted((sku, quantity) for sku, quantity in self._stock.items() if quantity <= threshold)\n"""
    boundary_error = """\n    def low_stock(self, threshold: int) -> list[tuple[str, int]]:\n        return [(sku, quantity) for sku, quantity in self._stock.items() if quantity < threshold]\n"""
    path = repo / "stockroom.py"
    path.write_text(path.read_text(encoding="utf-8") + (boundary_error if wrong else correct), encoding="utf-8")


TRANSFORMS: dict[str, Callable[[Path, bool], None]] = {TASKS[0]: transform_bug, TASKS[1]: transform_feature}


def evaluate_copy(task: str, mode: str) -> dict[str, object]:
    with tempfile.TemporaryDirectory() as temporary:
        repo = Path(temporary) / "repo"
        shutil.copytree(FIXTURE, repo)
        if mode != "pristine":
            TRANSFORMS[task](repo, mode == "wrong")
        return evaluate(repo, task)


def self_test() -> int:
    summary: dict[str, object] = {}
    for task in TASKS:
        pristine, reference, wrong = (evaluate_copy(task, mode) for mode in ("pristine", "reference", "wrong"))
        if pristine["acceptance"] or not pristine["regressions"]:
            raise AssertionError(f"{task}: pristine inversion/regression gate failed")
        if not reference["resolved"] or wrong["resolved"]:
            raise AssertionError(f"{task}: reference/wrong gate failed")
        summary[task] = {"pristine": pristine, "reference": reference, "wrong": wrong}
    print(json.dumps(summary, sort_keys=True))
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--task", choices=TASKS)
    parser.add_argument("--repo", type=Path)
    args = parser.parse_args()
    if args.self_test:
        return self_test()
    if args.task is None or args.repo is None:
        parser.error("--task and --repo are required without --self-test")
    result = evaluate(args.repo, args.task)
    print(json.dumps(result, sort_keys=True))
    return 0 if result["resolved"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
