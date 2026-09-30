"""One bounded Linux launcher for partial and final candidate observations.

Bubblewrap is a required external boundary for unreviewed bytes. Its absence or
failed preflight never enables local fallback. Known reviewed fixture bytes may
run locally and are labeled accordingly. Static source checks are not a sandbox.
"""
from __future__ import annotations

import ast
from dataclasses import dataclass
from functools import lru_cache
import hashlib
import json
import math
import os
from pathlib import Path
import signal
import subprocess
import sys
import tempfile
import time
from typing import Any


class ContainmentUnavailable(RuntimeError):
    pass


@dataclass(frozen=True)
class ObservationProcess:
    returncode: int
    stdout: str
    stderr: str
    mode: str
    timed_out: bool = False
    output_exceeded: bool = False


MAX_OUTPUT_BYTES = 8 * 1024 * 1024
MEMORY_BYTES = 256 * 1024 * 1024
CPU_SECONDS = 15
MAX_PROCESSES = 32
FIXTURE_HASHES = {
    "golden.py": "ec8f6d5d1b0613b44803135a59b5dd2a1b163ce22225dda564cae79da50b01dc",
    "frame_copy_error.py": "5fcd4e2d0e3d81593accc155ae911620b42a42e243415324e0dbd300ffa77c8e",
    "loose_tick_guard.py": "91a5d545bef5647e486a65fc95ece34eab8f2bc23f240c47298118f7eda77674",
    "mutating_tick.py": "22641556e5280ce7e76d4e8dcf2811bb23631c33ac0397ba94c67de01c9f5051",
    "tight_a_red_guard.py": "00db1ba417abad45db580c22a943fdec7ea6ed6afa764d789f83f985dd22cbf9",
    "wrong_initial.py": "a7c0088371f22b68f70f35a2c87e32e16abf9dee269424336a276c20124ada7d",
}


def _digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


@lru_cache(maxsize=1)
def _reviewed_hashes() -> frozenset[str]:
    """Only exact pinned fixtures and fixed host assemblies of their fragments."""
    from .oracle import ACTION_SYMBOLS, CONSTANTS, INITIAL

    root = Path(__file__).resolve().parents[2] / "tests/fixtures/candidates"
    hashes = set(FIXTURE_HASHES.values())
    constants = "\n".join(f"{name} = {value!r}" for name, value in CONSTANTS.items()) + "\n"
    for name in ("golden.py", "frame_copy_error.py"):
        data = (root / name).read_bytes()
        if _digest(data) != FIXTURE_HASHES[name]:
            raise ContainmentUnavailable(f"reviewed fixture has changed: {name}")
        source = data.decode("utf-8")
        functions = {node.name: ast.get_source_segment(source, node)
                     for node in ast.parse(source).body if isinstance(node, ast.FunctionDef)}
        fragments = ["INITIAL = " + repr(INITIAL)]
        for symbol in ACTION_SYMBOLS.values():
            partial = constants + "\n" + "\n\n".join(fragments) + "\n"
            hashes.add(_digest(partial.encode()))
            fragments.append(functions[symbol])
        partial = constants + "\n" + "\n\n".join(fragments) + "\n"
        hashes.add(_digest(partial.encode()))
        actions = "\n".join(["ACTIONS = {", *[f"    {label!r}: {symbol}," for label, symbol in ACTION_SYMBOLS.items()], "}"])
        hashes.add(_digest((partial.rstrip() + "\n\n" + actions + "\n").encode()))
    return frozenset(hashes)


def is_reviewed_source(source: str) -> bool:
    return _digest(source.encode("utf-8")) in _reviewed_hashes()


