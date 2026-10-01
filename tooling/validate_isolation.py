"""Credential-free, host-specific Linux boundary smoke test; no provider calls.

All adversarial runners below are reviewed local probes, not generated code.
They bypass the Python conformance filter to test the OS boundary itself.
Passing is evidence for this recorded host, not a general sandbox guarantee.
No security settings are changed, and failed preflight has no local fallback.
"""
from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
import json
import os
from pathlib import Path
import platform
import resource
import socket
import subprocess
import tempfile
import time
import uuid

from tla_steer import execution, pipeline, verifier
from tla_steer.contract import Proposal, PROPOSAL_SCHEMA_VERSION, controller_from_json
from tla_steer.smc import Particle
from tla_steer.worker import ReviewedFixtureWorker

ROOT = Path(__file__).resolve().parents[1]
SOURCE = (ROOT / "tests/fixtures/candidates/golden.py").read_text() + "\n# real isolation validation only\n"


def require(condition, message):
    if not condition:
        raise AssertionError(message)


def emit(name, status, **details):
    print(json.dumps({"probe": name, "status": status, **details}, sort_keys=True), flush=True)


def observe(runner, request=None, timeout=5):
    require(not execution.is_reviewed_source(SOURCE), "probe must bypass the fixture exception")
    result = execution.run_observations(SOURCE, runner, request or {}, timeout_seconds=timeout)
    require(result.mode == "bubblewrap_linux", "probe used local fixture mode")
    return result


def successful_json(result):
    require(result.returncode == 0 and not result.timed_out and not result.output_exceeded,
            f"probe process failed: {result.returncode}: {result.stderr[:500]}")
    return json.loads(result.stdout)


def golden_checkers():
    # Use both production grading entry points. A harmless source comment forces
    # the real boundary without mocking the launcher or changing pinned fixtures.
    fixture = ReviewedFixtureWorker(ROOT)
    controller = controller_from_json(json.dumps(fixture.controller))
    initial, step = controller.steps[:2]
    fragments = (
        Proposal(PROPOSAL_SCHEMA_VERSION, initial.id, fixture.initial),
        Proposal(PROPOSAL_SCHEMA_VERSION, step.id, fixture.fragments["golden.py"]["tick"] + "\n# real isolation"),
    )
    particle = Particle("isolation-probe", None, (), 1, fragments, 0, (), "alive")
    require(not execution.is_reviewed_source(pipeline._partial_source(particle)), "partial used fixture bytes")
    require(pipeline._score_action(particle, step).value == 1, "partial golden score failed")
    with tempfile.TemporaryDirectory(prefix="tla-golden-") as temporary:
        path = Path(temporary) / "candidate.py"
        path.write_text(SOURCE)
        result = verifier.verify_candidate(path)
    require(result["containment_mode"] == "bubblewrap_linux", "final used fixture mode")
    require(result["outcome"] == "EXACT", "final golden grading failed")


def private_data_and_network():
    with tempfile.TemporaryDirectory(prefix="tla-private-canary-") as temporary:
        canary = Path(temporary) / "fake-private-answer"
        token = "synthetic-canary-" + uuid.uuid4().hex
        canary.write_text(token)
        require(canary.read_text() == token, "filesystem positive control failed")
        oracle_path = ROOT / "src/tla_steer/oracle.py"
        require(oracle_path.is_file(), "private grader positive control failed")
        with canary.open() as descriptor, socket.socket() as listener:
            os.set_inheritable(descriptor.fileno(), True)
            require(os.read(descriptor.fileno(), len(token)) == token.encode(), "FD positive control failed")
            listener.bind(("127.0.0.1", 0))
            listener.listen(2)
            with socket.create_connection(listener.getsockname(), timeout=1):
                accepted, _ = listener.accept()
                accepted.close()
            prior = os.environ.get("TLA_SYNTHETIC_PRIVATE_CANARY")
            os.environ["TLA_SYNTHETIC_PRIVATE_CANARY"] = token
            try:
                request = {"paths": [str(canary), str(oracle_path), str(ROOT), str(Path.home())],
                           "fd": descriptor.fileno(), "port": listener.getsockname()[1],
                           "parent_pid": os.getpid(), "netns": os.readlink("/proc/self/ns/net")}
                result = successful_json(observe(r'''
import json, os, socket
request = json.load(__import__('sys').stdin)
assert set(os.environ) == {'LC_ALL'}
for path in request['paths']:
    assert not os.path.exists(path), path
assert not os.path.exists('/proc/' + str(request['parent_pid']))
try:
    os.fstat(request['fd'])
except OSError:
    pass
else:
    raise AssertionError('inherited private descriptor')
assert os.readlink('/proc/self/ns/net') != request['netns']
try:
    connection = socket.create_connection(('127.0.0.1', request['port']), timeout=.5)
except OSError:
    pass
else:
    connection.close()
    raise AssertionError('host listener reachable')
print(json.dumps({'filesystem_environment_fds_pid_private_grader': True, 'network': True}))
''', request))
            finally:
                if prior is None:
                    del os.environ["TLA_SYNTHETIC_PRIVATE_CANARY"]
                else:
                    os.environ["TLA_SYNTHETIC_PRIVATE_CANARY"] = prior
            require(all(result.values()) and len(result) == 2, "boundary response incomplete")


