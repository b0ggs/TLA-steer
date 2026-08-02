#!/usr/bin/env python3
import hashlib
import json
import secrets
import subprocess
import sys
from pathlib import Path

TASKS = {"compare-scheduled-instants", "integrate-event-deliveries"}
PUBLIC_SHA = "f5936a682b0ac4b0b476b788da42698d5cae8ecec450a6e1a45f72193960f0bf"
TASKS_SHA = "5cd4dae640ba5023d4433340db923bc25c0098c5c5169814b0b5c291fd67d6cd"
SELF_SHA = "71a85ee2453ec575af181505e25e9152721c1b01c533b35496c113360c46eb5e"
HERE = Path(__file__).resolve().parent

LOAD = r'''import importlib.util, pathlib, sys
root = pathlib.Path(sys.argv[1])
sys.path.insert(0, str(root))
spec = importlib.util.spec_from_file_location("notifier", root / "notifier.py")
notifier = importlib.util.module_from_spec(spec)
sys.modules["notifier"] = notifier
spec.loader.exec_module(notifier)
'''
PUBLIC = LOAD + r'''import types, unittest
tests = types.ModuleType("test_public")
exec(compile(%r, "test_public.py", "exec"), tests.__dict__)
suite = unittest.defaultTestLoader.loadTestsFromModule(tests)
result = unittest.TextTestRunner(stream=open(__import__("os").devnull, "w")).run(suite)
assert result.wasSuccessful()
'''
HIDDEN = {
 "compare-scheduled-instants": LOAD + r'''import copy
records = [
 {"id":"east","scheduled_at":"2024-01-01T13:00:00+02:00"},
 {"id":"west","scheduled_at":"2024-01-01T07:30:00-05:00"},
 {"id":"boundary","scheduled_at":"2024-01-01T12:00:00Z"},
 {"id":"past","scheduled_at":"2023-12-31T23:59:00+00:00"},
]
before = copy.deepcopy(records)
assert notifier.due_notification_ids(records, "2024-01-01T12:00:00+00:00") == ["east","boundary","past"]
assert records == before
assert notifier.due_notification_ids([{"id":"same","scheduled_at":"2024-06-01T10:00:00Z"},{"id":"future","scheduled_at":"2024-06-01T10:00:01Z"}], "2024-06-01T12:00:00+02:00") == ["same"]
''',
 "integrate-event-deliveries": LOAD + r'''import copy
event = {"type":"invoice.paid","data":{"customer":"Ada","total":"12.00"}}
subscriptions = [
 {"event":"invoice.paid","channel":"email","destination":"team","enabled":True},
 {"event":"invoice.sent","channel":"sms","destination":"skip","enabled":True},
 {"event":"invoice.paid","channel":"sms","destination":"team","enabled":True},
 {"event":"invoice.paid","channel":"email","destination":"team","enabled":True},
 {"event":"invoice.paid","channel":"push","destination":"off","enabled":False},
]
templates = {"invoice.paid:email":"Paid {total} for {customer}","invoice.paid:sms":"{customer} paid {total}","invoice.paid:push":"done"}
before = copy.deepcopy((event, subscriptions, templates))
assert notifier.build_deliveries(event, subscriptions, templates) == [{"channel":"email","destination":"team","body":"Paid 12.00 for Ada"},{"channel":"sms","destination":"team","body":"Ada paid 12.00"}]
assert (event, subscriptions, templates) == before
stream = ({"event":"ready","channel":channel,"destination":destination,"enabled":enabled} for channel,destination,enabled in [("email","a",False),("email","b",True),("sms","c",True)])
assert notifier.build_deliveries({"type":"ready","data":{"n":2}}, stream, {"ready:email":"E{n}"}) == [{"channel":"email","destination":"b","body":"E2"}]
'''
}


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def integrity(root):
    own = Path(__file__).read_bytes()
    normalized = own.replace(SELF_SHA.encode(), b"0" * 64, 1)
    if digest(HERE / "tasks.json") != TASKS_SHA or hashlib.sha256(normalized).hexdigest() != SELF_SHA:
        return False
    public, subject = root / "test_public.py", root / "notifier.py"
    if not public.is_file() or public.is_symlink() or digest(public) != PUBLIC_SHA:
        return False
    if not subject.is_file() or subject.is_symlink():
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
