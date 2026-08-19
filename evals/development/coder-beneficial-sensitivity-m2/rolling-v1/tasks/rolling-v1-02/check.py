#!/usr/bin/env python3
"""Objective checker for rolling-v1-02."""

import argparse
import copy
import importlib
import io
import json
import os
import subprocess
import sys
from pathlib import Path
from unittest import mock

sys.dont_write_bytecode = True

TASK_ID = "rolling-v1-02"
EXPECTED_FILES = {
    ".issue-contract.md",
    "CODER.md",
    "README.md",
    "fixtures/corridor.json",
    "pyproject.toml",
    "tests/test_public.py",
    "triageboard/__init__.py",
    "triageboard/__main__.py",
    "triageboard/router.py",
}
EXPECTED_PROTECTED_SHA256 = {
    ".issue-contract.md": "a318e0b61042a51434ea9bc77470791a10f63a818133621d1b36564dced25cb6",
    "CODER.md": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    "README.md": "dad538758c020ee1444fe49c1aa4ad8e2ec64651cce80a6947120ee3d01be632",
    "fixtures/corridor.json": "3a2fdc6793c746d30f1217b4024a9940de9990baf22bc353f7b650b6b679a8d5",
    "pyproject.toml": "8f38c96733d64381fe8b615cc37c8c6267773ca12793254ac1bf564283b7fdc8",
    "tests/test_public.py": "fb282234d4f3421553533627db835e4423ea1e837c98684ca1c3a1bf70989338",
    "triageboard/__init__.py": "f211661d1a2554661d1b219074d59e915259f2d8891dd73e729ca5cb1aa49be5",
}


def assertion(function):
    try:
        function()
        return {"passed": True, "details": "objective assertion passed"}
    except Exception as exc:
        return {"passed": False, "details": f"{type(exc).__name__}: {exc}"}


def require(condition, message):
    if not condition:
        raise AssertionError(message)


def raises_value_error(function):
    try:
        function()
    except ValueError:
        return
    raise AssertionError("ValueError was not raised")


def load_modules(root):
    sys.path.insert(0, str(root))
    for name in tuple(sys.modules):
        if name == "triageboard" or name.startswith("triageboard."):
            sys.modules.pop(name, None)
    package = importlib.import_module("triageboard")
    router_module = importlib.import_module("triageboard.router")
    main_module = importlib.import_module("triageboard.__main__")
    return package, router_module, main_module


def cli(root, argv):
    completed = subprocess.run(
        [sys.executable, "-m", "triageboard", *argv],
        cwd=root,
        capture_output=True,
        text=True,
        encoding="utf-8",
        env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
        timeout=30,
        check=False,
    )
    return completed.returncode, completed.stdout, completed.stderr


