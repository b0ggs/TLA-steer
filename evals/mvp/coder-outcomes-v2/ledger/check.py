#!/usr/bin/env python3
import hashlib
import json
import re
import secrets
import subprocess
import sys
from pathlib import Path

TASKS = {"deduplicate-running-balances", "add-period-summary"}
PUBLIC_SHA = "b6a823c24c590ce74d3ae4edd603de46d4cc9def0506effee47084ba3be8db39"
TASKS_SHA = "6a36c58371bf13abc37f990c3f85ee7b2d26e8a9ec0704ac899f6977fdaeb0fa"
SELF_SHA = "b19113bbad03396b2d3582eacd8c2325827cee0d307e121a920c93d8465c8f2b"
HERE = Path(__file__).resolve().parent

LOAD = r'''import importlib.util, pathlib, sys
root = pathlib.Path(sys.argv[1])
sys.path.insert(0, str(root))
spec = importlib.util.spec_from_file_location("ledger", root / "ledger.py")
ledger = importlib.util.module_from_spec(spec)
sys.modules["ledger"] = ledger
spec.loader.exec_module(ledger)
'''
PUBLIC = LOAD + r'''import types, unittest
tests = types.ModuleType("test_public")
exec(compile(%r, "test_public.py", "exec"), tests.__dict__)
suite = unittest.defaultTestLoader.loadTestsFromModule(tests)
result = unittest.TextTestRunner(stream=open(__import__("os").devnull, "w")).run(suite)
assert result.wasSuccessful()
'''
HIDDEN = {
    "deduplicate-running-balances": LOAD + r'''import copy
cases = [
 ("10.00", [{"id":"a","kind":"credit","amount":"2.50"},{"id":"b","kind":"debit","amount":"1.00"},{"id":"a","kind":"credit","amount":"99.00"}], ["12.50","11.50","11.50"]),
 ("0.00", [{"id":"x","kind":"debit","amount":"3.25"},{"id":"y","kind":"credit","amount":"1.10"},{"id":"z","kind":"credit","amount":"5.00"},{"id":"x","kind":"debit","amount":"3.25"}], ["-3.25","-2.15","2.85","2.85"]),
 ("1.00", [{"id":"q","kind":"credit","amount":"1.00"},{"id":"Q","kind":"credit","amount":"2.00"},{"id":"q","kind":"debit","amount":"9.00"}], ["2.00","4.00","4.00"]),
]
for opening, entries, expected in cases:
    before = copy.deepcopy(entries)
    assert ledger.running_balances(opening, entries) == expected
    assert entries == before
''',
    "add-period-summary": LOAD + r'''import copy
entries = [
 {"date":"2024-02-01","kind":"credit","amount":"20.00"},
 {"date":"2024-03-01","kind":"credit","amount":"500.00"},
 {"date":"2024-01-01","kind":"debit","amount":"10.00"},
 {"date":"2024-02-29","kind":"debit","amount":"5.00"},
 {"date":"2024-01-31","kind":"credit","amount":"0.25"},
 {"date":"2024-02-10","kind":"debit","amount":"2.25"},
]
before = copy.deepcopy(entries)
assert ledger.period_summary("100.00", entries, "2024-02-01", "2024-02-29") == {"opening":"90.25","credits":"20.00","debits":"7.25","closing":"103.00"}
assert entries == before
assert ledger.period_summary("3.00", [{"date":"2020-01-01","kind":"credit","amount":"2.00"},{"date":"2022-01-01","kind":"debit","amount":"9.00"}], "2021-01-01", "2021-12-31") == {"opening":"5.00","credits":"0.00","debits":"0.00","closing":"5.00"}
try:
    ledger.period_summary("0.00", [], "2024-02-02", "2024-02-01")
except ValueError:
    pass
else:
    raise AssertionError("reversed period accepted")
'''
}


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def integrity(root):
    own = Path(__file__).read_bytes()
    normalized = own.replace(SELF_SHA.encode(), b"0" * 64, 1)
    if digest(HERE / "tasks.json") != TASKS_SHA or hashlib.sha256(normalized).hexdigest() != SELF_SHA:
        return False
    public = root / "test_public.py"
    ledger = root / "ledger.py"
    if not public.is_file() or public.is_symlink() or digest(public) != PUBLIC_SHA:
        return False
    if not ledger.is_file() or ledger.is_symlink():
        return False
    blocked = {"check.py", "tasks.json", "sitecustomize.py", "usercustomize.py"}
    return not any(path.name in blocked for path in root.rglob("*"))


def run(code, root):
    token = secrets.token_hex(24)
    wrapped = code + "\nprint(" + repr(token) + ")\n"
    try:
        proc = subprocess.run([sys.executable, "-I", "-B", "-c", wrapped, str(root)],
                              cwd=root, text=True, capture_output=True, timeout=15)
    except subprocess.TimeoutExpired:
        return "TIMEOUT"
    return "PASS" if proc.returncode == 0 and proc.stdout == token + "\n" else "FAIL"


def emit(ok, task, code, exit_code):
    print(json.dumps({"code": code, "ok": ok, "task": task}, sort_keys=True,
                     separators=(",", ":")))
    return exit_code


def main(argv):
    if len(argv) != 3 or argv[1] not in TASKS:
        return emit(False, argv[1] if len(argv) > 1 else None, "INVALID_INVOCATION", 2)
    task, root = argv[1], Path(argv[2]).resolve()
    if not root.is_dir() or not integrity(root):
        return emit(False, task, "INTEGRITY_FAILURE", 3)
    public_source = (root / "test_public.py").read_bytes()
    if hashlib.sha256(public_source).hexdigest() != PUBLIC_SHA:
        return emit(False, task, "INTEGRITY_FAILURE", 3)
    public_result = run(PUBLIC % public_source, root)
    if public_result == "TIMEOUT":
        return emit(False, task, "SUBJECT_TIMEOUT", 1)
    if public_result != "PASS":
        return emit(False, task, "PUBLIC_REGRESSION_FAILURE", 1)
    hidden_result = run(HIDDEN[task], root)
    if hidden_result == "TIMEOUT":
        return emit(False, task, "SUBJECT_TIMEOUT", 1)
    if hidden_result != "PASS":
        return emit(False, task, "HIDDEN_ACCEPTANCE_FAILURE", 1)
    if not integrity(root):
        return emit(False, task, "INTEGRITY_FAILURE", 3)
    return emit(True, task, "PASS", 0)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
