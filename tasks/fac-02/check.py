#!/usr/bin/env python3
"""Checker for the inimerge bug-fix task (FAC02).

Usage: python check.py /path/to/workspace

The checker runs outside the workspace: every subprocess uses a private
temporary directory as its cwd, PYTHONDONTWRITEBYTECODE=1 is set, and
nothing is ever written into the scanned tree.  Exactly one subprocess is
spawned per scored key.  All comparisons are semantic (parsed JSON or
splitlines), never whole-output byte equality.

Every literal asserted below is stated verbatim in the workspace's public
files:
  R1  -> .issue-contract.md (FAC02-1)
  R2  -> CHANGELOG.md (FAC02-2)
  R3  -> CHANGELOG.md (FAC02-3)
  R4  -> docs/merging.md (FAC02-4)
  R5  -> docs/merging.md (FAC02-5)
  R6  -> docs/merging.md (FAC02-6)
  R7  -> tests/test_merger.py (FAC02-7)
  R8  -> docs/merging.md (FAC02-8)
  R9  -> README.md (FAC02-9)
  R10 -> docs/merging.md (FAC02-10)
  G1, G2 -> docs/merging.md ("Guarantees")

Output: canonical JSON
  {"requirements": {"R1": bool, ...}, "regressions": {"G1": bool, "G2": bool},
   "resolved": bool}
"""

import json
import os
import subprocess
import sys
import tempfile

TIMEOUT = 60


def run(cmd, workspace, cwd):
    """Run one subprocess with the workspace importable via PYTHONPATH."""
    env = dict(os.environ)
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    env["PYTHONPATH"] = workspace
    try:
        return subprocess.run(
            cmd,
            cwd=cwd,
            env=env,
            capture_output=True,
            text=True,
            timeout=TIMEOUT,
        )
    except (subprocess.TimeoutExpired, OSError):
        return None


def run_code(code, workspace, cwd, args=()):
    return run([sys.executable, "-c", code] + list(args), workspace, cwd)


def last_json(proc):
    """Parse the last non-empty stdout line of a successful subprocess."""
    if proc is None or proc.returncode != 0:
        return None
    for line in reversed(proc.stdout.strip().splitlines()):
        line = line.strip()
        if line:
            try:
                return json.loads(line)
            except ValueError:
                return None
    return None


# --- per-requirement subprocess payloads -----------------------------------

CODE_R1 = """
import json
from inimerge.merger import merge
print(json.dumps(merge({"s": {"k": "a", "only": "x"}}, {"s": {"k": "b"}})))
"""

CODE_R2 = """
import json, sys
try:
    with open(sys.argv[1], encoding="utf-8") as handle:
        lines = handle.read().splitlines()
except OSError:
    lines = []
ok = False
in_section = False
for line in lines:
    if line.startswith("## "):
        in_section = line.startswith("## 1.2.1")
        continue
    if in_section and line.strip() == (
        "- Fixed: override layers now take precedence over base layers."
    ):
        ok = True
        break
print(json.dumps({"ok": ok}))
"""

CODE_R3 = """
import json
import inimerge
print(json.dumps({"version": inimerge.__version__}))
"""

CODE_R4 = """
import json
from inimerge.merger import merge
doc = merge.__doc__ or ""
print(json.dumps({"ok": "Later layers take precedence over earlier layers." in doc}))
"""

CODE_R5 = """
import json
from inimerge.writer import dumps
print(json.dumps({"lines": dumps({"s": {"a": "1"}}).splitlines()}))
"""

CODE_R6 = """
import json
from inimerge.parser import parse
print(json.dumps(parse("[s]\\nkey =\\n")))
"""

CODE_R8 = """
import json
from inimerge.parser import parse
from inimerge.errors import ParseError
try:
    parse("[s]\\nvalid = 1\\nbogus line\\n")
    print(json.dumps({"msg": None}))
except ParseError as exc:
    print(json.dumps({"msg": str(exc)}))
"""