def check(root):
    def environment_check():
        actual = set()
        for path in root.rglob("*"):
            if not path.is_file():
                continue
            relative = path.relative_to(root)
            if "__pycache__" in relative.parts or relative.parts[0] == ".git":
                continue
            actual.add(relative.as_posix())
        require(actual == EXPECTED_FILES, "public file inventory changed")

    environment = assertion(environment_check)
    try:
        package, router_module, main_module = load_modules(root)
        bundle = json.loads((root / "fixtures/corridor.json").read_text(encoding="utf-8"))
        load_error = None
    except Exception as exc:
        package = router_module = main_module = bundle = None
        load_error = exc

    def modules_present():
        if load_error is not None:
            raise load_error

    def r1():
        modules_present()
        ticket = {
            "id": " Keep-Case ",
            "product": "mobile",
            "severity": "normal",
            "tags": [" First ", "Second"],
        }
        ticket_before = copy.deepcopy(ticket)
        policy_before = copy.deepcopy(bundle["policy"])
        routed = router_module.route_ticket(ticket, bundle["policy"])
        require(type(routed) is dict and routed is not ticket, "route_ticket did not return a fresh dictionary")
        require(ticket == ticket_before, "route_ticket mutated the ticket")
        require(bundle["policy"] == policy_before, "route_ticket mutated the policy")
        tickets = [copy.deepcopy(ticket_before)]
        tickets_before = copy.deepcopy(tickets)
        first = router_module.route_tickets(tickets, bundle["policy"])
        second = router_module.route_tickets([], bundle["policy"])
        require(type(first) is list and first is not tickets and first[0] is not tickets[0], "batch results are not fresh")
        require(type(second) is list and second == [] and second is not first, "batch calls did not return fresh lists")
        require(tickets == tickets_before and bundle["policy"] == policy_before, "route_tickets mutated an input")

    def r2():
        modules_present()
        valid = {"id": "X", "product": "mobile", "severity": "normal", "tags": []}
        invalid = [
            None,
            {"id": "X", "product": "mobile", "severity": "normal"},
            {**valid, "extra": True},
            {**valid, "id": " "},
            {**valid, "product": 7},
            {**valid, "severity": " "},
            {**valid, "tags": "vip"},
            {**valid, "tags": [1]},
            {**valid, "severity": "urgent"},
        ]
        for ticket in invalid:
            raises_value_error(lambda ticket=ticket: router_module.route_ticket(ticket, bundle["policy"]))

    def r3():
        modules_present()
        corridor = router_module.route_ticket(bundle["tickets"][0], bundle["policy"])
        require((corridor["id"], corridor["product"]) == ("T-20", "mobile"), "corridor normalization differs")
        policy = copy.deepcopy(bundle["policy"])
        policy["aliases"]["phone"] = "ios"
        ticket = {"id": " Alias-1 ", "product": " PHONE ", "severity": "normal", "tags": []}
        chained = router_module.route_ticket(ticket, policy)
        require((chained["id"], chained["product"]) == ("Alias-1", "ios"), "alias lookup was not exactly one step")

    def r4():
        modules_present()
        queues = [
            router_module.route_ticket(ticket, bundle["policy"])["queue"]
            for ticket in bundle["tickets"]
        ]
        require(queues == ["apps", "accounts", "general"], "queue selection or fallback differs")

    def r5():
        modules_present()
        rows = [router_module.route_ticket(ticket, bundle["policy"]) for ticket in bundle["tickets"]]
        normal = router_module.route_ticket(
            {"id": "T-N", "product": "other", "severity": "normal", "tags": []},
            bundle["policy"],
        )
        observed = [(row["priority"], row["escalated"]) for row in rows] + [
            (normal["priority"], normal["escalated"])
        ]
        require(observed == [(1, True), (1, True), (3, False), (2, False)], "priority or escalation differs")

    def r6():
        modules_present()
        result = router_module.route_ticket(
            {"id": " Card-7 ", "product": "other", "severity": "normal", "tags": [" Beta ", "VIP", "beta", " "]},
            bundle["policy"],
        )
        require(set(result) == {"id", "product", "queue", "priority", "escalated", "tags"}, "projection keys differ")
        require(result["id"] == "Card-7" and result["tags"] == ["beta", "vip"], "id or tag cleanup differs")
        require(type(result["id"]) is str and type(result["product"]) is str, "text fields have wrong types")
        require(type(result["queue"]) is str and type(result["priority"]) is int, "queue or priority has wrong type")
        require(type(result["escalated"]) is bool and type(result["tags"]) is list, "escalation or tags has wrong type")
        require(all(type(tag) is str for tag in result["tags"]), "tag members have wrong type")

    def r7():
        modules_present()
        tickets = [
            {"id": "B", "product": "other", "severity": "low", "tags": []},
            {"id": "C", "product": "other", "severity": "normal", "tags": []},
            {"id": "A", "product": "other", "severity": "normal", "tags": []},
        ]
        before = copy.deepcopy(tickets)
        result = router_module.route_tickets(tickets, bundle["policy"])
        require([row["id"] for row in result] == ["A", "C", "B"], "batch order differs")
        require(tickets == before, "batch routing mutated tickets")
        raises_value_error(lambda: router_module.route_tickets(tuple(tickets), bundle["policy"]))

    def r8():
        modules_present()
        fixture = root / "fixtures/corridor.json"
        fixture_bundle = json.loads(fixture.read_text(encoding="utf-8"))
        expected_stdout = json.dumps(
            fixture_bundle["expected"], ensure_ascii=False, sort_keys=True, separators=(",", ":")
        ) + "\n"
        stdout = io.StringIO()
        stderr = io.StringIO()
        with (
            mock.patch.object(main_module, "route_tickets", return_value=fixture_bundle["expected"]) as routed,
            mock.patch.object(main_module.sys, "stdout", stdout),
            mock.patch.object(main_module.sys, "stderr", stderr),
        ):
            status = main_module.main([str(fixture)])
        require((status, stdout.getvalue(), stderr.getvalue()) == (0, expected_stdout, ""), "direct CLI success differs")
        require(routed.call_count == 1, "CLI did not route exactly once")
        args, kwargs = routed.call_args
        require(args == (fixture_bundle["tickets"], fixture_bundle["policy"]) and not kwargs, "CLI routed the wrong bundle values")
        status, actual_stdout, actual_stderr = cli(root, ["fixtures/corridor.json"])
        require(status == 0 and actual_stderr == "", "subprocess CLI success status or stderr differs")
        parsed = json.loads(actual_stdout)
        canonical = json.dumps(parsed, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n"
        require(actual_stdout == canonical, "subprocess CLI output is not canonical JSON plus newline")
        missing = cli(root, ["fixtures/does-not-exist.json"])
        require(missing[0] == 2 and missing[1] == "" and missing[2] != "", "CLI missing-file behavior differs")

    def g1():
        modules_present()
        require(package.__all__ == ["route_ticket", "route_tickets"], "protected top-level exports differ")
        require(package.route_ticket is router_module.route_ticket, "route_ticket export differs")
        require(package.route_tickets is router_module.route_tickets, "route_tickets export differs")

    def integrity_check():
        import hashlib

        for relative, expected in EXPECTED_PROTECTED_SHA256.items():
            actual = hashlib.sha256((root / relative).read_bytes()).hexdigest()
            require(actual == expected, f"protected path changed: {relative}")
        require((root / "CODER.md").read_bytes() == b"", "CODER.md is not zero-byte")

    requirements = {
        name: assertion(function)
        for name, function in (
            ("R1", r1),
            ("R2", r2),
            ("R3", r3),
            ("R4", r4),
            ("R5", r5),
            ("R6", r6),
            ("R7", r7),
            ("R8", r8),
        )
    }
    regressions = {"G1": assertion(g1)}
    integrity = assertion(integrity_check)
    resolved = (
        environment["passed"]
        and integrity["passed"]
        and all(item["passed"] for item in requirements.values())
        and all(item["passed"] for item in regressions.values())
    )
    return {
        "environment": environment,
        "integrity": integrity,
        "regressions": regressions,
        "requirements": requirements,
        "resolved": resolved,
        "schema": "scout-check-result-v1",
        "task_id": TASK_ID,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("workspace", type=Path)
    arguments = parser.parse_args()
    print(json.dumps(check(arguments.workspace.resolve()), ensure_ascii=False, sort_keys=True, separators=(",", ":")))


if __name__ == "__main__":
    main()