def resource_limits():
    result = successful_json(observe(r'''
import errno, json, os, resource, signal
expected = {resource.RLIMIT_AS: 256*1024*1024, resource.RLIMIT_CPU: 15,
            resource.RLIMIT_FSIZE: 8*1024*1024, resource.RLIMIT_NPROC: 32,
            resource.RLIMIT_NOFILE: 64, resource.RLIMIT_CORE: 0}
assert all(resource.getrlimit(key) == (value, value) for key, value in expected.items())
for path in ('/boundary-write', '/work/boundary-write', '/usr/lib/boundary-write'):
    try:
        open(path, 'wb').close()
    except OSError as exc:
        assert exc.errno in (errno.EROFS, errno.EACCES, errno.EPERM)
    else:
        raise AssertionError('read-only mount writable: ' + path)
with open('/tmp/positive-control', 'wb') as handle:
    assert handle.write(b'local') == 5
total = 0
try:
    for index in range(3):
        with open('/tmp/bounded-' + str(index), 'wb', buffering=0) as handle:
            for block in range(7):
                total += handle.write(b'x' * 1024 * 1024)
except OSError as exc:
    assert exc.errno == errno.ENOSPC
else:
    raise AssertionError('tmpfs exceeded 16 MiB')
assert total <= 16*1024*1024
try:
    allocation = bytearray(512*1024*1024)
except MemoryError:
    pass
else:
    raise AssertionError('address-space allocation exceeded limit')
handles = []
try:
    for index in range(80):
        handles.append(open('/dev/null', 'rb'))
except OSError as exc:
    assert exc.errno == errno.EMFILE
else:
    raise AssertionError('descriptor limit missing')
finally:
    for handle in handles:
        handle.close()
children = []
limited = False
try:
    for index in range(40):
        child = os.fork()
        if child == 0:
            signal.pause()
            os._exit(0)
        children.append(child)
except OSError as exc:
    assert exc.errno == errno.EAGAIN
    limited = True
finally:
    for child in children:
        os.kill(child, signal.SIGKILL)
        os.waitpid(child, 0)
assert limited and 0 < len(children) < 32, 'namespace process limit not enforced'
print(json.dumps({'mounts_tmpfs_memory_descriptors_processes_limits': True}))
'''))
    require(result == {"mounts_tmpfs_memory_descriptors_processes_limits": True}, "resource response incomplete")
    flood = observe("import os\nwhile True: os.write(1, b'x'*65536)", timeout=3)
    require(flood.output_exceeded and len(flood.stdout.encode()) == execution.MAX_OUTPUT_BYTES,
            "output was not bounded during collection")
    spin = observe("while True: pass", timeout=.3)
    require(spin.timed_out, "wall-clock deadline not enforced")


def named_processes(marker):
    result = set()
    for path in Path("/proc").glob("[0-9]*/comm"):
        try:
            if path.read_text().strip() == marker:
                result.add(int(path.parent.name))
        except (FileNotFoundError, ProcessLookupError, PermissionError):
            pass
    return result