def _linux_command(scratch: Path, runner_path: Path, timeout_seconds: float) -> list[str]:
    """Minimal system-Python runtime mounts; never bind /, /home or the repo."""
    if not sys.platform.startswith("linux"):
        raise ContainmentUnavailable("guarded execution currently requires a compatible Linux host")
    python = Path("/usr/bin/python3").resolve()
    if not python.is_file() or not Path("/usr/bin/bwrap").is_file() or not Path("/usr/bin/prlimit").is_file():
        raise ContainmentUnavailable("system Python, bubblewrap and prlimit are required")
    try:
        probe = subprocess.run(
            [str(python), "-I", "-S", "-c", "import json,sysconfig; print(json.dumps([sysconfig.get_path('stdlib'),sysconfig.get_config_var('MULTIARCH')]))"],
            capture_output=True, text=True, check=True, timeout=5, env={},
        )
        stdlib, multiarch = json.loads(probe.stdout)
    except (OSError, ValueError, subprocess.SubprocessError) as exc:
        raise ContainmentUnavailable(f"unable to resolve system Python runtime: {exc}") from exc
    stdlib_path = Path(stdlib).resolve()
    library_path = Path("/usr/lib") / str(multiarch)
    if (stdlib_path.parent != Path("/usr/lib") or not stdlib_path.name.startswith("python3.")
            or not library_path.is_dir() or library_path.resolve().parent != Path("/usr/lib")):
        raise ContainmentUnavailable("unsupported system Python runtime layout")
    command = [
        "/usr/bin/prlimit", f"--as={MEMORY_BYTES}:{MEMORY_BYTES}",
        f"--cpu={CPU_SECONDS}:{CPU_SECONDS}", f"--fsize={MAX_OUTPUT_BYTES}:{MAX_OUTPUT_BYTES}",
        f"--nproc={MAX_PROCESSES}:{MAX_PROCESSES}", "--nofile=64:64", "--core=0:0", "--",
        "/usr/bin/bwrap", "--unshare-all", "--unshare-user", "--die-with-parent", "--new-session",
        "--cap-drop", "ALL", "--clearenv", "--setenv", "LC_ALL", "C.UTF-8", "--disable-userns",
        "--ro-bind", str(python), str(python),
        "--ro-bind", str(stdlib_path), str(stdlib_path),
        "--ro-bind", str(library_path), str(library_path),
        "--symlink", "usr/lib", "/lib",
    ]
    if Path("/usr/lib64").is_dir():
        command += ["--ro-bind", "/usr/lib64", "/usr/lib64", "--symlink", "usr/lib64", "/lib64"]
    # Do not expose installed application packages or potential private graders.
    empty = scratch / "empty-packages"
    empty.mkdir(exist_ok=True)
    for name in ("site-packages", "dist-packages"):
        command += ["--ro-bind", str(empty), str(stdlib_path / name)]
    command += [
        "--proc", "/proc", "--dev", "/dev", "--size", str(16 * 1024 * 1024), "--tmpfs", "/tmp",
        "--ro-bind", str(scratch), "/work", "--chdir", "/work",
        "--remount-ro", "/", "--remount-ro", "/dev", "--remount-ro", "/proc",
        "--", str(python), "-I", "-S", str(Path("/work") / runner_path.name),
        "/work/candidate.py",
    ]
    return command


