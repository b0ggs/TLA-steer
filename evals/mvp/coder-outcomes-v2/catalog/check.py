#!/usr/bin/env python3
import hashlib
import json
import secrets
import subprocess
import sys
from pathlib import Path

TASKS = {"integrate-warehouse-availability", "refactor-lazy-pagination"}
PUBLIC_SHA = "709184b76da001751a9f15b4b9ba3426a47656c41540d285e645df6b716a2f2b"
TASKS_SHA = "47bf5cd0a534cc914fd4844df95aebacff7a1deb6bdb58e8c1823a95b5dc2678"
SELF_SHA = "e4f5d7c2a17fa0266f8defff615b197f45a16dc7422e5e19910f4ecd61e7d049"
HERE = Path(__file__).resolve().parent

LOAD = r'''import importlib.util, pathlib, sys
root = pathlib.Path(sys.argv[1])
sys.path.insert(0, str(root))
spec = importlib.util.spec_from_file_location("catalog", root / "catalog.py")
catalog = importlib.util.module_from_spec(spec)
sys.modules["catalog"] = catalog
spec.loader.exec_module(catalog)
'''
PUBLIC = LOAD + r'''import types, unittest
tests = types.ModuleType("test_public")
exec(compile(%r, "test_public.py", "exec"), tests.__dict__)
suite = unittest.defaultTestLoader.loadTestsFromModule(tests)
result = unittest.TextTestRunner(stream=open(__import__("os").devnull, "w")).run(suite)
assert result.wasSuccessful()
'''
HIDDEN = {
 "integrate-warehouse-availability": LOAD + r'''import copy
products = [{"sku":"AB-12","name":"Pen"},{"sku":"zx 9","name":"Pad"},{"sku":"NONE","name":"Clip"}]
rows = [{"sku":"ab 12","location":"east","quantity":"3"},{"sku":"other","location":"x","quantity":99},{"sku":"ZX-9","location":"east","quantity":0},{"sku":"AB12","location":"west","quantity":2}]
before = copy.deepcopy((products, rows))
assert catalog.availability_report(products, rows) == [{"sku":"AB-12","name":"Pen","available":5},{"sku":"zx 9","name":"Pad","available":0},{"sku":"NONE","name":"Clip","available":0}]
assert (products, rows) == before
p = ({"sku":sku,"name":name} for sku,name in [("C-1","Cup"),("D2","Dish")])
r = ({"sku":sku,"quantity":qty} for sku,qty in [("d-2","4"),("c1",1),("C 1","2")])
assert catalog.availability_report(p, r) == [{"sku":"C-1","name":"Cup","available":3},{"sku":"D2","name":"Dish","available":4}]
''',
 "refactor-lazy-pagination": LOAD + r'''class Probe:
 def __init__(self): self.value = 0; self.consumed = 0
 def __iter__(self): return self
 def __next__(self):
  if self.value == 5: raise StopIteration
  value = self.value; self.value += 1; self.consumed += 1; return value
probe = Probe()
result = catalog.pages(probe, 2)
assert iter(result) is result and probe.consumed == 0
assert next(result) == [0, 1] and probe.consumed == 2
assert next(result) == [2, 3] and probe.consumed == 4
assert next(result) == [4] and probe.consumed == 5
try: next(result)
except StopIteration: pass
else: raise AssertionError("iterator did not stop")
assert list(catalog.pages((x for x in "abc"), 5)) == [["a","b","c"]]
try: catalog.pages(iter([1]), 0)
except ValueError: pass
else: raise AssertionError("validation was deferred")
'''
}


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def integrity(root):
    own = Path(__file__).read_bytes()
    normalized = own.replace(SELF_SHA.encode(), b"0" * 64, 1)
    if digest(HERE / "tasks.json") != TASKS_SHA or hashlib.sha256(normalized).hexdigest() != SELF_SHA:
        return False
    public, subject = root / "test_public.py", root / "catalog.py"
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