def descendant_cleanup():
    marker = "tla-" + uuid.uuid4().hex[:10]
    runner = f'''import ctypes, os, time
child = os.fork()
if child == 0:
    ctypes.CDLL(None).prctl(15, {marker.encode()!r}, 0, 0, 0)
time.sleep(8)
'''
    require(not named_processes(marker), "cleanup marker was not unique")
    with ThreadPoolExecutor(max_workers=1) as pool:
        future = pool.submit(observe, runner, timeout=3)
        deadline = time.monotonic() + 2
        observed = set()
        while not observed and time.monotonic() < deadline and not future.done():
            observed = named_processes(marker)
            time.sleep(.02)
        result = future.result()
    require(observed, "descendant positive control failed; cleanup was not tested")
    require(result.timed_out, "descendant probe did not reach timeout")
    deadline = time.monotonic() + 1
    while named_processes(marker) and time.monotonic() < deadline:
        time.sleep(.02)
    require(not named_processes(marker), "descendant survived launcher cleanup")


def main():
    commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    require(not os.environ.get("GITHUB_SHA") or commit == os.environ["GITHUB_SHA"], "wrong checked-out commit")
    packages = subprocess.run(["dpkg-query", "-W", "bubblewrap", "python3", "util-linux"],
                              capture_output=True, text=True, timeout=5)
    versions = packages.stdout.strip() if packages.returncode == 0 else "package records unavailable"
    restriction = Path("/proc/sys/kernel/apparmor_restrict_unprivileged_userns")
    emit("host", "recorded", commit=commit, kernel=platform.release(), python=platform.python_version(),
         image=os.environ.get("ImageOS"), image_version=os.environ.get("ImageVersion"), packages=versions,
         apparmor_restrict_unprivileged_userns=restriction.read_text().strip() if restriction.exists() else "absent")
    # Read-only diagnostics: RLIMIT_NPROC counts all host threads for this UID,
    # including the CI worker, before bubblewrap can create its namespaces.
    uid_threads = uid_processes = 0
    for status in Path('/proc').glob('[0-9]*/status'):
        try:
            fields = dict(line.split(':', 1) for line in status.read_text().splitlines() if ':' in line)
            if int(fields['Uid'].split()[0]) == os.getuid():
                uid_processes += 1
                uid_threads += int(fields['Threads'])
        except (OSError, KeyError, ValueError):
            continue
    def read_value(path):
        try:
            return Path(path).read_text().strip()
        except OSError:
            return 'unavailable'
    cgroup = {}
    for row in read_value('/proc/self/cgroup').splitlines():
        if row.startswith('0::'):
            root = Path('/sys/fs/cgroup')
            current = (root / row[3:].lstrip('/')).resolve()
            while current == root or root in current.parents:
                cgroup[str(current)] = {name: read_value(current / name)
                                        for name in ('pids.current', 'pids.max', 'pids.events')}
                if current == root:
                    break
                current = current.parent
    emit('launch_limits', 'recorded', uid=os.getuid(), uid_processes=uid_processes,
         uid_threads=uid_threads, parent_nproc=resource.getrlimit(resource.RLIMIT_NPROC),
         launcher_nproc=execution.MAX_PROCESSES, cgroup=cgroup,
         kernel_limits={name: read_value('/proc/sys/' + name) for name in
                        ('kernel/threads-max', 'kernel/pid_max', 'user/max_user_namespaces', 'user/max_pid_namespaces')},
         apparmor_profile=read_value('/proc/self/attr/current'))
    checks = [("real_preflight", execution.preflight), ("golden_partial_and_final", golden_checkers),
              ("private_data_and_network", private_data_and_network), ("resource_limits", resource_limits),
              ("descendant_cleanup", descendant_cleanup)]
    for index, (name, check) in enumerate(checks):
        try:
            check()
        except Exception as exc:
            emit(name, "failed", error=f"{type(exc).__name__}: {exc}")
            for remaining, _ in checks[index+1:]:
                emit(remaining, "not_run")
            return 1
        emit(name, "passed")
    emit("summary", "passed", scope="recorded host only; controlled smoke probes; no live-model claim")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
