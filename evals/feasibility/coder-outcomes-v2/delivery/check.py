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
TASKS = ("delivery-dispatch-manifest", "delivery-retire-legacy-quote")
WORKER = r'''
import copy, importlib.util, json, sys

def capture(call):
    try:
        return {"value": call()}
    except BaseException as exc:
        return {"error": type(exc).__name__}

def load(path):
    spec = importlib.util.spec_from_file_location("delivery_subject", path)
    if spec is None or spec.loader is None:
        raise RuntimeError("subject loader unavailable")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

try:
    module = load(sys.argv[1])
    task = sys.argv[2]
    def common():
        records = module.delivery_records()
        rates = module.zone_rates()
        cost = capture(lambda: module.shipping_cost(records[1], rates))
        missing = capture(lambda: module.shipping_cost({"delivery_id": "D-3", "zone": "north", "weight": 1}, {}))
        return {"records": records, "rates": rates, "cost": cost, "missing": missing}
    def integration():
        deliveries = [
            {"delivery_id": "D-2", "zone": "west", "weight": 2},
            {"delivery_id": "D-1", "zone": "east", "weight": 3},
        ]
        rates = {"east": 4, "west": 7}
        before_deliveries, before_rates = copy.deepcopy(deliveries), dict(rates)
        result = capture(lambda: module.dispatch_manifest(deliveries, rates))
        missing = capture(lambda: module.dispatch_manifest([{"delivery_id": "D-3", "zone": "north", "weight": 1}], rates))
        return {"result": result, "missing": missing, "before_deliveries": before_deliveries,
                "after_deliveries": deliveries, "before_rates": before_rates, "after_rates": rates}
    def refactor():
        return {"legacy_present": hasattr(module, "legacy_quote")}
    probe = integration if task == "delivery-dispatch-manifest" else refactor
    print(json.dumps({"facts": {"common": capture(common), "task": capture(probe)}}, sort_keys=True))
except BaseException as exc:
    print(json.dumps({"worker_error": type(exc).__name__}, sort_keys=True))
'''


def subject_facts(repo: Path, task: str) -> tuple[dict[str, object] | None, str | None]:
    command = [sys.executable, "-I", "-B", "-c", WORKER, str(repo / "delivery.py"), task]
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


def integration_acceptance(facts: dict[str, object]) -> bool:
    task = value(facts, "task")
    if not task:
        return False
    result, missing = task.get("result"), task.get("missing")
    expected = [
        {"delivery_id": "D-1", "zone": "east", "weight": 3, "rate": 4, "cost": 12},
        {"delivery_id": "D-2", "zone": "west", "weight": 2, "rate": 7, "cost": 14},
    ]
    return bool(
        isinstance(result, dict) and result.get("value") == expected
        and isinstance(missing, dict) and missing.get("error") == "KeyError"
        and task.get("before_deliveries") == task.get("after_deliveries")
        and task.get("before_rates") == task.get("after_rates")
    )


def refactor_acceptance(facts: dict[str, object]) -> bool:
    task = value(facts, "task")
    return bool(task and task.get("legacy_present") is False)


def regressions(facts: dict[str, object]) -> bool:
    common = value(facts, "common")
    if not common:
        return False
    expected_records = [
        {"delivery_id": "D-200", "zone": "west", "weight": 2},
        {"delivery_id": "D-100", "zone": "east", "weight": 3},
    ]
    cost, missing = common.get("cost"), common.get("missing")
    return bool(
        common.get("records") == expected_records
        and common.get("rates") == {"east": 4, "west": 3}
        and isinstance(cost, dict) and cost.get("value") == 12
        and isinstance(missing, dict) and missing.get("error") == "KeyError"
    )


def evaluate(repo: Path, task: str) -> dict[str, object]:
    try:
        facts, subject_error = subject_facts(repo, task)
        if facts is None:
            return {"task": task, "acceptance": False, "regressions": False,
                    "resolved": False, "subject_error": subject_error}
        acceptance = integration_acceptance(facts) if task == TASKS[0] else refactor_acceptance(facts)
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


def transform_integration(repo: Path, wrong: bool) -> None:
    correct = """\n\ndef dispatch_manifest(deliveries: list[dict[str, Any]], rates: dict[str, int]) -> list[dict[str, Any]]:\n    result = []\n    for delivery in deliveries:\n        rate = rates[delivery[\"zone\"]]\n        result.append({\"delivery_id\": delivery[\"delivery_id\"], \"zone\": delivery[\"zone\"], \"weight\": delivery[\"weight\"], \"rate\": rate, \"cost\": delivery[\"weight\"] * rate})\n    return sorted(result, key=lambda item: item[\"delivery_id\"])\n"""
    wrong_join = """\n\ndef dispatch_manifest(deliveries: list[dict[str, Any]], rates: dict[str, int]) -> list[dict[str, Any]]:\n    return [{\"delivery_id\": item[\"delivery_id\"], \"zone\": item[\"zone\"], \"weight\": item[\"weight\"], \"rate\": 1, \"cost\": item[\"weight\"]} for item in sorted(deliveries, key=lambda item: item[\"delivery_id\"])]\n"""
    path = repo / "delivery.py"
    path.write_text(path.read_text(encoding="utf-8") + (wrong_join if wrong else correct), encoding="utf-8")


def transform_refactor(repo: Path, wrong: bool) -> None:
    legacy = """\n\ndef legacy_quote(delivery: dict[str, Any], rates: dict[str, int]) -> int:\n    return shipping_cost(delivery, rates)\n"""
    path = repo / "delivery.py"
    replace_once(path, legacy, "")
    if wrong:
        supported = """def shipping_cost(delivery: dict[str, Any], rates: dict[str, int]) -> int:\n    return delivery[\"weight\"] * rates[delivery[\"zone\"]]\n"""
        broken = """def shipping_cost(delivery: dict[str, Any], rates: dict[str, int]) -> int:\n    return delivery[\"weight\"]\n"""
        replace_once(path, supported, broken)


TRANSFORMS: dict[str, Callable[[Path, bool], None]] = {TASKS[0]: transform_integration, TASKS[1]: transform_refactor}


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