def _collect(command: list[str], scratch: Path, request: str, timeout_seconds: float, mode: str) -> ObservationProcess:
    """File-backed bounded output, plus wall-clock/process-group cleanup."""
    if not math.isfinite(timeout_seconds) or timeout_seconds <= 0:
        raise ValueError("timeout must be finite and positive")
    # Output files live outside the mounted scratch and are write-only in child.
    with tempfile.TemporaryDirectory(prefix="tla-steer-output-") as output_dir:
        out_path, err_path = Path(output_dir) / "stdout", Path(output_dir) / "stderr"
        with out_path.open("wb") as stdout, err_path.open("wb") as stderr, tempfile.TemporaryFile() as stdin:
            stdin.write(request.encode("utf-8"))
            stdin.seek(0)
            process = subprocess.Popen(command, cwd=scratch, stdin=stdin, stdout=stdout, stderr=stderr,
                                       env={}, start_new_session=True, close_fds=True)
            deadline = time.monotonic() + timeout_seconds
            timed_out = output_exceeded = False
            try:
                while process.poll() is None:
                    output_exceeded = out_path.stat().st_size >= MAX_OUTPUT_BYTES or err_path.stat().st_size >= MAX_OUTPUT_BYTES
                    timed_out = time.monotonic() >= deadline
                    if output_exceeded or timed_out:
                        break
                    time.sleep(.01)
            finally:
                # Kill the entire process group even when the leader exited,
                # so a descendant cannot retain output pipes or keep running.
                try:
                    os.killpg(process.pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass
                process.wait()
        output_exceeded = output_exceeded or out_path.stat().st_size >= MAX_OUTPUT_BYTES or err_path.stat().st_size >= MAX_OUTPUT_BYTES
        with out_path.open("rb") as stdout, err_path.open("rb") as stderr:
            output = stdout.read(MAX_OUTPUT_BYTES).decode("utf-8", "replace")
            error = stderr.read(MAX_OUTPUT_BYTES).decode("utf-8", "replace")
        return ObservationProcess(process.returncode, output, error, mode, timed_out, output_exceeded)


def run_observations(source: str, runner: str, request: dict[str, Any], *, timeout_seconds: float) -> ObservationProcess:
    """Execute only observation code; private expected answers stay in parent."""
    reviewed = is_reviewed_source(source)
    if not reviewed:
        preflight()
    mode = "reviewed_fixture_local" if reviewed else "bubblewrap_linux"
    with tempfile.TemporaryDirectory(prefix="tla-steer-observations-") as temporary:
        scratch = Path(temporary)
        (scratch / "candidate.py").write_text(source, encoding="utf-8")
        runner_path = scratch / "runner.py"
        runner_path.write_text(runner, encoding="utf-8")
        if reviewed:
            command = ["/usr/bin/prlimit", f"--as={MEMORY_BYTES}:{MEMORY_BYTES}",
                       f"--cpu={CPU_SECONDS}:{CPU_SECONDS}", f"--fsize={MAX_OUTPUT_BYTES}:{MAX_OUTPUT_BYTES}",
                       "--core=0:0", "--", sys.executable, "-I", "-S", str(runner_path), str(scratch / "candidate.py")]
        else:
            command = _linux_command(scratch, runner_path, timeout_seconds)
        try:
            result = _collect(command, scratch, json.dumps(request, separators=(",", ":")), timeout_seconds, mode)
            if not reviewed and result.returncode != 0 and result.stderr.startswith(("bwrap:", "/usr/bin/prlimit:", "prlimit:")):
                raise ContainmentUnavailable("isolation launch failed after preflight: " + result.stderr[:500])
            return result
        except OSError as exc:
            raise ContainmentUnavailable(f"unable to launch {mode}: {exc}") from exc


def preflight() -> dict[str, Any]:
    """A real isolated launch is mandatory before provider calls; no fallback."""
    runner = "import json, os, sys\nassert set(os.environ) == {'LC_ALL'} and os.environ['LC_ALL'] == 'C.UTF-8'\nassert not os.path.exists('/home/agent')\nassert not os.path.exists('/workspace')\nprint(json.dumps({'isolated_launch': True}))\n"
    with tempfile.TemporaryDirectory(prefix="tla-steer-preflight-") as temporary:
        scratch = Path(temporary)
        path = scratch / "runner.py"
        path.write_text(runner)
        command = _linux_command(scratch, path, 5)
        try:
            result = _collect(command, scratch, "{}", 5, "bubblewrap_linux")
        except OSError as exc:
            raise ContainmentUnavailable(f"isolation preflight launch failed: {exc}") from exc
    if result.returncode != 0 or result.timed_out or result.output_exceeded or result.stdout.strip() != '{"isolated_launch": true}':
        raise ContainmentUnavailable("isolation preflight failed; provider calls blocked: " + result.stderr.strip()[:500])
    return {"mode": "bubblewrap_linux", "preflight_passed": True, "hostile_code_validation": "requires host-specific adversarial checks"}
