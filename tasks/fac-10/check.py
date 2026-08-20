#!/usr/bin/env python3
"""Checker for the addrbook NANP-formatting task (factory task 10).

Usage: python3 check.py /path/to/workspace

Runs from outside the workspace, spawns one subprocess per requirement,
and writes nothing into the workspace (PYTHONDONTWRITEBYTECODE=1; all
subprocess cwds point at a throwaway temp directory).

Every literal asserted below is stated verbatim in the workspace's public
files (README.md, docs/normalization.md, CHANGELOG.md, tests/*.py,
.issue-contract.md).
"""

import json
import os
import shutil
import subprocess
import sys
import tempfile

SNIPPET_TIMEOUT = 120
SUITE_TIMEOUT = 300


def _env(workspace):
    env = dict(os.environ)
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    env["PYTHONPATH"] = workspace
    env["WS"] = workspace
    return env


def _run(workspace, argv, scratch, timeout):
    try:
        return subprocess.run(
            argv,
            cwd=scratch,
            env=_env(workspace),
            capture_output=True,
            text=True,
            timeout=timeout,
        )
    except (subprocess.TimeoutExpired, OSError):
        return None


def run_snippet(workspace, code, scratch, timeout=SNIPPET_TIMEOUT):
    proc = _run(workspace, [sys.executable, "-c", code], scratch, timeout)
    return proc is not None and proc.returncode == 0 and "PASS" in proc.stdout


# --- Requirement snippets -------------------------------------------------

# FAC10-1 (README.md): 10-digit inputs -> +1-XXX-XXX-XXXX.
R1 = '''
from addrbook.phones import normalize_phone
assert normalize_phone("(555) 123-4567") == "+1-555-123-4567"
assert normalize_phone("555.867.5309") == "+1-555-867-5309"
print("PASS")
'''

# FAC10-2 (README.md): 11-digit inputs with a leading 1.
R2 = '''
from addrbook.phones import normalize_phone
assert normalize_phone("1 (555) 010-9999") == "+1-555-010-9999"
print("PASS")
'''

# FAC10-3 (docs/normalization.md): normalize_record returns a new dict,
# leaves the input equal to its pre-call snapshot, and the returned
# record's "phones" list is independent of the input's "phones" list.
# Only shallow top-level independence plus a new "phones" list is tested.
R3 = '''
import copy
from addrbook.normalize import normalize_record
rec = {
    "name": "Ada  Lovelace",
    "email": " Ada@Example.COM ",
    "phones": ["(555) 123-4567"],
    "tags": ["friend"],
}
snapshot = copy.deepcopy(rec)
out = normalize_record(rec)
assert out is not rec
assert rec == snapshot
out["phones"].append("extra")
assert rec["phones"] == snapshot["phones"]
print("PASS")
'''

# FAC10-4 (CHANGELOG.md): "## 1.4.0" section with the exact bullet line,
# outside HTML comments (the note itself says comments are ignored).
R4 = '''
import os, re
path = os.path.join(os.environ["WS"], "CHANGELOG.md")
with open(path, encoding="utf-8") as fh:
    text = fh.read()
text = re.sub(r"<!--.*?-->", "", text, flags=re.S)
lines = [line.strip() for line in text.splitlines()]
assert "## 1.4.0" in lines
assert "- Canonical +1-XXX-XXX-XXXX formatting for NANP phone numbers." in lines
print("PASS")
'''

# FAC10-5 (README.md): version bump.
R5 = '''
import addrbook
assert addrbook.__version__ == "1.4.0"
print("PASS")
'''

# FAC10-6 (docs/normalization.md): config default.
R6 = '''
from addrbook import config
assert config.DEFAULTS["phone_style"] == "nanp-dashed"
print("PASS")
'''

# FAC10-7 (docs/normalization.md): exact docstring sentence.
R7 = '''
from addrbook.phones import normalize_phone
sentence = "Returns NANP numbers in +1-XXX-XXX-XXXX form."
assert sentence in (normalize_phone.__doc__ or "")
print("PASS")
'''

# FAC10-8 (docs/normalization.md): exact strict-mode error message.
R8 = '''
from addrbook.dedupe import dedupe
from addrbook.errors import DuplicateKeyError
records = [{"email": "ada@example.com"}, {"email": "ada@example.com"}]
try:
    dedupe(records, key="email", strict=True)
except DuplicateKeyError as exc:
    assert str(exc) == "duplicate contact key: ada@example.com"
    print("PASS")
'''

# FAC10-9 (tests/test_normalize.py): whitespace boundary in clean_name.
R9 = '''
from addrbook.normalize import clean_name
assert clean_name("\\t Ada \\t Lovelace \\n") == "Ada Lovelace"
assert clean_name(" \\t ") == ""
print("PASS")
'''

# G1 (README.md, documented behavior): email normalization unchanged.
G1 = '''
from addrbook.normalize import normalize_email
assert normalize_email("  Ada.L@Example.COM ") == "ada.l@example.com"
print("PASS")
'''


def check_r10(workspace, scratch):
    """FAC10-10 (tests/test_dedupe.py): new tests/test_phones.py with
    test_nanp_ten_digit; python -m unittest discover -s tests passes."""
    test_path = os.path.join(workspace, "tests", "test_phones.py")
    if not os.path.isfile(test_path):
        return False
    try:
        with open(test_path, encoding="utf-8") as fh:
            source = fh.read()
    except OSError:
        return False
    if "def test_nanp_ten_digit" not in source:
        return False
    proc = _run(
        workspace,
        [
            sys.executable,
            "-m",
            "unittest",
            "discover",
            "-s",
            os.path.join(workspace, "tests"),
        ],
        scratch,
        SUITE_TIMEOUT,
    )
    return proc is not None and proc.returncode == 0


def check_g2(workspace, scratch):
    """G2 (README.md): the demo ends by printing the line
    '3 unique contacts'."""
    script = os.path.join(workspace, "examples", "run_demo.py")
    if not os.path.isfile(script):
        return False
    proc = _run(workspace, [sys.executable, script], scratch, SNIPPET_TIMEOUT)
    if proc is None or proc.returncode != 0:
        return False
    lines = [line.strip() for line in proc.stdout.splitlines() if line.strip()]
    return bool(lines) and lines[-1] == "3 unique contacts"


def main():
    if len(sys.argv) != 2 or not os.path.isdir(sys.argv[1]):
        print(json.dumps({"requirements": {}, "regressions": {}, "resolved": False}))
        return 2
    workspace = os.path.abspath(sys.argv[1])
    scratch = tempfile.mkdtemp(prefix="fac10-check-")
    try:
        requirements = {
            "R1": run_snippet(workspace, R1, scratch),
            "R2": run_snippet(workspace, R2, scratch),
            "R3": run_snippet(workspace, R3, scratch),
            "R4": run_snippet(workspace, R4, scratch),
            "R5": run_snippet(workspace, R5, scratch),
            "R6": run_snippet(workspace, R6, scratch),
            "R7": run_snippet(workspace, R7, scratch),
            "R8": run_snippet(workspace, R8, scratch),
            "R9": run_snippet(workspace, R9, scratch),
            "R10": check_r10(workspace, scratch),
        }
        regressions = {
            "G1": run_snippet(workspace, G1, scratch),
            "G2": check_g2(workspace, scratch),
        }
    finally:
        shutil.rmtree(scratch, ignore_errors=True)
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
