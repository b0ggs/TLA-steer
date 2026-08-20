#!/usr/bin/env python3
"""Checker for the slidewin bug-fix task.

Usage: python3 check.py /path/to/workspace

Runs one subprocess per requirement, never writes into the workspace
(PYTHONDONTWRITEBYTECODE=1, cwd is a private temp dir), and prints canonical
JSON: {"requirements": {...}, "regressions": {...}, "resolved": bool}.

Every value asserted below is stated verbatim in the workspace's public
documentation (.issue-contract.md, README.md, docs/design.md, CHANGELOG.md,
or a tests/ comment).
"""

import json
import os
import subprocess
import sys
import tempfile

PRELUDE = (
    "import sys\n"
    "ws = sys.argv[1]\n"
    "sys.path.insert(0, ws)\n"
)

PROBES = {
    # R1 (primary): issue #41 / docs/design.md "Window semantics" — an event
    # exactly window seconds old is expired; strictly younger events count.
    "R1": """
from slidewin.clock import ManualClock
from slidewin.window import SlidingWindowCounter

clk = ManualClock()
c = SlidingWindowCounter(10, clock=clk)
c.record()            # event at t=0
clk.advance(9.5)
assert c.count() == 1, "event strictly inside the window must count"

clk2 = ManualClock()
c2 = SlidingWindowCounter(10, clock=clk2)
c2.record()           # event at t=0
clk2.advance(10)      # exactly window seconds old
assert c2.count() == 0, "event exactly window seconds old must be expired"
""",
    # R2: CHANGELOG.md prose — record the fix under a "## 0.2.1" heading.
    "R2": """
import io, os
path = os.path.join(ws, "CHANGELOG.md")
with io.open(path, "r", encoding="utf-8") as fh:
    lines = fh.read().splitlines()
assert any(line.strip().startswith("## 0.2.1") for line in lines), \\
    "CHANGELOG.md must contain a '## 0.2.1' heading"
""",
    # R3: README.md "Releases" — __version__ reads "0.2.1" once the fix lands.
    "R3": """
import slidewin
assert slidewin.__version__ == "0.2.1", repr(slidewin.__version__)
""",
    # R4: docs/design.md — count docstring includes, word for word:
    # "Events exactly window seconds old are expired."
    "R4": """
from slidewin.window import SlidingWindowCounter
doc = SlidingWindowCounter.count.__doc__ or ""
assert "Events exactly window seconds old are expired." in doc, repr(doc)
""",
    # R5: README.md "Configuration" — LimiterConfig() with no arguments
    # reports window_seconds of 60 and default_limit of 5.
    "R5": """
from slidewin.config import LimiterConfig
cfg = LimiterConfig()
assert cfg.window_seconds == 60, repr(cfg.window_seconds)
assert cfg.default_limit == 5, repr(cfg.default_limit)
""",
    # R6: docs/design.md "Error wording" — limit 5, 60s window raises with the
    # exact message "limit of 5 per 60s exceeded".
    "R6": """
from slidewin.clock import ManualClock
from slidewin.config import LimiterConfig
from slidewin.errors import RateLimitExceeded
from slidewin.limiter import RateLimiter

clk = ManualClock()
cfg = LimiterConfig(window_seconds=60, default_limit=5)
lim = RateLimiter(limit=5, config=cfg, clock=clk)
for _ in range(5):
    lim.acquire("k")
try:
    lim.acquire("k")
except RateLimitExceeded as exc:
    assert str(exc) == "limit of 5 per 60s exceeded", repr(str(exc))
else:
    raise AssertionError("expected RateLimitExceeded on the sixth acquire")
""",
    # R7: docs/design.md "Clocks" — negative advance raises ValueError with
    # message "cannot advance clock backwards" and leaves the clock unchanged.
    "R7": """
from slidewin.clock import ManualClock
clk = ManualClock()
try:
    clk.advance(-1)
except ValueError as exc:
    assert str(exc) == "cannot advance clock backwards", repr(str(exc))
else:
    raise AssertionError("negative advance must raise ValueError")
assert clk.now() == 0.0, "clock reading must be left unchanged"
""",
    # R8: README.md "Enforcement and shadow mode" — remaining() is clamped at
    # zero; once hits meet or exceed the limit it returns 0.
    "R8": """
from slidewin.clock import ManualClock
from slidewin.config import LimiterConfig
from slidewin.limiter import RateLimiter

clk = ManualClock()
cfg = LimiterConfig(window_seconds=60, default_limit=2)
lim = RateLimiter(config=cfg, clock=clk)
for _ in range(4):
    lim.hit("k")
out = lim.remaining("k")
assert out == 0, repr(out)
""",
    # R9: tests/test_window.py comment — add a passing regression test named
    # test_boundary_event_expired.
    "R9": """
import importlib.util, os, unittest

path = os.path.join(ws, "tests", "test_window.py")
spec = importlib.util.spec_from_file_location("test_window_probe", path)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
suite = unittest.TestLoader().loadTestsFromModule(mod)
names = []
def collect(s):
    for t in s:
        if isinstance(t, unittest.TestSuite):
            collect(t)
        else:
            names.append(t._testMethodName)
collect(suite)
assert "test_boundary_event_expired" in names, names
stream = open(os.devnull, "w")
result = unittest.TextTestRunner(stream=stream, verbosity=0).run(suite)
stream.close()
assert result.wasSuccessful(), "tests in tests/test_window.py must pass"
""",
    # R10: README.md "Enforcement and shadow mode" — a successful acquire
    # returns remaining slots: with limit 5, first returns 4, second returns 3.
    "R10": """
from slidewin.clock import ManualClock
from slidewin.config import LimiterConfig
from slidewin.limiter import RateLimiter

clk = ManualClock()
cfg = LimiterConfig(window_seconds=60, default_limit=5)
lim = RateLimiter(config=cfg, clock=clk)
first = lim.acquire("k")
assert first == 4, repr(first)
second = lim.acquire("k")
assert second == 3, repr(second)
""",
    # G1 (regression): README quick-start behaviour — events strictly inside
    # the window are all counted.
    "G1": """
from slidewin.clock import ManualClock
from slidewin.window import SlidingWindowCounter

clk = ManualClock()
c = SlidingWindowCounter(10, clock=clk)
for _ in range(3):
    clk.advance(1)
    c.record()
clk.advance(2)
assert c.count() == 3, repr(c.count())
""",
    # G2 (regression): acquire under the limit does not raise, and
    # RateLimitExceeded stays an Exception subclass.
    "G2": """
from slidewin.clock import ManualClock
from slidewin.config import LimiterConfig
from slidewin.errors import RateLimitExceeded
from slidewin.limiter import RateLimiter

assert issubclass(RateLimitExceeded, Exception)
clk = ManualClock()
cfg = LimiterConfig(window_seconds=60, default_limit=5)
lim = RateLimiter(config=cfg, clock=clk)
lim.acquire("g")
lim.acquire("g")  # still under the limit: must not raise
""",
}


def run_probe(source, workspace, tmpdir):
    env = dict(os.environ)
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    env.pop("PYTHONPATH", None)
    try:
        proc = subprocess.run(
            [sys.executable, "-c", PRELUDE + source, workspace],
            cwd=tmpdir,
            env=env,
            capture_output=True,
            text=True,
            timeout=120,
        )
    except subprocess.TimeoutExpired:
        return False
    return proc.returncode == 0


def main():
    if len(sys.argv) != 2:
        print("usage: check.py <workspace>", file=sys.stderr)
        return 2
    workspace = os.path.abspath(sys.argv[1])
    results = {"requirements": {}, "regressions": {}}
    with tempfile.TemporaryDirectory() as tmpdir:
        for key in ["R1", "R2", "R3", "R4", "R5", "R6", "R7", "R8", "R9",
                    "R10", "G1", "G2"]:
            ok = run_probe(PROBES[key], workspace, tmpdir)
            bucket = "requirements" if key.startswith("R") else "regressions"
            results[bucket][key] = ok
    results["resolved"] = (
        all(results["requirements"].values())
        and all(results["regressions"].values())
    )
    print(json.dumps(results))
    return 0


if __name__ == "__main__":
    sys.exit(main())
