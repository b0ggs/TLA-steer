#!/usr/bin/env python3
import hashlib
import json
import secrets
import subprocess
import sys
from pathlib import Path

TASKS = {"add-execution-waves", "refactor-context-merge"}
PUBLIC_SHA = "cc85c2c19a777f710e7a0b56ae3aea14baab15d2d4a40017ff3847856a74656b"
TASKS_SHA = "00c68aa9e44a5af571fce8daa954d187a282dc3950f7fefda758cb4e52bf7ee1"
SELF_SHA = "57aae0aa541d825d4ae32a584de87820eddcfc9f043eff8490e4aa9d3f6a0961"
HERE = Path(__file__).resolve().parent

LOAD = r'''import importlib.util, pathlib, sys
root = pathlib.Path(sys.argv[1])
sys.path.insert(0, str(root))
spec = importlib.util.spec_from_file_location("workflow", root / "workflow.py")
workflow = importlib.util.module_from_spec(spec)
sys.modules["workflow"] = workflow
spec.loader.exec_module(workflow)
'''
PUBLIC = LOAD + r'''import types, unittest
tests = types.ModuleType("test_public")
exec(compile(%r, "test_public.py", "exec"), tests.__dict__)
suite = unittest.defaultTestLoader.loadTestsFromModule(tests)
result = unittest.TextTestRunner(stream=open(__import__("os").devnull, "w")).run(suite)
assert result.wasSuccessful()
'''
HIDDEN = {
 "add-execution-waves": LOAD + r'''import copy
steps = [{"id":"deploy","needs":["test","audit"]},{"id":"fetch","needs":[]},{"id":"audit","needs":["fetch"]},{"id":"build","needs":["fetch"]},{"id":"test","needs":["build"]},{"id":"notify","needs":["deploy"]}]
before = copy.deepcopy(steps)
assert workflow.execution_waves(steps) == [["fetch"],["audit","build"],["test"],["deploy"],["notify"]]
assert steps == before
stream = ({"id":i,"needs":n} for i,n in [("a",[]),("b",[]),("c",["a"]),("d",["a","b"])])
assert workflow.execution_waves(stream) == [["a","b"],["c","d"]]
assert workflow.execution_waves([]) == []
for bad in ([{"id":"a","needs":["missing"]}], [{"id":"a","needs":["b"]},{"id":"b","needs":["a"]}]):
 try: workflow.execution_waves(bad)
 except ValueError: pass
 else: raise AssertionError("invalid dependencies accepted")
''',
 "refactor-context-merge": LOAD + r'''import copy
base = {"job":{"retries":2,"labels":["base"],"auth":{"user":"ada","token":"old"}},"flags":["a"],"keep":1}
overlay = {"job":{"auth":{"token":"new"},"timeout":5},"flags":["b"]}
before = copy.deepcopy((base, overlay))
result = workflow.merge_context(base, overlay)
assert result == {"job":{"retries":2,"labels":["base"],"auth":{"user":"ada","token":"new"},"timeout":5},"flags":["b"],"keep":1}
assert (base, overlay) == before
result["job"]["labels"].append("changed"); result["flags"].append("changed"); result["job"]["auth"]["token"] = "changed"
assert (base, overlay) == before
assert workflow.merge_context({"x":{"a":1},"y":1},{"x":2,"y":{"b":2}}) == {"x":2,"y":{"b":2}}
'''
}


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def integrity(root):
    own = Path(__file__).read_bytes()
    normalized = own.replace(SELF_SHA.encode(), b"0" * 64, 1)
    if digest(HERE / "tasks.json") != TASKS_SHA or hashlib.sha256(normalized).hexdigest() != SELF_SHA:
        return False
    public, subject = root / "test_public.py", root / "workflow.py"
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