CODE_R10 = """
import json
from inimerge.writer import dumps
lines = dumps({"s": {"b": "2", "a": "1"}}).splitlines()
keys = [line.split("=")[0].strip() for line in lines[1:] if "=" in line]
print(json.dumps({"keys": keys}))
"""

CODE_G1 = """
import json
from inimerge.parser import parse
print(json.dumps(parse("[db]\\nhost = localhost\\nport = 5432\\n")))
"""

CODE_G2 = """
import json
from inimerge.merger import merge
print(json.dumps(merge({"a": {"x": "1"}, "b": {"y": "2"}}, {"a": {"z": "3"}})))
"""


def main():
    if len(sys.argv) != 2 or not os.path.isdir(sys.argv[1]):
        print(json.dumps({"error": "usage: check.py WORKSPACE_DIR"}))
        return 2
    workspace = os.path.abspath(sys.argv[1])

    requirements = {}
    regressions = {}

    with tempfile.TemporaryDirectory(prefix="fac02-check-") as tmp:
        # R1 (FAC02-1): override values win for keys present in both inputs.
        requirements["R1"] = last_json(run_code(CODE_R1, workspace, tmp)) == {
            "s": {"k": "b", "only": "x"}
        }

        # R2 (FAC02-2): changelog bullet inside the "## 1.2.1" section.
        requirements["R2"] = last_json(
            run_code(
                CODE_R2, workspace, tmp,
                args=[os.path.join(workspace, "CHANGELOG.md")],
            )
        ) == {"ok": True}

        # R3 (FAC02-3): version bump.
        requirements["R3"] = last_json(run_code(CODE_R3, workspace, tmp)) == {
            "version": "1.2.1"
        }

        # R4 (FAC02-4): docstring sentence in merge().
        requirements["R4"] = last_json(run_code(CODE_R4, workspace, tmp)) == {
            "ok": True
        }

        # R5 (FAC02-5): default delimiter renders entries as "key = value".
        requirements["R5"] = last_json(run_code(CODE_R5, workspace, tmp)) == {
            "lines": ["[s]", "a = 1"]
        }

        # R6 (FAC02-6): "key =" parses to the empty string.
        requirements["R6"] = last_json(run_code(CODE_R6, workspace, tmp)) == {
            "s": {"key": ""}
        }

        # R7 (FAC02-7): named test method exists and passes.
        proc = run(
            [
                sys.executable,
                "-m",
                "unittest",
                "tests.test_merger.MergerTests.test_override_precedence",
            ],
            workspace,
            tmp,
        )
        requirements["R7"] = proc is not None and proc.returncode == 0

        # R8 (FAC02-8): exact ParseError message wording.
        requirements["R8"] = last_json(run_code(CODE_R8, workspace, tmp)) == {
            "msg": "line 3: expected 'key = value' or '[section]'"
        }

        # R9 (FAC02-9): CLI exits with status 2 on a parse failure.
        bad_path = os.path.join(tmp, "bad.ini")
        with open(bad_path, "w", encoding="utf-8") as handle:
            handle.write("bogus line\n")
        proc = run(
            [sys.executable, "-m", "inimerge.cli", bad_path], workspace, tmp
        )
        requirements["R9"] = proc is not None and proc.returncode == 2

        # R10 (FAC02-10): keys emitted in ascending alphabetical order.
        requirements["R10"] = last_json(run_code(CODE_R10, workspace, tmp)) == {
            "keys": ["a", "b"]
        }

        # G1: documented parse guarantee keeps working.
        regressions["G1"] = last_json(run_code(CODE_G1, workspace, tmp)) == {
            "db": {"host": "localhost", "port": "5432"}
        }

        # G2: base-only keys and sections survive a merge.
        regressions["G2"] = last_json(run_code(CODE_G2, workspace, tmp)) == {
            "a": {"x": "1", "z": "3"},
            "b": {"y": "2"},
        }

    resolved = all(requirements.values()) and all(regressions.values())
    print(
        json.dumps(
            {
                "requirements": requirements,
                "regressions": regressions,
                "resolved": resolved,
            }
        )
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
